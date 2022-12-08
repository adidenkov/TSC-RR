#!/usr/bin/env python3
""" Utilities for displaying results. """
import argparse
import glob
import json
import sys
import pandas as pd


def table(results, precision=3):
    ''' Create a display-able table from raw results.
    @param results: nested dictionary of results.
    @param precision: number of decimal places to display.
    @returns: table of results.
    '''
    column_names = pd.DataFrame([[metric, t]
        for metric, types in next(iter(results.values())).items()
            for t in types.keys()],
        columns=["Scenario", ""])

    rows = [[round(val, precision)
        for types in result.values()
            for val in types.values()]
        for scenario, result in results.items()]

    index = results.keys()

    columns = pd.MultiIndex.from_frame(column_names)
    return pd.DataFrame(rows, columns=columns, index=index)


def save(filename, results):
    ''' Save the results dictionary to a file.
    @param filename: relative path of file.
    @param results: nested dictionary of results.
    '''
    with open(filename, 'w') as f:
        print(json.dumps(results), file=f)


def load(filename):
    ''' Get a results dictionary from a file.
    @param filename: relative path of file.
    @return: nested dictionary of results.
    '''
    with open(filename, 'r') as f:
        return json.load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('filename', nargs='?',
        help="Results file to use (defaults to most-recent)")
    args = parser.parse_args()
    try:
        filename = args.filename or sorted(glob.glob("results_*.json"))[-1]
    except IndexError:
        print(f"No results files found")
        sys.exit(1)
    print(f"Loading results from '{filename}'\n")
    print(table(load(filename)))