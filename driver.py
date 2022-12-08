#!/usr/bin/env python3
""" Run the simulation on each available dataset. """
import argparse
import cityflow
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

from display import save, table

DATA = "data"


# Load the template configuration
with open("config.json", 'r') as infile:
    config = json.load(infile)

# Locally stored results, combination of all runs
results = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))


def run_scenario(scenario):
    ''' Run the simulation on a given roadnet+flow.
    @param scenario: relative path of the containing directory.
    '''
    scenario = scenario.rstrip('/')
    name = scenario.split('/')[-1]
    print(f"Running: {name}".ljust(25) + "...", end='', flush=True)

    # Generate config file
    config["dir"] = f"{scenario}/"
    with open(f"{scenario}/config.json", 'w') as outfile:
        json.dump(config, outfile)

    # Run the simulation
    eng = cityflow.Engine(f"{scenario}/config.json")
    for _ in range(3600):
        eng.next_step()

    print("done")

    # Save statistics
    results[name]['Travel time']['Average'] = eng.get_average_travel_time()


# Parse arguments
parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-s', '--scenario', action='append', metavar="DIR",
    help=f"run using data in this directory\nExample: {DATA}/1-example\nDefault: run all")
parser.add_argument('-o', '--output', action='store', nargs='?',
    const=f"results_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}.json")
args = parser.parse_args()

# Warn about missing data
if not os.path.exists(DATA):
    print(f"Missing directory: {DATA}")
    print(f"Make sure to run ./get-data.sh")
    sys.exit(1)

try:
    # Run only the requested scenarios
    if args.scenario:
        for dataset in args.scenario:
            if os.path.exists(dataset):
                run_scenario(dataset)
            else:
                print(f"Scenario not found: {dataset}")

    # Find all downloaded datasets
    else:
        def order(dataset):
            num, name = dataset.split('-')
            return (int(num), name)
        for directory in sorted(next(os.walk(DATA))[1], key=order):
            run_scenario(f"{DATA}/{directory}")

# Save and display partial results
except KeyboardInterrupt:
    print("\nInterrupted")
print()

# Display results table
if args.output:
    save(args.output, results)
    print(f"Saved results to '{args.output}'\n")
print(table(results))