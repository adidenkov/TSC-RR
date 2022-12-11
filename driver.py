#!/usr/bin/env python3
""" Run the simulation on each available dataset. """
import argparse
import cityflow
import json
import os
import shlex
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime

from display import load, save, table

DATA = "data"


# Load the template configuration
with open("config.json", 'r') as infile:
    config = json.load(infile)

# Locally stored results, combination of all runs
results = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))


# TODO: Do this more efficiently through CityFlow
cumul_vehicles, cumul_waiting = dict(), Counter()
def wait_time_callback(eng, includeWaiting=True):
    global cumul_vehicles, cumul_waiting
    types = eng.get_vehicle_type(includeWaiting)
    waiting = set(eng.get_vehicles(includeWaiting)) - set(dict(filter(
        lambda vs: vs[1] >= 0.1, eng.get_vehicle_speed().items())).keys())
    cumul_vehicles = dict(cumul_vehicles, **types)
    cumul_waiting += Counter(types[v] for v in waiting)

def get_average_wait_time_by_type(eng):
    wait = {t: (cumul_waiting[t], n) for t, n in Counter(cumul_vehicles.values()).items()}
    cws, ns = zip(*wait.values())
    wait['average'] = (sum(cws), sum(ns))
    return {t: cw/n for t, (cw, n) in wait.items()}

def run_scenario(scenario, trials=5, callback=None):
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
        global cumul_vehicles, cumul_waiting
        cumul_vehicles, cumul_waiting = dict(), Counter()
        eng = cityflow.Engine(f"{scenario}/config.json")
        for _ in range(3600):
            eng.next_step()
            wait_time_callback(eng)

        # Save statistics
        for typ, avg in eng.get_average_travel_time_by_type().items():
            results[name]['Travel time'][typ.capitalize()].append(avg)
        for typ, avg in get_average_wait_time_by_type(eng).items():
            results[name]['Wait time'][typ.capitalize()].append(avg)
        if callback:
            callback(results)

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
save_results = (lambda results: save(args.output, results)) if args.output else None

try:
    # Run only the requested scenarios
    if args.scenario:
        for dataset in args.scenario:
            if os.path.exists(dataset):
                run_scenario(dataset, args.trials, save_results)
            else:
                print(f"Scenario not found: {dataset}")

    # Find all downloaded datasets
    else:
        for directory in sorted(next(os.walk(DATA))[1], key=order):
            run_scenario(f"{DATA}/{directory}", args.trials, save_results)

# Save and display partial results
except KeyboardInterrupt:
    print("\nInterrupted")
print()

# Display results table
if not results:
    print("No scenarios were run")
    sys.exit(1)
print(table(results))