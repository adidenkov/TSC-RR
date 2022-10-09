#!/usr/bin/env python3
""" Run the simulation on each available dataset. """
import cityflow
import json
import os


# Load the template configuration
with open("config.json", 'r') as infile:
    config = json.load(infile)

# Find all downloaded datasets
def order(dataset):
    num, name = dataset.split('-')
    return (int(num), name)
for dataset in sorted(next(os.walk("data"))[1], key=order):
    print(f"Running: {dataset}".ljust(25) + "...", end='', flush=True)

    # Generate config file
    config["dir"] = f"data/{dataset}/"
    with open(f"data/{dataset}/config.json", 'w') as outfile:
        json.dump(config, outfile)

    # Run the simulation
    eng = cityflow.Engine(f"data/{dataset}/config.json")
    for _ in range(100):
        eng.next_step()

    print("done")