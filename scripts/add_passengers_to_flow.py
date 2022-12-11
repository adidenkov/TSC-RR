
import sys
import json
import argparse
import random

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add "passengers" parameter to all vehicles in flow file.')
    parser.add_argument('input', help="The original flow file to which passengers will be added.")
    parser.add_argument('-o', '--output', help="The name of the new flow file (default=<input>_passengers.json).")
    parser.add_argument('-s', '--seed', type=int, default=5834, help="Value of the random seed.")
    parser.add_argument('--random', action="store_true", help="# passengers will be random number between 1 and 4 (inclusive).")
    parser.add_argument('--nudge', action="store_true", help="add a small amount of variation to vehicle starting times.")

    args = parser.parse_args()
    random.seed(args.seed)

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
            vehicle_info["vehicle"]["type"] = "car"
            if args.nudge:
                nudge = random.randint(-10,10)
                for key in ["startTime", "endTime"]:
                    if vehicle_info[key] != -1:
                        vehicle_info[key] = max(0, vehicle_info[key] + nudge)
        with open(args.output, "w") as o:
            json.dump(flow_json, o)

