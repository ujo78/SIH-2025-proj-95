import random
from typing import List, Tuple, Iterable

import osmnx as ox
import networkx as nx
from shapely.geometry import LineString, MultiLineString, GeometryCollection
import folium
import simpy

from helpers import *

ox.settings.use_cache = True


CENTER_LAT = 20.2590372
CENTER_LON = 85.79181
CENTER = (CENTER_LAT, CENTER_LON)

G = ox.graph_from_point(CENTER, dist=2000, network_type="drive", simplify=True)
G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

Gp = ox.projection.project_graph(G)

def random_far_nodes(G, min_path_seconds=60.0, max_tries=200) -> Tuple[int, int, List[int]]:
    nodes = list(G.nodes)
    for _ in range(max_tries):
        orig = random.choice(nodes)
        dest = random.choice(nodes)
        if orig == dest:
            continue
        try:
            path = nx.shortest_path(G, orig, dest, weight="travel_time")
            tt_list = route_edge_values(G, path, "travel_time", default=0.0)
            if sum(v or 0.0 for v in tt_list) >= min_path_seconds:
                return orig, dest, path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue
    for _ in range(max_tries):
        orig = random.choice(nodes)
        dest = random.choice(nodes)
        if orig == dest:
            continue
        try:
            path = nx.shortest_path(G, orig, dest, weight="travel_time")
            return orig, dest, path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            continue
    raise RuntimeError("Could not find a valid path")
