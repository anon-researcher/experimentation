# Topology-aware Continuous Experimentation in Microservice-based Applications - Online Appendix

This is the online appendix for our submission at Middleware'19. It provides the heuristics' source code, a full replication package for both the ranking quality evaluation and the performance evaluation, and additional screenshots of our interactive tooling.

### Table of Contents
1. **[Source Code](#source-code)**<br>
2. **[Screenshots UI](#screenshots-ui)**<br>
3. **[Ranking Quality Evaluation](#ranking-quality)**<br>
4. **[Performance Evaluation](#performance-evaluation)**<br>

### Source Code
The source code of the implemented heuristics can be found as part of the _performance evaluation_ replication package in the folder `performance_evaluation/src`. The overall algorithm is implemented in `rankingAlgorithm.ts`, the heuristics' implementations of _annotate_ and _extract_ phases are contained in `strategies.ts`. Note that `strategies.ts` contains more heuristics than presented in the paper and the naming of the heuristics is slightly different. Consult the documentation provided in `strategies.ts` for details.

Detailled instructions to build and execute the heuristics are covered in the [Performance Evaluation Replication Package](#performance-evaluation).

### Screenshots UI
Screenshots are presented [here](screenshots.md).

### Ranking Quality
The replication package for the _ranking quality evaluation_ can be found in the folder `ranking_quality_evaluation`. To execute both nDCG computation and data analysis an installation of _Python 3_ and _R_ (including package `tidyverse` is required.

The package consists of:
* Relevance ratings for all scenarios in folder `relevance` <br>
* Resulting rankings (heuristic output) for all scenarios in folders `running` and `multichange`<br>
* Script `ndcg.py` to compute nDCG scores based on the relevance ratings and rankings<br>
* Data Analysis script `script.R` to explore results and create plots<br>

Relevance ratings can be adjusted to explore how nDCG scores would change. For every sub-scenario there is a respective relevance-rating file in folder `relevance`. Every line contains a single change (i.e., source and target) plus the rating between 0 and 4.

To compute scores based on the given relevance ratings simply execute `python ndcg.py relevance`.
This creates a `results_ndcg.csv` file containing all nDCG scores for all scenarios, all heuristics, and multiple combinations of parameters (e.g., penalties, number of rankings to consider).

Use our _R_ script `script.R` to explore the results and replicate our plots on demand.


### Performance Evaluation

#### Installation Instructions
Replicating our performance evaluation requires:
1. Node.js (>= version 10.15)
2. NPM (>= version 6.9)
3. Python 3 
4. R (>= version 3.5) for data analysis only

#### Build Instructions
1. Switch directory `cd performance_evaluation`
2. `npm install`
3. `npm run build`

#### Difference Graphs
Due to their size the used difference graphs (broad and deep variants) are not included in the repository and need to be downloaded separately.

1. create folder `mkdir evaluation_data`
2. `cd evaluation_data`
3. Download _broad_ difference graphs from [here](https://figshare.com/s/0b92e30e27a420d8db6b)
4. Download _deep_ difference graphs from [here](https://figshare.com/s/8b8e17b2fb01f13ab705)
5. go back `cd ..`

#### Execution
The script `runner.py` is the main script for executing the performance evaluation. It will take care to feed the respective heuristic with difference graphs as input and monitors CPU and memory utilization. Check out `runner.py` for the various settings (e.g., how many repetitions) and adjust paths as required (e.g., output files for results). 

By default the results of heuristcs will be logged in a folder `logs`, make sure to create it before executing (i.e., `mkdir logs`).
Captured data on heuristic execution (e.g., execution time) will be stored in `results.txt` and utilization data in `utilization.txt`.

To replicate the evaluation on _broad_ difference graphs:
1. Uncompress `tar -xzf evaluation_data/broad.tar.gz --directory evaluation_data/`
2. Adjust parameters in `runner.py` (e.g., output file, default `results.txt`)
3. Run: `python runner.py`

To replicate the evaluation on _deep_ difference graphs:
1. Uncompress `tar -xzf evaluation_data/deep.tar.gz --directory evaluation_data/`
2. Adjust parameters in `runner.py` (e.g., output file, default `results.txt`)
2. Run: `python runner.py`

#### Data Analysis

To combine results on both structures of difference graphs (i.e., broad and deep) use the script `prepare.py` which creates a single resulting `overall_results.csv` file for data analysis. It will also combine the single result entries with details of the underlying graph (e.g., nodes, edges, average endpoint calls).

1. Adjust paths in `prepare.py` as required
2. Run `python prepare.py`

Explore the results using our _R_ script `performance.R` and create plots on demand.

#### Generating Difference Graphs

We also provide the script we used to generate difference graphs of multiple sizes and with various characteristics. The script is located in `evaluation_data/topology.py`.
Adjust parameters (e.g., maximum path lenghts, mean and SD values used to create nodes and calls, and change frequencies, probabilities that performance deviations are included and of which extent). Run the script using `python topology.py`. This will create output that can be fed to heuristics.
