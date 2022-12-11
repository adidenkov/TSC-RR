#!/usr/bin/env python3
""" Run the simulation on each available dataset. """
import argparse
import cityflow
import json
import os
import shlex
import subprocess
import sys
from collections import defaultdict
from datetime import datetime

from display import load, save, table

DATA = "data"


# Load the template configuration
with open("config.json", 'r') as infile:
    config = json.load(infile)

# Locally stored results, combination of all runs
results = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))


def run_scenario(scenario, trials=5):
    ''' Run the simulation on a given roadnet+flow.
    @param scenario: relative path of the containing directory.
    '''
    scenario = scenario.rstrip('/')
    name = scenario.split('/')[-1]
    print(f"Running: {name}".ljust(25), end='', flush=True)

    # Generate config file
    config["dir"] = f"{scenario}/"
    config["flowFile"] = "flow-pass.json"
    for i in range(trials):
        print('.', end='', flush=True)
        if len(results[name]['Travel time']['Average']) > i:
            continue
        config["seed"] = i
        with open(f"{scenario}/config.json", 'w') as outfile:
            json.dump(config, outfile)

        # Create the scenarios
        subprocess.run(shlex.split(f"python3 ./scripts/add_passengers_to_flow.py "
            f"{scenario}/flow.json -o {scenario}/flow-pass.json --random -s {i} --nudge"))

        # Run the simulation
        eng = cityflow.Engine(f"{scenario}/config.json")
        for _ in range(3600):
            eng.next_step()

        # Save statistics
        results[name]['Travel time']['Average'].append(eng.get_average_travel_time())

    print("done")


# Run easier scenarios first
def order(dataset):
    num, name = dataset.split('/')[-1].split('-')
    return (int(num), name)

# Parse arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-s', '--scenario', action='append', nargs='*', metavar="DIR",
    help=f"run with data in this directory\nExample: {DATA}/1-example\nDefault: run all")
parser.add_argument('-o', '--output', action='store', nargs='?', metavar="JSON",
    const=f"results_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.json",
    help=f"save results to this file\nDefault: results_date_time.json")
parser.add_argument('-i', '--input', metavar="JSON",
    help=f"continue from a previous result")
parser.add_argument('-t', '--trials', type=int, default=5,
    help=f"trials to run for each scenario")
args = parser.parse_args()
if args.scenario:
    args.scenario = sorted(set(s.rstrip('/') for l in args.scenario for s in l), key=order)

# Warn about missing data
if not os.path.exists(DATA):
    print(f"Missing directory: {DATA}")
    print(f"Make sure to run ./get-data.sh")
    sys.exit(1)

# Load a previous result
if args.input:
    results = load(args.input)

try:
    # Run only the requested scenarios
    if args.scenario:
        for dataset in args.scenario:
            if os.path.exists(dataset):
                run_scenario(dataset, args.trials)
            else:
                print(f"Scenario not found: {dataset}")

    # Find all downloaded datasets
    else:
        for directory in sorted(next(os.walk(DATA))[1], key=order):
            run_scenario(f"{DATA}/{directory}", args.trials)

# Save and display partial results
except KeyboardInterrupt:
    print("\nInterrupted")
print()

# Display results table
if not results:
    print("No scenarios were run")
    sys.exit(1)
if results and args.output:
    save(args.output, results)
    print(f"Saved results to '{args.output}'\n")
print(table(results))