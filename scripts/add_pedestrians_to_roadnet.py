
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

split_idx = 0

standard_lightphase = {
    "time": -1,
    "availableRoadLinks": []
}

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

# t should be between 0 and 1 (inclusive)
def lerp(start_num, end_num, t):
    return (t * (end_num-start_num)) + start_num

def get_road_connection_points(intersection, start, end, num_points):
    start_vec = (start["points"][0]["x"]-start["points"][1]["x"], start["points"][0]["y"]-start["points"][1]["y"])
    end_vec = (end["points"][1]["x"]-end["points"][0]["x"], end["points"][1]["y"]-end["points"][0]["y"])
    ipt = (intersection["point"]["x"], intersection["point"]["y"])
    # Get the 2 points that are in direction of each lane (going away from intersection) by intersection width
    start_direction = math.atan2(start_vec[1], start_vec[0])
    end_direction = math.atan2(end_vec[1], end_vec[0])
    start_point = (ipt[0] + intersection["width"]*math.cos(start_direction), ipt[1] + intersection["width"]*math.sin(start_direction))
    end_point = (ipt[0] + intersection["width"]*math.cos(end_direction), ipt[1] + intersection["width"]*math.sin(end_direction))
    # Just linearly interpolate between start and end by num_points
    points = []
    for i in range(num_points):
        points.append({
            "x": lerp(start_point[0], end_point[0], float(i)/num_points),
            "y": lerp(start_point[1], end_point[1], float(i)/num_points)
        })
    
    return points

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

class Crosswalk:
    def __init__(self, swi1, swi2, ri1, ri2, crossing_clump, sw1, sw2, main_intersection):
        self.swi1 = swi1
        self.swi2 = swi2
        self.ri1 = ri1
        self.ri2 = ri2
        self.crossing_clump = crossing_clump
        self.sw1 = sw1
        self.sw2 = sw2
        self.main_intersection = main_intersection

    def __str__(self) -> str:
        s = ""
        s += "Crosswalk:\n"
        s += "\tSidewalk Crossings: {}, {}\n".format(self.swi1["id"], self.swi2["id"])
        s += "\tRoad Intersections: {}, {}".format(self.ri1["id"], self.ri2["id"])
        return s

    # After 1 road has been split on a crosswalk, 
    # this should alter the endpoint of other crosswalks that have not been created/split roads.
    # So, this helps us find and replace old road intersections with the new crosswalk intersections.
    def update_intersection(self, old_id, new_intersection):
        if (self.ri1["id"] == old_id):
            self.ri1 = new_intersection
        if (self.ri2["id"] == old_id):
            self.ri2 = new_intersection
        if (self.swi1["id"] == old_id):
            self.swi1 = new_intersection
        if (self.swi2["id"] == old_id):
            self.swi2 = new_intersection

    # Detects if 
    def correct_incoming_roads_from(self, other_crosswalk, old_road_id_to_new_road_split):
        # if self.does_share_clump(other_crosswalk):
        # for road in self.crossing_clump:
        #     if road[""]
        print(self.main_intersection["id"])
        print("\tOld clump roads: {}".format([r["id"] for r in self.crossing_clump]))
        self.crossing_clump = [r if r["id"] not in old_road_id_to_new_road_split else old_road_id_to_new_road_split[r["id"]] for r in self.crossing_clump]
        print("\tNew clump roads: {}".format([r["id"] for r in self.crossing_clump]))

    # Just returns midpoint of 2 sidewalk intersections
    def intersect_position(self):
        return ((self.swi1["point"]["x"] + self.swi2["point"]["x"]) / 2, (self.swi1["point"]["y"] + self.swi2["point"]["y"]) / 2)

    def does_share_clump(self, other) -> bool:
        my_ids = [x["id"] for x in self.crossing_clump]
        other_ids = [x["id"] for x in other.crossing_clump]
        return set(my_ids) == set(other_ids)

    def get_intersections_of_road(self, road):
        start_intersection = None
        end_intersection = None
        # print(str(self))
        # print("Road start intersection: {}".format(road["startIntersection"]))
        # print("Road end intersection: {}".format(road["endIntersection"]))
        if road["startIntersection"] == self.swi1["id"]:
            start_intersection = self.swi1
        elif road["startIntersection"] == self.swi2["id"]:
            start_intersection = self.swi2
        elif road["startIntersection"] == self.ri1["id"]:
            start_intersection = self.ri1
        elif road["startIntersection"] == self.ri2["id"]:
            start_intersection = self.ri2
        # else:
        #     for r in self.crossing_clump:
        #         if road["startIntersection"] == r["id"]:
        #             start_intersection = r
        #             break
        if road["endIntersection"] == self.swi1["id"]:
            end_intersection = self.swi1
        elif road["endIntersection"] == self.swi2["id"]:
            end_intersection = self.swi2
        elif road["endIntersection"] == self.ri1["id"]:
            end_intersection = self.ri1
        elif road["endIntersection"] == self.ri2["id"]:
            end_intersection = self.ri2
        # else:
        #     for r in self.crossing_clump:
        #         if road["endIntersection"] == r["id"]:
        #             end_intersection = r
        #             break

        # print((start_intersection, end_intersection))
        return (start_intersection, end_intersection)


class RoadSplitter:
    def __init__(self, split_intersection, crosswalk):
        # self.road = road
        self.crosswalk = crosswalk
        self.split_intersection = split_intersection
        self.road_splits = []
        self.outgoing_road_id_to_new_road_split = {}
        # self.create_split()

    def num_lanes(self):
        lanes = 0
        for r in self.crosswalk.crossing_clump:
            lanes += 2*len(r["lanes"])
        lanes += len(self.crosswalk.sw1["lanes"])
        lanes += len(self.crosswalk.sw2["lanes"])
        return lanes

    def split(self):
        to_split = [self.crosswalk.sw1, self.crosswalk.sw2, *self.crosswalk.crossing_clump]
        # to_split = [x for x in to_split if self.crosswalk.main_intersection["id"] == x["startIntersection"]]
        # print(len(to_split))
        c = 0
        for r in to_split:
            self.split_road(r)
            c += 1
            # print("Split road {} ({}/{}) at crosswalk {}".format(r["id"], c, len(to_split), self.crosswalk))

        # Create traffic lights
        num_lanes = self.num_lanes()
        # self.split_intersection["trafficLight"]["roadLinkIndices"] = [i for i in range(num_lanes)]
        self.split_intersection["trafficLight"]["roadLinkIndices"] = [i for i in range(4)]
        self.split_intersection["trafficLight"]["lightphases"] = []
        # First 4 lanes should be the sidewalk lanes
        phase = deepcopy(standard_lightphase)
        phase["time"] = 30
        phase["availableRoadLinks"].extend([i for i in range(2)])
        self.split_intersection["trafficLight"]["lightphases"].append(phase)
        # The rest of the phases are the road lanes
        phase = deepcopy(standard_lightphase)
        phase["time"] = 30
        phase["availableRoadLinks"].extend([i for i in range(2, 4)])
        self.split_intersection["trafficLight"]["lightphases"].append(phase)

    def add_road_splits_to_roads(self, roads):
        roads.extend(self.road_splits)

    def split_road(self, road):
        start_intersection, end_intersection = self.crosswalk.get_intersections_of_road(road)
        # print(road)
        # print(start_intersection["id"])
        # print(end_intersection["id"])
        # if (start_intersection == None or end_intersection == None):
        #     print("------------- DUMP CROSSWALK INFO --------------")
        #     print("SWI1: {}\n".format(self.crosswalk.swi1))
        #     print("SWI2: {}\n".format(self.crosswalk.swi2))
        #     print("RI1: {}\n".format(self.crosswalk.ri1))
        #     print("RI2: {}\n".format(self.crosswalk.ri2))

        road_split = deepcopy(road)
        self.road_splits.append(road_split)
        old_id = road_split["id"]
        global split_idx
        road_split["id"] = road_split["id"] + "_split" + str(split_idx)
        split_idx += 1
        # Change the sidewalk intersection road IDs to match the new road
        # Roads for start_intersection do not change (because the start road id does not change)
        # Road IDs for end_intersection must be updated to this new split that replaces the old road id
        # end_intersection["roads"] = [s.replace(old_id, road_split["id"]) for s in end_intersection["roads"]]
        end_intersection["roads"] = [s if old_id != s else road_split["id"] for s in end_intersection["roads"]]
        # print("Updated end intersection {} road {} to new split road {}".format(end_intersection["id"], old_id, road_split["id"]))
        for link in end_intersection["roadLinks"]:
            # link["startRoad"] = link["startRoad"].replace(old_id, road_split["id"])
            # link["endRoad"] = link["endRoad"].replace(old_id, road_split["id"])
            link["startRoad"] = link["startRoad"] if link["startRoad"] != old_id else road_split["id"]
            link["endRoad"] = link["endRoad"] if link["endRoad"] != old_id else road_split["id"]
        # Change the end intersection of original road to be the split intersection
        road["points"][1]["x"] = self.split_intersection["point"]["x"]
        road["points"][1]["y"] = self.split_intersection["point"]["y"]
        road["endIntersection"] = self.split_intersection["id"]
        # Change the start intersection of original road to be the split intersection
        road_split["points"][0]["x"] = self.split_intersection["point"]["x"]
        road_split["points"][0]["y"] = self.split_intersection["point"]["y"]
        road_split["startIntersection"] = self.split_intersection["id"]
        # if (road["id"] == "road_1_1_1"):
        #     print(road)
        #     print(road_split)
        # Modify split intersection to just "go straight" between these two roads
        new_roadlink = deepcopy(standard_roadlink)
        new_roadlink["type"] = "go_straight"
        new_roadlink["startRoad"] = road["id"]
        new_roadlink["endRoad"] = road_split["id"]
        # default_points = new_roadlink["laneLinks"][0]["points"]
        default_points = get_road_connection_points(self.split_intersection, road, road_split, 6)
        new_roadlink["laneLinks"].clear()
        for lane_idx in range(len(road["lanes"])):
            for l in range(len(road["lanes"])):
                # new_roadlink["laneLinks"].append({"startLaneIndex": 1, "endLaneIndex": 0, "points": default_points})
                new_roadlink["laneLinks"].append({"startLaneIndex": lane_idx, "endLaneIndex": l, "points": default_points})

        # THE NEW ROAD IS ALWAYS THE ONE THAT GOES OUT FROM THE CROSSWALK'S MAIN INTERSECTION
        # THEREFORE: KEEP TRACK OF WHICH OUTGOING ROADS TO UPDATE FOR LATER
        if self.crosswalk.main_intersection["id"] != end_intersection["id"]:
            self.outgoing_road_id_to_new_road_split[old_id] = road_split

        self.split_intersection["roads"].append(road["id"])
        self.split_intersection["roads"].append(road_split["id"])
        self.split_intersection["roadLinks"].append(new_roadlink)



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
        crosswalk_objects = []
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
                # offset = 22
                offset = 54
                # offset = 100
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

            # Make new crosswalks at intersections
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
                sw1 = new_sidewalk
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
                new_sidewalk["startIntersection"] = new_sidewalk_intersections[adjacent_idx]["id"]
                new_sidewalk["endIntersection"] = new_sidewalk_intersections[i]["id"]

                sidewalk_count += 1
                sw2 = new_sidewalk
                new_sidewalks.append(new_sidewalk)
                crosswalks.append(new_sidewalk)
                roadnet_json["roads"].append(new_sidewalk)

                crosswalk_objects.append(Crosswalk(new_sidewalk_intersections[i], new_sidewalk_intersections[adjacent_idx], intersections_dict[clump_intersect_points[adjacent_idx][5][0]["startIntersection"]], intersections_dict[clump_intersect_points[adjacent_idx][5][0]["endIntersection"]], clump_intersect_points[adjacent_idx][5], sw1, sw2, intersection))

            
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
        all_new_sidewalks_dict = {s["id"]: s for s in all_new_sidewalks}
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
                    new_roadlink["laneLinks"][0]["points"].clear()
                    new_roadlink["laneLinks"][0]["points"] = get_road_connection_points(sidewalk_intersection, all_new_sidewalks_dict[i], all_new_sidewalks_dict[o], 6)
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

        crosswalk_intersections = []
        to_update = [x for x in crosswalk_objects]
        # Create crosswalk intersections that force interaction between roads and sidewalks
        print("# Crosswalks: {}".format(len(crosswalk_objects)))
        for crosswalk in crosswalk_objects:
            # For each sidewalk, create a new intersection at the point where the clump and crosswalk meet
            # The only kind of turn here should be "go_straight" to prevent cars from turning on sidewalks and pedestrians from turning on roads
            position = crosswalk.intersect_position()
            
            crosswalk_intersection = deepcopy(standard_sidewalk_intersection)
            crosswalk_intersection["id"] = crosswalk_intersection["id"] + str(sidewalk_intersection_count) + "_crosswalk"
            crosswalk_intersection["point"]["x"] = position[0]
            crosswalk_intersection["point"]["y"] = position[1]
            crosswalk_intersection["sidewalk"] = False

            splitter = RoadSplitter(crosswalk_intersection, crosswalk)
            splitter.split()
            splitter.add_road_splits_to_roads(roadnet_json["roads"])

            print(crosswalk.main_intersection["id"])
            print({r: splitter.outgoing_road_id_to_new_road_split[r]["id"] for r in splitter.outgoing_road_id_to_new_road_split})

            # Update some intersection of neighboring crosswalks with newly created crosswalk intersection if need be
            to_update.remove(crosswalk)
            # associated_crosswalk is the crosswalk down near the other intersection
            associated_crosswalks = [x for x in to_update if crosswalk.does_share_clump(x)]
            for c in associated_crosswalks:
                # main_intersection refers to the road intersection around which the crosswalk was placed
                # Use this to update the other crosswalks that used this main_intersection as an endpoint
                # with the newly created crosswalk intersection
                c.update_intersection(crosswalk.main_intersection["id"], crosswalk_intersection)
                # If the updated road(s) is outgoing, then we need to replace the road in the clump with the
                # newly created split road for relevant associated crosswalks
                c.correct_incoming_roads_from(crosswalk, splitter.outgoing_road_id_to_new_road_split)


            # # With the new crosswalk intersection, we need to split the existing roads
            # sw1split = deepcopy(crosswalk.sw1)
            # sw2split = deepcopy(crosswalk.sw2)

            # # Add all relevant road IDs to intersection's roads
            # crosswalk_intersection["roads"].append(crosswalk.sw1)
            # crosswalk_intersection["roads"].append(crosswalk.sw2)
            # for road in crosswalk.crossing_clump:
            #     crosswalk_intersection["roads"].append(road["id"])

            


            sidewalk_intersection_count += 1
            crosswalk_intersections.append(crosswalk_intersection)
            intersections.append(crosswalk_intersection)



        with open(args.output, "w") as o:
            json.dump(roadnet_json, o, indent=2)
