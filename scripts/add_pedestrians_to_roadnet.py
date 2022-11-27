
import sys
import json
import argparse
import random
import math

from copy import deepcopy

# Steps:
#   1. Find intersections where virtual=false (only visible intersections)
#   2. Find the roads specified in the "roads" field
#   3. For each road in roads, find those that are "parallel". Find roads where points[0] and points[1] are switched (swapped start/end coordinates)
#   4. 

def get_angle(cornerx, cornery, x1, y1, x2, y2):
    v1 = (x1-cornerx, y1-cornery)
    v2 = (x2-cornerx, y2-cornery)
    # From https://www.codespeedy.com/calculate-angle-between-two-vectors-in-python/
    dotProduct = v1[0]*v2[0] + v1[1]*v2[1]
    modOfVector1 = math.sqrt( v1[0]*v1[0] + v1[1]*v1[1])*math.sqrt(v2[0]*v2[0] + v2[1]*v2[1]) 
    angle = dotProduct/modOfVector1
    return angle

def is_clump_in_list(clump, clumplist):
    for c in clumplist:
        listroads_ids = [x["id"] for x in c]
        listroads_ids.sort()
        clump_ids = [x["id"] for x in clump]
        clump_ids.sort()
        if (listroads_ids == clump_ids):
            return True
    
    return False

# Returns a list of road's start and end points: [(startx, starty), (endx, endy)]
def get_roadpoints(road):
    return [(road["points"][0]["x"], road["points"][0]["y"]), (road["points"][1]["x"], road["points"][1]["y"])]

class SidewalkIntersectionInfo:
    def __init__(self, position, intersection_position, clump1_endpoint, clump2_endpoint, intersection, clump):
        self.position = position
        self.intersection_position = intersection_position
        self.c1e = clump1_endpoint
        self.c2e = clump2_endpoint
        self.intersection = intersection
        self.clump = clump

class ClumpInfo:
    def __init__(self, points):
        self.points = points
        self.matching_intersections1
        self.matching_intersections2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add "sidewalks" to roadnet file.')
    parser.add_argument('input', help="The original roadnet file to which passengers will be added.")
    parser.add_argument('-o', '--output', help="The name of the new sidewalks roadnet file (default=<input>_sidewalks.json).")

    args = parser.parse_args()

    if args.output is None:
        args.output = args.input.replace(".json", "_") + "sidewalks.json"

    stdsi = open("standard_sidewalk_intersection.json", "r")
    standard_sidewalk_intersection = json.load(stdsi)
    stdsi.close()
    # print(standard_sidewalk_intersection)

    stds = open("standard_sidewalk.json", "r")
    standard_sidewalk = json.load(stds)
    stds.close()
    # print(standard_sidewalk)

    stdrl = open("standard_roadlink.json", "r")
    standard_roadlink = json.load(stdrl)
    stdrl.close()

    debug_print = False
    debug_intersection_ids = ["42430474", "42429314"]

    orig_roadnet_file = args.input
    with open(orig_roadnet_file, "r") as f:
        roadnet_json = json.load(f)
        intersections = roadnet_json["intersections"]   # array of intersections
        intersections_dict = {i["id"]: i for i in intersections}
        true_intersections = []
        for intersection in intersections:
            intersection["sidewalk"] = False
            if(not intersection["virtual"] and not intersection["sidewalk"]):
                true_intersections.append(intersection)

        num_intersections = len(true_intersections)
        count = 0
        sidewalk_intersection_count = 0
        sidewalk_count = 0
        all_sidewalk_intersection_info = []
        all_clumps = []
        clump_info = []
        crosswalks = []
        for intersection in true_intersections:
            if intersection["id"] in debug_intersection_ids:
                debug_print = True
            else:
                debug_print = False

            location = (intersection["point"]["x"], intersection["point"]["y"])
            # Analyze roads in this intersection
            roads = []
            road_ids = []
            for road_id in intersection["roads"]:
                for road in roadnet_json["roads"]:
                    if (road["id"] == road_id):
                        roads.append(road)
                        road_ids.append(road_id)
            
            clumps = []
            clumped_ids = []
            for i in range(len(roads)):
                c = []
                for q in range(i+1, len(roads)):
                    # If start and end of 1st == start and end of 2nd OR if start and end of 1st == end and start of 2nd
                    if (roads[i]["startIntersection"] == roads[q]["startIntersection"] and roads[i]["endIntersection"] == roads[q]["endIntersection"]) or (roads[i]["endIntersection"] == roads[q]["startIntersection"] and roads[i]["startIntersection"] == roads[q]["endIntersection"]):
                        # Only add if haven't clumped
                        if (roads[q]["id"] not in clumped_ids):
                            clumped_ids.append(roads[q]["id"])
                            c.append(roads[q])
                # Only add if haven't clumped
                if (roads[i]["id"] not in clumped_ids):
                    clumped_ids.append(roads[i]["id"])
                    c.append(roads[i])
                    clumps.append(c)

            # Remove empty clumps (though there should be none)
            clumps = [clump for clump in clumps if len(clump) > 0]

            clumpids = [[road["id"] for road in clump] for clump in clumps]
            if debug_print:
                print("Clump IDs: {}".format(clumpids))

            # Ignore intersections with 2 or fewer clumps
            if (len(clumps) <= 2):
                continue
            
            clump_widths = []
            for clump in clumps:
                width = 0
                for road in clump:
                    for lane in road["lanes"]:
                        width += lane["width"]
                clump_widths.append(width)

            all_clumps.extend(clumps)
            
            # Number of sidewalk intersections depend on number of clumps
            # Calculate points where clumps meet intersection 
            clump_intersect_points = []
            for i in range(len(clumps)):
                # One endpoint is common intersection... Get other endpoint here
                if (clumps[i][0]["startIntersection"] == intersection["id"]):
                    end_point = (intersections_dict[clumps[i][0]["endIntersection"]]["point"]["x"], intersections_dict[clumps[i][0]["endIntersection"]]["point"]["y"])
                else:
                    end_point = (intersections_dict[clumps[i][0]["startIntersection"]]["point"]["x"], intersections_dict[clumps[i][0]["startIntersection"]]["point"]["y"])  

                # print(end_point)
                angle = math.atan2(end_point[1]-location[1], end_point[0]-location[0])
                # radius = 1*clump_widths[i]
                radius = 16
                x = location[0] + (radius*math.cos(angle))
                y = location[1] + (radius*math.sin(angle))

                # Keep track of clump info, too
                clump_intersect_points.append((x,y, clump_widths[i], location, end_point, clumps[i]))

                if debug_print:
                    print("clump meets intersection: {},{} (width: {})".format(x, y, clump_widths[i]))
            
            # Sort them by angle around intersection location
            # This allows me to know that adjacent coordinates should be connected by sidewalk
            clump_intersect_points.sort(key = lambda ci: math.atan2(ci[1]-location[1], ci[0]-location[0]))
            if debug_print:
                print("Clumps Intersection Points: {}".format(clump_intersect_points))
            
            # print([x[4] for x in clump_intersect_points])
            
            # Go around, determining sidewalk intersection positions as midpoints of adjacent clump intersects
            sidewalk_intersect_positions = []
            for i in range(len(clump_intersect_points)):
                adjacent_idx = (i+1) % len(clump_intersect_points)
                start = clump_intersect_points[i]
                end = clump_intersect_points[adjacent_idx]
                # new_position = (((end[0]-start[0])/2)+location[0], ((end[1]-start[1])/2)+location[1])
                new_position = (((end[0]-start[0])/2)+start[0], ((end[1]-start[1])/2)+start[1])
                if debug_print:
                    print("Start: {}, End: {}, Midpt: {}".format(start, end, new_position))
                sidewalk_intersect_positions.append(new_position)
            
            # Find average intersection location and move a bit away from it
            location_avg = [sum(t)/len(sidewalk_intersect_positions) for t in zip(*sidewalk_intersect_positions)]
            new_sidewalk_intersection_positions = []
            for position in sidewalk_intersect_positions:
                angle = math.atan2(position[1]-location_avg[1], position[0]-location_avg[0])
                # radius = 1*clump_widths[i]
                offset = 22
                x = position[0] + (offset*math.cos(angle))
                y = position[1] + (offset*math.sin(angle))
                new_sidewalk_intersection_positions.append((x,y))
            sidewalk_intersect_positions = new_sidewalk_intersection_positions
            
            if debug_print:
                print("Sidewalk intersection positions: {}".format(sidewalk_intersect_positions))

            # Make new sidewalk intersections
            new_sidewalk_intersections = []
            for position in sidewalk_intersect_positions:
                new_sidewalk_intersection = deepcopy(standard_sidewalk_intersection)
                new_sidewalk_intersection["id"] = new_sidewalk_intersection["id"] + str(sidewalk_intersection_count)
                new_sidewalk_intersection["point"]["x"] = position[0]
                new_sidewalk_intersection["point"]["y"] = position[1]
                sidewalk_intersection_count += 1
                new_sidewalk_intersections.append(new_sidewalk_intersection)
                intersections.append(new_sidewalk_intersection)

            # Make new sidewalks at intersections
            new_sidewalks = []
            for i in range(len(new_sidewalk_intersections)):
                adjacent_idx = (i+1) % len(new_sidewalk_intersections)
                startpos = new_sidewalk_intersections[i]["point"]
                endpos = new_sidewalk_intersections[adjacent_idx]["point"]
                new_sidewalk = deepcopy(standard_sidewalk)
                new_sidewalk["id"] = new_sidewalk["id"] + str(sidewalk_count)
                new_sidewalk["points"][0]["x"] = startpos["x"]
                new_sidewalk["points"][0]["y"] = startpos["y"]
                new_sidewalk["points"][1]["x"] = endpos["x"]
                new_sidewalk["points"][1]["y"] = endpos["y"]
                new_sidewalk["startIntersection"] = new_sidewalk_intersections[i]["id"]
                new_sidewalk["endIntersection"] = new_sidewalk_intersections[adjacent_idx]["id"]

                sidewalk_count += 1
                new_sidewalks.append(new_sidewalk)
                crosswalks.append(new_sidewalk)
                roadnet_json["roads"].append(new_sidewalk)

                startpos = new_sidewalk_intersections[adjacent_idx]["point"]
                endpos = new_sidewalk_intersections[i]["point"]
                new_sidewalk = deepcopy(standard_sidewalk)
                new_sidewalk["id"] = new_sidewalk["id"] + str(sidewalk_count)
                new_sidewalk["points"][0]["x"] = startpos["x"]
                new_sidewalk["points"][0]["y"] = startpos["y"]
                new_sidewalk["points"][1]["x"] = endpos["x"]
                new_sidewalk["points"][1]["y"] = endpos["y"]
                new_sidewalk["startIntersection"] = new_sidewalk_intersections[i]["id"]
                new_sidewalk["endIntersection"] = new_sidewalk_intersections[adjacent_idx]["id"]

                sidewalk_count += 1
                new_sidewalks.append(new_sidewalk)
                crosswalks.append(new_sidewalk)
                roadnet_json["roads"].append(new_sidewalk)
            
            if debug_print:
                print("New Sidewalks: {}".format(new_sidewalks))

            if (count%20 == 0):
                print("Added sidewalk intersections to {}/{}".format(count, num_intersections))
            count += 1

            # Organize sidewalk/clump intersection info for later
            # print([x for x in clump_intersect_points])
            # print(location)
            # for x in clump_intersect_points:
            #     print(x)
            # print(len(sidewalk_intersect_positions))
            for i in range(len(sidewalk_intersect_positions)):
                adjacent_idx = (i+1) % len(clump_intersect_points)
                # print("sidewalk intersection position: ", (sidewalk_intersect_positions[i][0],sidewalk_intersect_positions[i][1]))
                # print("attached intersection location: ", location)
                # print("clump1: ", clump_intersect_points[i][4])
                # print("clump2: ", clump_intersect_points[adjacent_idx][4])
                all_sidewalk_intersection_info.append(SidewalkIntersectionInfo((sidewalk_intersect_positions[i][0],sidewalk_intersect_positions[i][1]), location, clump_intersect_points[i][4], clump_intersect_points[adjacent_idx][4], new_sidewalk_intersections[i], clump_intersect_points[i][5]))

        # Connect sidewalk intersections along roads
        unique_clumps = []
        [unique_clumps.append(x) for x in all_clumps if not is_clump_in_list(x, unique_clumps)]
        all_clumps = unique_clumps
        # print([[i["id"] for i in x] for x in all_clumps])
        # print(len(all_clumps))
        clumps_to_do = len(all_clumps)
        count = 0

        # for i in range(clumps_to_do):
        #     # road = roadnet_json["roads"][i]
        #     road = all_clumps[i][0]
        #     road_startpoint = (road["points"][0]["x"], road["points"][0]["y"])
        #     road_endpoint = (road["points"][1]["x"], road["points"][1]["y"])
        connectors = []
        for intersection in true_intersections:
            road_startpoint = (intersection["point"]["x"], intersection["point"]["y"])

            viable_starts = [x for x in all_sidewalk_intersection_info if x.intersection_position == road_startpoint]
            # print([x.position for x in viable_starts])
            for start in viable_starts:
                viable_ends = [x for x in all_sidewalk_intersection_info if start.intersection_position == x.c1e and (start.c2e == x.intersection_position)]
                for end in viable_ends:
                    startpos = start.position
                    endpos = end.position
                    new_sidewalk = deepcopy(standard_sidewalk)
                    new_sidewalk["id"] = new_sidewalk["id"] + str(sidewalk_count)
                    new_sidewalk["points"][0]["x"] = startpos[0]
                    new_sidewalk["points"][0]["y"] = startpos[1]
                    new_sidewalk["points"][1]["x"] = endpos[0]
                    new_sidewalk["points"][1]["y"] = endpos[1]
                    new_sidewalk["startIntersection"] = start.intersection["id"]
                    new_sidewalk["endIntersection"] = end.intersection["id"]

                    sidewalk_count += 1
                    new_sidewalks.append(new_sidewalk)
                    connectors.append(new_sidewalk)
                    roadnet_json["roads"].append(new_sidewalk)

                    startpos = end.position
                    endpos = start.position
                    new_sidewalk = deepcopy(standard_sidewalk)
                    new_sidewalk["id"] = new_sidewalk["id"] + str(sidewalk_count)
                    new_sidewalk["points"][0]["x"] = startpos[0]
                    new_sidewalk["points"][0]["y"] = startpos[1]
                    new_sidewalk["points"][1]["x"] = endpos[0]
                    new_sidewalk["points"][1]["y"] = endpos[1]
                    new_sidewalk["startIntersection"] = end.intersection["id"]
                    new_sidewalk["endIntersection"] = start.intersection["id"]

                    sidewalk_count += 1
                    new_sidewalks.append(new_sidewalk)
                    connectors.append(new_sidewalk)
                    roadnet_json["roads"].append(new_sidewalk)


        all_new_sidewalks = connectors + crosswalks
        for sidewalk_info in all_sidewalk_intersection_info:
            # Add sidewalks as roads for intersection
            incoming = []
            outgoing = []
            sidewalk_intersection = sidewalk_info.intersection
            incoming = [x for x in all_new_sidewalks if x["endIntersection"]==sidewalk_intersection["id"]]
            outgoing = [x for x in all_new_sidewalks if x["startIntersection"]==sidewalk_intersection["id"]]
            sidewalk_intersection["roads"].extend([x["id"] for x in incoming])
            sidewalk_intersection["roads"].extend([x["id"] for x in outgoing])

            # Create roadLinks for sidewalks in this intersection
            incoming_ids = [x["id"] for x in incoming]
            outgoing_ids = [x["id"] for x in outgoing]
            roadLinks = sidewalk_intersection["roadLinks"]
            num_links = 0
            for i in incoming_ids:
                for o in outgoing_ids:
                    new_roadlink = deepcopy(standard_roadlink)
                    new_roadlink["startRoad"] = i
                    new_roadlink["endRoad"] = o
                    roadLinks.append(new_roadlink)
                    num_links += 1
            
            # Default Traffic light stuff
            sidewalk_intersection["trafficLight"]["roadLinkIndices"].extend([x for x in range(num_links)])
            sidewalk_intersection["trafficLight"]["lightphases"].clear()
            sidewalk_intersection["trafficLight"]["lightphases"].append({"time": 5, "availableRoadLinks": [x for x in range(num_links)]})
                


            # # viable_ends = [x for x in all_sidewalk_intersection_info if x.intersection_position == viable_starts[0].c2e]
            # viable_ends = [x for x in all_sidewalk_intersection_info if x.intersection_position == road_endpoint and x.c1e==road_startpoint]
            # # print([x.position for x in viable_ends])
            # count = 0
            # for start, end in zip(viable_starts, viable_ends):
            #     if 2%2==0:
            #         startpos = start.position
            #         endpos = end.position
            #         new_sidewalk = deepcopy(standard_sidewalk)
            #         new_sidewalk["id"] = new_sidewalk["id"] + str(sidewalk_count)
            #         new_sidewalk["points"][0]["x"] = startpos[0]
            #         new_sidewalk["points"][0]["y"] = startpos[1]
            #         new_sidewalk["points"][1]["x"] = endpos[0]
            #         new_sidewalk["points"][1]["y"] = endpos[1]
            #         new_sidewalk["startIntersection"] = start.intersection["id"]
            #         new_sidewalk["endIntersection"] = end.intersection["id"]

            #         sidewalk_count += 1
            #         new_sidewalks.append(new_sidewalk)
            #         roadnet_json["roads"].append(new_sidewalk)
            #     count += 1



            # # Find  road endpoints in sidewalk intersection info
            # # viable_sidewalk_intersections = (x for x in all_sidewalk_intersection_info if x.intersection_position == road_startpoint and x.c2e == road_endpoint)
            # viable_sidewalk_intersections = [x for x in all_sidewalk_intersection_info if x.intersection_position == road_startpoint]
            # print("", road_startpoint, ".....")
            # # print("", [x.position for x in viable_sidewalk_intersections])
            # # print(len(viable_sidewalk_intersections))
            # for sint in viable_sidewalk_intersections:
            #     print("my loc: ", sint.position)
            #     viable_matches = [x for x in all_sidewalk_intersection_info if x.c1e == road_startpoint and x.intersection_position != sint.intersection_position]
            #     print("matches: ", [x.position for x in viable_matches])
            #     # viable_matches = (x for x in viable_sidewalk_intersections if x.c1e == sint.intersection_position)
            #     true_matches = []
            #     for match in viable_matches:
            #         # print(len(viable_matches))
            #         startpos = sint.position
            #         endpos = match.position
            #         true_matches.append((sint, match))

            #     # print([str(x[0].position) + " -> " + str(x[1].intersection_position) for x in true_matches])

            #     for i  in range(len(true_matches)):
            #         startpos = true_matches[i][0].position
            #         endpos = true_matches[i][1].position
            #         new_sidewalk = deepcopy(standard_sidewalk)
            #         new_sidewalk["id"] = new_sidewalk["id"] + str(sidewalk_count)
            #         new_sidewalk["points"][0]["x"] = startpos[0]
            #         new_sidewalk["points"][0]["y"] = startpos[1]
            #         new_sidewalk["points"][1]["x"] = endpos[0]
            #         new_sidewalk["points"][1]["y"] = endpos[1]
            #         new_sidewalk["startIntersection"] = true_matches[i][0].intersection["id"]
            #         new_sidewalk["endIntersection"] = true_matches[i][1].intersection["id"]

            #         sidewalk_count += 1
            #         new_sidewalks.append(new_sidewalk)
            #         roadnet_json["roads"].append(new_sidewalk)

                # min_angle = float('inf')
                # mindx = -1
                # for i in range(len(true_matches)):
                #     a = get_angle(road_startpoint[0],road_startpoint[1],road_endpoint[0],road_endpoint[1],true_matches[i][1].position[0],true_matches[i][1].position[1])
                #     print(abs(math.degrees(a)))
                #     if abs(math.degrees(a)) < min_angle:
                #         mindx = i
                #         min_angle = a

                # if mindx >= 0:
                #     startpos = true_matches[mindx][0].position
                #     endpos = true_matches[mindx][1].position
                #     new_sidewalk = deepcopy(standard_sidewalk)
                #     new_sidewalk["id"] = new_sidewalk["id"] + str(sidewalk_count)
                #     new_sidewalk["points"][0]["x"] = startpos[0]
                #     new_sidewalk["points"][0]["y"] = startpos[1]
                #     new_sidewalk["points"][1]["x"] = endpos[0]
                #     new_sidewalk["points"][1]["y"] = endpos[1]
                #     new_sidewalk["startIntersection"] = true_matches[mindx][0].intersection["id"]
                #     new_sidewalk["endIntersection"] = true_matches[mindx][1].intersection["id"]

                #     sidewalk_count += 1
                #     new_sidewalks.append(new_sidewalk)
                #     roadnet_json["roads"].append(new_sidewalk)

            count += 1
            if (count%20 == 0):
                # print("{}/{} Roads connected.".format(count, roads_to_do))
                print("{}/{} Clumps connected.".format(count, clumps_to_do))


        with open(args.output, "w") as o:
            json.dump(roadnet_json, o, indent=2)
