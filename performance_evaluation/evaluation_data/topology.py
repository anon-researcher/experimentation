import random
import math
import json
import os
from enum import Enum

# parameters for creation of tree structures, how many successors has a single node
branch_mean = 1.5  # broad 2.5, deep 1.5
branch_std = 0.5   # broad 1.5, deep 0.5

# parameters for creation of graph structures, how many connecting edges between subtrees:
edge_mean = 2
edge_std = 0.5  # broad 1.0, deep 0.5

# how 'deep' is the original tree-like structure
depths = [i for i in range(2, 26)]   # deep from 2 to 25, broad from 2 to 12 (all inclusive)

# used for unique node labeling
node_counter = 0

# change type distribution in percent. Remaining percentage => unchanged
# change_types = {'removed': 2, 'added': 2, 'updated': 2}                           # 2  2  2
# change_types = {'removed': 5, 'added': 5, 'updated': 10}                          # 5  5  10
# change_types = {'removed': 10, 'added': 15, 'updated': 15} ]                      # 10 15 15
change_types = {'removed': 20, 'added': 20, 'updated': 25}                          # 20 20 25

# probability for performance deviations on a single node (in percent):
deviation_probabilities = [0, 5, 10, 20, 30]

# range for introduced performance deviation in Milliseconds
min_deviation = 30
max_deviation = 200


def run():

    change_types['unchanged'] = sum(value for value in change_types.values())

    for depth in depths:
        # output folder
        out_dir = f"out_{depth}_r{change_types['removed']}_a{change_types['added']}_u{change_types['updated']}"
        construct_graph(depth, out_dir)


def construct_graph(depth, out_dir):
    # set up 'root' node of the interaction graph and target service of the experiment
    all_nodes = set()
    root = Node("edge", version=1, level=0)
    target = Node("target", version=1, level=1)
    target.node_type = NodeType.UPDATED
    root.outgoing.add(target)
    target.incoming.add(root)
    all_nodes.add(root)
    all_nodes.add(target)

    while True:
        target.outgoing = set()

        node_set = set()
        level_dict = {}

        # creates a basic tree structure, every node has random.gauss(branch_mean, branch_std) successors
        create_child_nodes(target, depth, node_set, level_dict, max_depth=depth)

        # we require that we have at least branch^depth nodes in our tree/graph
        if len(node_set) >= branch_mean**depth:
            break

    add_connections(target, level_dict)
    for node in node_set:
        add_connections(node, level_dict)

    # traverse(root)

    total_elements = len(node_set)
    # print(f"total:{total_elements}")

    removed = tag_nodes(node_set, NodeType.REMOVED, math.floor(total_elements * change_types['removed']/100))
    all_removed = propagate_update(removed, NodeType.REMOVED, {})

    # print("------\ntotal removed:" + str(len(removed)))
    # for item in removed:
    #     print(item)
    #
    # print("---------\nadded after propagation:" + str(len(all_removed)))
    # for item in all_removed.difference(removed):
    #     print(item)

    # if a 'removed' node has a successor, we cannot tag this successor as newly 'added':
    # same applies for predecessor
    blocked_candidates = all_removed.copy()
    updated_set = {target}
    for item in all_removed:
        blocked_candidates = blocked_candidates.union(item.outgoing)
        blocked_candidates = blocked_candidates.union(item.incoming)

        for node in item.incoming:
            if node.node_type != NodeType.REMOVED and node.node_type != NodeType.UPDATED:
                node.node_type = NodeType.UPDATED
                updated_set.add(node)

    # print("---------\nblocked candidates for add:" + str(len(blocked_candidates)))
    # for item in blocked_candidates:
    #     print(item)

    remaining = node_set - blocked_candidates
    added = tag_nodes(remaining, NodeType.ADDED, math.floor(total_elements * change_types['added']/100))
    all_added = propagate_update(added, NodeType.ADDED, blocked_candidates)

    for item in all_added:
        for node in item.incoming:
            if node.node_type == NodeType.UNCHANGED:
                node.node_type= NodeType.UPDATED
                updated_set.add(node)

    # print("------\ntotal added:" + str(len(added)))
    # for item in added:
    #     print(item)
    #
    # print("---------\nadded after propagation:" + str(len(all_added)))
    # for item in all_added.difference(added):
    #     print(item)
    #
    # print("==========================")

    update_candidates = node_set.difference(all_removed).difference(all_added).difference(updated_set)
    updated = tag_nodes(update_candidates, NodeType.UPDATED, max(0, math.floor(total_elements * change_types['updated']/100) - len(updated_set)))

    all_updated = updated.union(updated_set)
    all_nodes = node_set.union(all_nodes)

    # print("------\ntotal updated (before " + str(len(updated_set)) + "):" + str(len(all_updated)))
    # for item in all_updated:
    #     print(item)

    # remaining = remaining - added
    # updated = tag_nodes(remaining, NodeType.UPDATED, math.floor(total_elements * change_types['updated']/100))

    categorized = {
        'node': {
            NodeType.UNCHANGED: set(),
            NodeType.REMOVED: set(),
            NodeType.UPDATED: set(),
            NodeType.ADDED: set()
        },
        'changes': {
            'common': set(),
            'calling_new_ep': set(),
            'removing': set(),
            'calling_ex_ep': set(),
            'updated_caller': set(),
            'updated_version': set(),
            'updated_callee': set(),
            'uncaptured': set(),
        }
    }
    traverse(root, categorized, visited=set(), print_node=False)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    save_summary_file(f"{out_dir}/summary.json", categorized['node'])

    for probability in deviation_probabilities:
        if probability != 0:
            add_performance_issues(all_updated, probability)

        save_interaction_graph(f"{out_dir}/graph_{probability}.json", categorized['changes'])

        # print("------------------------")
        # print(f"Deviation probability {probability}%:")
        # traverse_generic(root, Node.print_with_deviation, visited=set())

        if probability != 0:
            reset_performance_issues(all_nodes)

    print("========================")
    num_nodes = sum(len(value) for value in categorized['node'].values())
    num_edges = sum(len(value) for key,value in categorized['changes'].items() if key != 'uncaptured')

    call_counter = []
    for n in all_nodes:
        call_counter.append(len(n.outgoing))

    stats = []
    stats.append(f"Depth: {depth}")
    stats.append(f"Total nodes: {num_nodes}")
    stats.append(f"Total edges: {num_edges}")
    stats.append(f"Density: {num_edges / (num_nodes * (num_nodes-1))}")
    stats.append(f"Max depth: {len(level_dict)}")
    stats.append(f"Average calls: {sum(call_counter)/len(call_counter)}")

    stats.append("\nNode details:")
    stats.append(f" |- unchanged: {len(categorized['node'][NodeType.UNCHANGED])}, "
                 f"removed: {len(categorized['node'][NodeType.REMOVED])}, "
                 f"added: {len(categorized['node'][NodeType.ADDED])}, "
                 f"updated: {len(categorized['node'][NodeType.UPDATED])}")
    stats.append(f" |- unchanged: {round(100*len(categorized['node'][NodeType.UNCHANGED])/num_nodes)}%, "
                 f"removed: {round(100*len(categorized['node'][NodeType.REMOVED])/num_nodes)}%, "
                 f"added: {round(100*len(categorized['node'][NodeType.ADDED])/num_nodes)}%, "
                 f"updated: {round(100*len(categorized['node'][NodeType.UPDATED])/num_nodes)}%")


    stats.append("\nChange details:")
    stats.append(f" |- common: {len(categorized['changes']['common'])}")
    stats.append(f" |- removing: {len(categorized['changes']['removing'])}")
    stats.append(f" |- calling_new_ep: {len(categorized['changes']['calling_new_ep'])}")
    stats.append(f" |- calling_ex_ep: {len(categorized['changes']['calling_ex_ep'])}")
    stats.append(f" |- updated_caller: {len(categorized['changes']['updated_caller'])}")
    stats.append(f" |- updated_callee: {len(categorized['changes']['updated_callee'])}")
    stats.append(f" |- updated_version: {len(categorized['changes']['updated_version'])}")
    stats.append(f" |- uncaptured: {len(categorized['changes']['uncaptured'])}")

    with open(f"{out_dir}/stats.txt", "w") as f:
        f.writelines('\n'.join(stats))

    print('\n'.join(stats))

    assert len(categorized['changes']['uncaptured']) == 0

    #
    # save_interaction_graph("interaction_graph.json", categorized['changes'])
    # save_summary_file("summary.json", categorized['node'])


def add_performance_issues(node_set, deviation_probability):
    for node in node_set:
        probability = random.randint(0, 100)
        if probability <= deviation_probability:
            node.deviation = random.randint(min_deviation, max_deviation) * 1000  # delay in microseconds
            for item in node.incoming:
                propagate_delay(item, node, node.deviation)


def reset_performance_issues(node_set):
    for node in node_set:
        node.deviation = 0
        node.cascaded_deviations = {}


def propagate_delay(node, origin, delay):
    if origin not in node.cascaded_deviations:
        node.cascaded_deviations[origin] = delay
        for item in node.incoming:
            propagate_delay(item, origin, delay)


def handle_standard_output(change_type, changes):
    output = []
    for source, target in changes:
        output.append(get_standard_entry(source, target, change_type))
    return output


def get_standard_entry(source, target, change_type):
    return {
        "source": source.get_json_entry(version_inc=(change_type == 'updated_caller' or change_type== 'updated_version')),
        "target": target.get_json_entry(version_inc=(change_type == 'updated_callee' or change_type== 'updated_version'))
    }


def handle_comparable_output(change_type, changes):
    output = []
    for source, target in changes:
        entry = get_standard_entry(source, target, change_type)
        if change_type == 'updated_caller' or change_type == 'updated_version':
            entry['oldSourceVersion'] = f"v{source.version}"
        if change_type == 'updated_callee' or change_type == 'updated_version':
            entry['oldTargetVersion'] = f"v{target.version}"
        entry['stats'] = {
            'critical': True if target.deviation > 0 or len(target.cascaded_deviations)>0 else False,
            'maxDeviation': target.deviation + sum(target.cascaded_deviations.values())
        }
        output.append(entry)
    return output


def save_interaction_graph(path, categorized):
    output = {}
    with open(path, "w") as file:
        standard = ['calling_new_ep', 'calling_ex_ep', 'removing']
        comparable = ['common', 'updated_caller', 'updated_callee', 'updated_version']

        for change_type in standard:
            output[change_type] = handle_standard_output(change_type, categorized[change_type])

        for change_type in comparable:
            output[change_type] = handle_comparable_output(change_type, categorized[change_type])

        file.write(json.dumps(output))


def save_summary_file(path, categorized):
    output = {}
    with open(path, "w") as file:
        output['diff_summary'] = {'added_services': [{'service': n.name} for n in categorized[NodeType.ADDED]],
                   'deleted_services': [{'service': n.name} for n in categorized[NodeType.REMOVED]],
                   'added_versions': [{'service': n.name, 'version': f"v{n.version}"} for n in
                                      categorized[NodeType.ADDED]] + \
                                     [{'service': n.name, 'version': f"v{n.version + 1}"} for n in
                                      categorized[NodeType.UPDATED]],
                   'deleted_versions': [{'service': n.name, 'version': f"v{n.version}"} for n in
                                        categorized[NodeType.REMOVED]] + \
                                       [{'service': n.name, 'version': f"v{n.version}"} for n in
                                        categorized[NodeType.UPDATED]],
                   'added_endpoints': [n.get_json_entry() for n in categorized[NodeType.ADDED]] +
                                      [n.get_json_entry(version_inc=True) for n in categorized[NodeType.UPDATED]],
                   'deleted_endpoints': [n.get_json_entry() for n in categorized[NodeType.REMOVED]] +
                                        [n.get_json_entry() for n in categorized[NodeType.UPDATED]]
                   }
        output['endpoints'] = [n.get_json_entry() for n in categorized[NodeType.ADDED]] +\
                              [n.get_json_entry(version_inc=True) for n in categorized[NodeType.UPDATED]] +\
                              [n.get_json_entry(version_inc=False) for n in categorized[NodeType.UPDATED]] +\
                              [n.get_json_entry() for n in categorized[NodeType.REMOVED]] +\
                              [n.get_json_entry() for n in categorized[NodeType.UNCHANGED]]

        file.write(json.dumps(output))


def add_connections(node, level_dict):
    # determine how many edges to add
    num_edges = round(min(6, max(0, random.gauss(edge_mean, edge_std))))

    if num_edges == 0:
        return

    candidates = set()
    for level,level_set in level_dict.items():
        if level > node.level:
            candidates = candidates.union(level_set)

    # remove those nodes where there already exists a connection to
    candidates = candidates - node.outgoing

    picked = random.sample(candidates, min(num_edges, len(candidates)))
    for item in picked:
        node.outgoing.add(item)
        item.incoming.add(node)


def tag_nodes(node_set, node_type, num_nodes):
    if num_nodes > len(node_set):
        return set()

    selection = set(random.sample(node_set, num_nodes))
    for node in selection:
        node.node_type = node_type

    return selection


def propagate_update(node_set, node_type, blocked_nodes):
    updated_set = node_set.copy()

    for node in node_set:
        for candidate in node.outgoing:
            if candidate not in blocked_nodes:
                traverse_update(node, candidate, updated_set, node_type, blocked_nodes)

    return updated_set


def traverse_update(node, candidate, updated_set, node_type, blocked_nodes):
    if candidate.node_type == node_type:
        return

    if len(candidate.incoming) == 1 and node in candidate.incoming and candidate not in blocked_nodes:
        candidate.node_type = node_type
        updated_set.add(candidate)

        for new_candidate in candidate.outgoing:
            if len(new_candidate.incoming) == 1:
                traverse_update(candidate, new_candidate, updated_set, node_type, blocked_nodes)


def create_child_nodes(node, depth, node_set, level_dict, max_depth):
    # stop creation when maximum depth is reached
    if depth == 0:
        return

    num_children = round(min(8, max(0, random.gauss(branch_mean, branch_std))))

    # no children, we are done
    if num_children == 0:
        return

    for idx in range(num_children):
        child = Node(get_unique_name(), level=max_depth - depth + 2)
        child.incoming.add(node)
        node.outgoing.add(child)
        node_set.add(child)
        add_to_level(level_dict, child)
        create_child_nodes(child, depth-1, node_set, level_dict, max_depth)


def add_to_level(level_dict, node):
    if not node or not hasattr(node, 'level'):
        return

    level = node.level
    if level not in level_dict:
        level_dict[level] = set()

    level_dict[level].add(node)


def traverse(node, stats, visited, print_node=False):
    if node in visited:
        return

    if print_node:
        print(node)

    update_node_stats(node, stats)
    visited.add(node)
    for child in node.outgoing:
        update_change_type_stats(node, child, stats)
        traverse(child, stats, visited, print_node)


def traverse_generic(node, func, visited):
    if node in visited:
        return

    print(func(node))

    visited.add(node)
    for child in node.outgoing:
        traverse_generic(child, func, visited)


def update_node_stats(node, stats):
    stats['node'][node.node_type].add(node)


def update_change_type_stats(node, child, stats):
    if node.node_type == NodeType.UNCHANGED and child.node_type == NodeType.UNCHANGED:
        stats['changes']['common'].add((node, child))
    elif (node.node_type == NodeType.UNCHANGED or node.node_type == NodeType.UPDATED or node.node_type == NodeType.ADDED) and child.node_type == NodeType.ADDED:
        stats['changes']['calling_new_ep'].add((node, child))
    elif (node.node_type == NodeType.UPDATED and child.node_type == NodeType.REMOVED) or node.node_type == NodeType.REMOVED:
        stats['changes']['removing'].add((node, child))
    elif node.node_type == NodeType.ADDED and (child.node_type == NodeType.UNCHANGED or child.node_type == NodeType.UPDATED):
        stats['changes']['calling_ex_ep'].add((node, child))
    elif node.node_type == NodeType.UPDATED and child.node_type == NodeType.UNCHANGED:
        stats['changes']['updated_caller'].add((node, child))
    elif node.node_type == NodeType.UPDATED and child.node_type == NodeType.UPDATED:
        stats['changes']['updated_version'].add((node, child))
    elif node.node_type == NodeType.UNCHANGED and child.node_type == NodeType.UPDATED:
        stats['changes']['updated_callee'].add((node, child))
    else:
        stats['changes']['uncaptured'].add((node, child))


def get_unique_name():
    global node_counter
    node_counter += 1
    return f"a{node_counter}"


class NodeType(Enum):
    UNCHANGED = 1,
    ADDED = 2,
    REMOVED = 3,
    UPDATED = 4


class Node:
    def __init__(self, name, version=1, incoming=None, outgoing=None, node_type=NodeType.UNCHANGED, level=-1):
        self.name = name
        self.version = version
        self.incoming = incoming if incoming is not None else set()
        self.outgoing = outgoing if outgoing is not None else set()
        self.node_type = node_type
        self.level = level
        self.deviation = 0
        self.cascaded_deviations = {}

    def __str__(self):
        return f"{self.name}: {self.node_type.name} inc: [{','.join(n.name for n in self.incoming)}] out: [{','.join(n.name for n in self.outgoing)}] level: {self.level}]"

    def print_with_deviation(self):
        return f"{self.name}: {self.node_type.name} inc: [{','.join(n.name for n in self.incoming)}] out: [{','.join(n.name for n in self.outgoing)}] deviation: {self.deviation} cascaded: [{','.join(n.name + ': ' + str(d) for n,d in self.cascaded_deviations.items())}]"

    def get_json_entry(self, version_inc=False):
        return {
            "service": self.name,
            "version": f"v{self.version if not version_inc else self.version+1}",
            "endpoint": f"GET http://{self.name}:8080/"
        }


if __name__ == '__main__':
    run()
