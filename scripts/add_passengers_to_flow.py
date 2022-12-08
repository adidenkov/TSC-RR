
import sys
import json
import argparse
import random

if __name__ == "__main__":
    random.seed(5834)
    parser = argparse.ArgumentParser(description='Add "passengers" parameter to all vehicles in flow file.')
    parser.add_argument('input', help="The original flow file to which passengers will be added.")
    parser.add_argument('-o', '--output', help="The name of the new flow file (default=<input>_passengers.json).")
    parser.add_argument('--random', action="store_true", help="# passengers will be random number between 1 and 4 (inclusive).")

    args = parser.parse_args()

    if args.output is None:
        args.output = args.input.replace(".json", "_") + "passengers.json"

    in_flow_file = args.input
    with open(in_flow_file, "r") as f:
        flow_json = json.load(f)
        for vehicle_info in flow_json:
            if "passengers" not in vehicle_info["vehicle"].keys():
                if args.random:
                    vehicle_info["vehicle"]["passengers"] = random.randint(1,4)
                else:
                    vehicle_info["vehicle"]["passengers"] = 1
        with open(args.output, "w") as o:
            json.dump(flow_json, o)

