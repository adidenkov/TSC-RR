
import sys
import json
import argparse
import random
from copy import deepcopy

def get_available_sidewalks(current_sidewalk, roadnet, exclude_ids):
    next_intersection_id = current_sidewalk["endIntersection"]
    next_intersection = [x for x in roadnet["intersections"] if x["id"] == next_intersection_id][0]
    options = [x["endRoad"] for x in next_intersection["roadLinks"] if x["startRoad"]==current_sidewalk["id"] and x["endRoad"] not in exclude_ids]
    return options



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Adds random pedestrian flows on sidewalks.')
    parser.add_argument('input', help="The original flow file which should INCLUDE PASSENGERS.")
    parser.add_argument('roadnet', help="The roadnet file which should INCLUDE SIDEWALKS.")
    parser.add_argument('-o', '--output', help="The name of the new flow file (default=<input>_pedestrians.json).")
    parser.add_argument('-n', '--number', type=int, default=1, help="# of pedestrian flows that will be added.")

    args = parser.parse_args()

    if args.output is None:
        args.output = args.input.replace(".json", "_") + "pedestrians.json"

    stdp = open("standard_pedestrian.json", "r")
    standard_pedestrian = json.load(stdp)
    stdp.close()

    in_flow_file = args.input
    with open(in_flow_file, "r") as f:
        flow_json = json.load(f)
        
        with open(args.roadnet, "r") as roadnet_file:
            roadnet = json.load(roadnet_file)

            sidewalk_dict = {}
            for intersection in [x for x in roadnet["intersections"] if x["sidewalk"]]:
                for sidewalk_id in intersection["roads"]:
                    sidewalk_dict[sidewalk_id] = [x for x in roadnet["roads"] if x["id"] == sidewalk_id][0]
            sidewalk_ids = [sidewalk_dict[x]["id"] for x in sidewalk_dict]


            for i in range(args.number):
                # Build new route:
                # 1. Pick random starting sidewalk
                # 2. Pick random connected sidewalk that is not in route
                # 3. Repeat some number of times
                sidewalk_intersections = [x for x in roadnet["intersections"] if x["sidewalk"]]
                new_route = []

                start = random.choice(sidewalk_intersections)["id"]
                sidewalk_intersections = [x for x in sidewalk_intersections if x["id"] != start]
                # end = random.choice(sidewalk_intersections)["id"]
                # new_route.append(start)
                # new_route.append(end)


                count = 0
                random_intersection = random.choice(sidewalk_intersections)
                current_sidewalk_id = random.choice(random_intersection["roads"])
                # current_sidewalk = [x for x in roadnet["roads"] if x["id"] == current_sidewalk_id][0]
                current_sidewalk = sidewalk_dict[current_sidewalk_id]
                new_route.append(current_sidewalk["id"])
                while (current_sidewalk_id == new_route[0]):
                    current_sidewalk_id = random.choice(sidewalk_ids)
                new_route.append(current_sidewalk_id)

                # options = get_available_sidewalks(current_sidewalk, roadnet, new_route)
                # if len(options) > 0:
                #     new_route.append(random.choice(options))

                # while (len(options) > 0 and count < 12):
                #     print(options)
                #     current_sidewalk_id = random.choice(options)
                #     current_sidewalk = sidewalk_dict[current_sidewalk_id]
                #     new_route.append(current_sidewalk["id"])
                #     options = get_available_sidewalks(current_sidewalk, roadnet, new_route)
                #     count += 1

                new_pedestrian = deepcopy(standard_pedestrian)
                new_pedestrian["route"].extend(new_route)
                flow_json.append(new_pedestrian)

            # # Fix existing routes so that they go through splits
            # road_dict = {r["id"]: r for r in roadnet["roads"]}
            # for flow in flow_json:
            #     fixed_route = []
            #     for item in flow["route"]:
            #         if 
        
        with open(args.output, "w") as o:
            json.dump(flow_json, o)

