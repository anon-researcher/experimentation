import {RankingAlgorithm} from "./rankingAlgorithm";

import {DiffType, Edge} from "./types/types";
import {CommonCall, DiffCall, UpdatedSourceVersion, UpdatedTargetVersion, UpdatedVersion} from "./types/callTypes";
import {SimulatedComparison, SimulatedSimpleStatistics} from "./types/statisticTypes";
import * as fs from "fs";
import {Strategy} from "./strategies";

let algorithm = new RankingAlgorithm();

let edge_dict = new Map<string, Map<string, Edge>>();

if(process.argv.length !== 7 && !isNaN(parseInt(process.argv[2]))) {
    console.log("Usage: node app.js <strategyID> <graph.json> <summary.json> <benchmark_file> <log_file>");
    process.exit();
}

let strategyID = parseInt(process.argv[2]) % 12;
let graph_path = process.argv[3];
let summary_path = process.argv[4];

console.log("Start benchmarking " + Strategy[strategyID]);
let startOverall = Date.now();
prepareEdgeDictionary(edge_dict, graph_path);
let endpoints = JSON.parse(fs.readFileSync(summary_path, 'utf-8')).endpoints;
let endPrepare = Date.now();

// let iterations = 10;
//
//
// // @ts-ignore
// let strategies = Object.keys(Strategy).map(k => Strategy[k]).filter(v => typeof v === "number") as number[];

// console.log(strategies.join(","));
//
// strategies.forEach(strategy => {

algorithm.strategy = strategyID;

let startTime = Date.now();
let result = algorithm.rank(edge_dict, endpoints, "target");
let endTime = Date.now();

let preparation = endPrepare - startOverall;
let runtime = endTime - startTime;
let overall = endTime - startOverall;

console.log("  |-> algorithm: " + runtime + " ms, prepare: " + preparation + " ms, overall: " + overall + " ms");

fs.writeFileSync(process.argv[6], JSON.stringify(result.slice(0,10)), {flag: 'a'});
fs.writeFileSync(process.argv[5], strategyID + "," + endTime + "," + startTime + "," + runtime + "," + startOverall + "," + preparation + "," + overall + "," + graph_path + "\n", {flag: 'a'});

// });

// (function repeat(counter) {
//     setTimeout(function () {
//         let start = Date.now();
//         algorithm.rank(edge_dict, endpoints, "target");
//         let end = Date.now();
//
//         let runtime = end - start
//         console.log("iteration " + (iterations - counter + 1) + ": " + runtime + " ms");
//
//         if (--counter) {
//             repeat(counter);
//         }else {
//             console.log("done");
//         }
//     }, 100)
// })(iterations);











// ---------------------------------------------------------------------------------------------------------------------
/* helper functions for preparing input data */
function prepareEdgeDictionary(edge_dict: Map<string, Map<string, Edge>>, graph_path: string): void {

    let interaction_graph = JSON.parse(fs.readFileSync(graph_path, 'utf-8'));

    interaction_graph['calling_new_ep'].forEach((entry: any) => {
        let edge: Edge = getEdge(entry, edge_dict);
        edge.addCall(new DiffCall(entry.source, entry.target, DiffType.ADD_CALL_TO_NEW_SERVICE,
            new SimulatedSimpleStatistics()));
    });

    interaction_graph['calling_ex_ep'].forEach((entry: any) => {
        let edge: Edge = getEdge(entry, edge_dict);
        edge.addCall(new DiffCall(entry.source, entry.target, DiffType.ADD_CALL_TO_EXISTING_ENDPOINT,
            new SimulatedSimpleStatistics()));
    });

    interaction_graph['removing'].forEach((entry: any) => {
        let edge: Edge = getEdge(entry, edge_dict);
        edge.addCall(new DiffCall(entry.source, entry.target, DiffType.REMOVE_CALL, new SimulatedSimpleStatistics()));
    });

    interaction_graph['common'].forEach((entry: any) => {
        let edge: Edge = getEdge(entry, edge_dict);
        edge.addCall(new CommonCall(entry.source, entry.target,
            new SimulatedComparison(entry.stats.critical, entry.stats.maxDeviation)));
    });

    interaction_graph['updated_caller'].forEach((entry: any) => {
        let edge: Edge = getEdge(entry, edge_dict);
        edge.addCall(new UpdatedSourceVersion(entry.source, entry.target, entry.oldSourceVersion,
            new SimulatedComparison(entry.stats.critical, entry.stats.maxDeviation)));
    });

    interaction_graph['updated_callee'].forEach((entry: any) => {
        let edge: Edge = getEdge(entry, edge_dict);
        edge.addCall(new UpdatedTargetVersion(entry.source, entry.target, entry.oldTargetVersion,
            new SimulatedComparison(entry.stats.critical, entry.stats.maxDeviation)));
    });

    interaction_graph['updated_version'].forEach((entry: any) => {
        let edge: Edge = getEdge(entry, edge_dict);
        edge.addCall(new UpdatedVersion(entry.source, entry.target, entry.oldSourceVersion, entry.oldTargetVersion,
            new SimulatedComparison(entry.stats.critical, entry.stats.maxDeviation)));
    });
}

function getEdge(entry: any, edge_dict: Map<string, Map<string, Edge>>) : any {

    if(!edge_dict.has(entry.source.service)) {
        edge_dict.set(entry.source.service, new Map<string, Edge>());
    }
    // !. => non-null assertion operator, we know based on the block before that the key exists
    if(!edge_dict.get(entry.source.service)!.has(entry.target.service)) {
        let edge = new Edge(entry.source.service, entry.target.service);
        edge_dict.get(entry.source.service)!.set(entry.target.service, edge);
        return edge;
    }else {
        return edge_dict.get(entry.source.service)!.get(entry.target.service);
    }
}