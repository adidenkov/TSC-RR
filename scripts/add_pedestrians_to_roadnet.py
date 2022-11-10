
import sys
import json
import argparse
import random

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add "sidewalks" and "pedestrians" to roadnet file.')
    parser.add_argument('input', help="The original flow file to which passengers will be added.")
    parser.add_argument('-o', '--output', help="The name of the new flow file (default=<input>_pedestrians.json).")

    args = parser.parse_args()

    if args.output is None:
        args.output = args.input.replace(".json", "_") + "pedestrians.json"

    orig_roadnet_file = args.input
    with open(orig_roadnet_file, "r") as f:
        roadnet_json = json.load(f)

        with open(args.output, "w") as o:
            json.dump(roadnet_json, o, indent=2)

