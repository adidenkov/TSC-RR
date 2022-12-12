#!/usr/bin/env python3
""" Utilities for displaying results. """
import argparse
import glob
import json
import statistics
import sys
import pandas as pd

from collections import defaultdict


def table(results, precision=2, per_vehicle=False):
    ''' Create a display-able table from raw results.
    @param results: nested dictionary of results.
    @param precision: number of decimal places to display.
    @returns: table of results.
    '''
    key1 = lambda x: 'z' if x.startswith('Average') else x
    key2 = lambda x: tuple(map(key1, x))
    names = sorted(([metric, t]
        for metric, types in next(iter(results.values())).items()
            for t in types.keys()), key=key2)
    column_names = pd.DataFrame(names, columns=["Scenario", ""])

    rows = map(lambda l: map(lambda val:
        f"{f'{statistics.mean(val[per_vehicle]):.{precision}f}' if val[per_vehicle] else '--'}"
        f"{f'±{statistics.stdev(val[per_vehicle]):.{precision}f}' if len(val[per_vehicle]) > 1 else ''}", l),
        [[result[mtr][typ]
            for mtr, typ in names]
                for result in results.values()])

    index = results.keys()

    columns = pd.MultiIndex.from_frame(column_names)
    return pd.DataFrame(rows, columns=columns, index=index)


def save(filename, results):
    ''' Save the results dictionary to a file.
    @param filename: relative path of file.
    @param results: nested dictionary of results.
    '''
    with open(filename, 'w') as f:
        print(json.dumps(results, indent='\t'), file=f)


def load(filename):
    ''' Get a results dictionary from a file.
    @param filename: relative path of file.
    @return: nested dictionary of results.
    '''
    with open(filename, 'r') as f:
        return defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [[],[]])), json.load(f))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('filename', nargs='?',
        help="Results file to use (defaults to most-recent)")
    parser.add_argument('-p', '--precision', type=int, default=2,
        help="Number of decimals to display  (defaults to 3)")
    parser.add_argument('--per-vehicle', action="store_true",
        help="Legacy per-vehicle averaging scheme")
    args = parser.parse_args()
    try:
        filename = args.filename or sorted(glob.glob("results_*.json"))[-1]
    except IndexError:
        print(f"No results files found")
        sys.exit(1)
    print(f"Loading results from '{filename}'\n")
    print(table(load(filename), args.precision, args.per_vehicle))