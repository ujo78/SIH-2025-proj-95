import random
from typing import List, Tuple, Iterable

import osmnx as ox
import networkx as nx
from shapely.geometry import LineString, MultiLineString, GeometryCollection
import folium
import simpy

from helpers import *
from routers import *

class TrafficModel:
    def __init__(self, G, max_vehicles=14, spawn_rate_per_s=1/18.0, sim_seconds=240):
        self.G = G
        self.env = simpy.Environment()
        self.max_vehicles = max_vehicles
        self.spawn_rate = spawn_rate_per_s
        self.sim_seconds = sim_seconds
        self.routes = {}       # vid -> path (list of node IDs)
        self.start_nodes = {}  # vid -> start node id
        self.end_nodes = {}    # vid -> end node id

    def drive(self, vid: int, path: List[int]):
        tt_list = route_edge_values(self.G, path, "travel_time", default=4.0)
        for travel_t in tt_list:
            travel_t = max(0.05, float(travel_t or 4.0))
            yield self.env.timeout(travel_t)

    def vehicle_source(self):
        vid = 0
        created = 0
        while created < self.max_vehicles:
            orig, dest, path = random_far_nodes(self.G, min_path_seconds=45.0)
            path = normalize_route(path)  # ensure flat list [n0, n1, ...]
            self.routes[vid] = path
            self.start_nodes[vid] = path  # store single node IDs
            self.end_nodes[vid] = path[-1]
            self.env.process(self.drive(vid, path))
            created += 1
            vid += 1
            inter_arrival = random.expovariate(self.spawn_rate)
            yield self.env.timeout(inter_arrival)

    def run(self):
        random.seed(42)
        self.env.process(self.vehicle_source())
        self.env.run(until=self.sim_seconds)