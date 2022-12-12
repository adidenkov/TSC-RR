
import sys
import json
import argparse
import random
from copy import deepcopy

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Copies random car flows and turns them into "busses". NOTE: This means that there should be at least n flows specified if up to n busses are desired.')
    parser.add_argument('input', help="The original flow file which should INCLUDE PASSENGERS.")
    parser.add_argument('-o', '--output', help="The name of the new flow file (default=<input>_buses.json).")
    parser.add_argument('-n', '--number', type=int, default=1, help="# of bus flows that will be added.")
    parser.add_argument('-f', '--fraction', type=float, default=0.05, help="%% of bus flows that will be added.")
    parser.add_argument('-p', '--passenger_scale', type=float, default=5.0, help="A coefficient by which to scale the passenger count of copied vehicle.")
    parser.add_argument('-s', '--seed', type=int, default=5834, help="Value of the random seed.")

    args = parser.parse_args()
    random.seed(args.seed)

    if args.output is None:
        args.output = args.input.replace(".json", "_") + "buses.json"

    in_flow_file = args.input
    with open(in_flow_file, "r") as f:
        flow_json = json.load(f)
        num = min(max(args.number, round(len(flow_json)*args.fraction)), len(flow_json))
        copy_to_busses = random.sample(flow_json, num)
        for vehicle_info in copy_to_busses:
            new_bus = deepcopy(vehicle_info)
            new_bus["vehicle"]["length"] = 15
            new_bus["vehicle"]["passengers"] = (int)(args.passenger_scale * new_bus["vehicle"]["passengers"])
            new_bus["vehicle"]["type"] = "bus"
            new_bus["interval"] = 10 * new_bus["interval"]
            new_bus["endTime"] = -1
            flow_json.append(new_bus)
        with open(args.output, "w") as o:
            json.dump(flow_json, o)
            print(f"Added {num} bus flows")

