import subprocess
import time

result_file = 'result.txt'

repetitions = 5

deviation_probabilities = [0,5,10,20,30]

steps = [i for i in range(2,12)]  # for broad graphs
# steps = [i for i in range(2,26)]  # for deep graphs

types = ['low', 'midlow', 'midhigh', 'high']

strategies = [i for i in range(0,12)]

print("Starting monitoring helper")
monitoring = subprocess.Popen(args=['node', 'dist/monitoring.js', 'utilization.txt', '500'])

print("Waiting 5 secs to start benchmarking...")
time.sleep(5)

for rep in range(0, repetitions):
    print(f"Start repetition: {rep+1}", flush=True)

    for type in types:
        print(f"Type: {type}", flush=True)

        for step in steps:
            print(f"Trace depth: {step}", flush=True)

            summary_path = f"evaluation_data/{type}/out_{step}/summary.json"
            print(f"summary-path: {summary_path}", flush=True)
            for strategy in strategies:
                print(f"Run strategy: {strategy}", flush=True)

                for deviation in deviation_probabilities:
                    interaction_path = f"evaluation_data/{type}/out_{step}/graph_{deviation}.json"
                    subprocess.call(args=['node', 'dist/app.js', str(strategy), interaction_path, summary_path, result_file, f"logs/log_{type}_{step}_{strategy}_{deviation}.json"])
            print("---", flush=True)
        print("---------", flush=True)
    print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", flush=True)

print("Benchmarking done, stopping monitoring")
monitoring.terminate()
time.sleep(5)
