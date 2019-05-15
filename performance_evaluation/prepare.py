import csv

graph_stats = {
    'broad' : {},
    'deep': {}
}

with open("graph_stats.csv", newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # variant,type,depth,nodes,edges,calls
        if row['type'] not in graph_stats[row['variant']]:
            graph_stats[row['variant']][row['type']] = {}

        if row['depth'] not in graph_stats[row['variant']][row['type']]:
            graph_stats[row['variant']][row['type']][row['depth']] = {}

        graph_stats[row['variant']][row['type']][row['depth']]['nodes'] = row['nodes']
        graph_stats[row['variant']][row['type']][row['depth']]['edges'] = row['edges']
        graph_stats[row['variant']][row['type']][row['depth']]['calls'] = row['calls']

broad_file = "./stats/broad/result.txt"
deep_file = "./stats/deep/result.txt"

out_file = "overall_results.csv"

variants = ["broad", "deep"]

with open(out_file, "w") as out:

    out.write("strategyID,endTime,algorithmStartTime,algorithmDuration,startTime,setupDuration,duration,variation,frequency,depth,deviation,nodes,edges,calls\n")
    for variant in variants:
        print(f"preparing '{variant}' results:")

        with open(broad_file if variant == "broad" else deep_file, "r") as file:

            for line in file:
                content = line.split(",")
                # strategyID, endTime, algorithmStartTime, algorithmDuration, startTime, setupDuration, duration, path
                details = content[7].split("/")

                # evaluation_data/low/out_2 /graph_0.json
                eval_type = details[1]
                depth = details[2].split("_")[1]
                deviation = details[3][6:].split('.')[0]

                nodes = graph_stats[variant][eval_type][depth]['nodes']
                edges = graph_stats[variant][eval_type][depth]['edges']
                calls = graph_stats[variant][eval_type][depth]['calls']

                out.write(",".join(content[:-1]) + "," + f"{variant},{eval_type},{depth},{deviation},{nodes},{edges},{calls}\n")