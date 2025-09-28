import random
from typing import List, Tuple, Iterable

import osmnx as ox
import networkx as nx
from shapely.geometry import LineString, MultiLineString, GeometryCollection
import folium
import simpy

ox.settings.use_cache = True

CENTER_LAT = 20.2590372
CENTER_LON = 85.79181
CENTER = (CENTER_LAT, CENTER_LON)

G = ox.graph_from_point(CENTER, dist=2000, network_type="drive", simplify=True)
G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

Gp = ox.projection.project_graph(G)

def select_edge_data(G, u, v, prefer_attr="travel_time"):
    data_dict = G.get_edge_data(u, v)
    if not data_dict:
        return None
    best_key = None
    best_val = None
    for k, d in data_dict.items():
        val = d.get(prefer_attr, None)
        if isinstance(val, (int, float)):
            if best_val is None or val < best_val:
                best_key, best_val = k, val
    if best_key is None:
        k = next(iter(data_dict.keys()))
        return data_dict[k]
    return data_dict[best_key]

def normalize_route(path):
    # If nested like [[n1, n2, ...]], flatten one level
    if isinstance(path, (list, tuple)) and path and isinstance(path, (list, tuple)):
        flat = []
        for part in path:
            flat.extend(part if isinstance(part, (list, tuple)) else [part])
        path = flat
    return list(path)


def route_edge_values(G, path: List[int], attr: str, default=None):
    vals = []
    for u, v in zip(path[:-1], path[1:]):
        d = select_edge_data(G, u, v, prefer_attr=attr)
        vals.append(d.get(attr, default) if d else default)
    return vals

def route_geoms_projected(Gp, path: List[int]) -> List[LineString]:
    """Get route segment geometries from the projected graph (meters); build straight lines if missing."""
    geoms = []
    for u, v in zip(path[:-1], path[1:]):
        d = select_edge_data(Gp, u, v, prefer_attr="travel_time")
        geom = d.get("geometry") if d else None
        if geom is None:
            ux, uy = Gp.nodes[u]["x"], Gp.nodes[u]["y"]
            vx, vy = Gp.nodes[v]["x"], Gp.nodes[v]["y"]
            geom = LineString([(ux, uy), (vx, vy)])
        geoms.append(geom)
    return geoms

def concat_lines(segments: Iterable[LineString]) -> LineString:
    """Concatenate ordered segments into a single LineString."""
    coords = []
    for i, seg in enumerate(segments):
        pts = list(seg.coords)
        if i > 0 and coords and pts and coords[-1] == pts:
            coords.extend(pts[1:])
        else:
            coords.extend(pts)
    return LineString(coords)

def offset_route_linestring(ls_m: LineString, offset_m: float, side: str = "left") -> LineString:
    """Offset a route in meters to reduce visual overlap."""
    try:
        return ls_m.parallel_offset(abs(offset_m), side=side, join_style=2)
    except Exception:
        return ls_m

def to_latlon(geom_m):
    """Project geometry from Gp CRS back to lat/lon."""
    geom_ll, _ = ox.projection.project_geometry(geom_m, crs=Gp.graph["crs"], to_latlong=True)
    return geom_ll

def node_latlon(G, n):
    # Defensive: If n is a list or tuple, use its first element.
    if isinstance(n, (list, tuple)):
        n = n[0]
    return (G.nodes[n]["y"], G.nodes[n]["x"])

def simplify_linestring_deg_latlon(ls, tol=1e-5):
    return ls.simplify(tol, preserve_topology=False)

def iter_lines_latlon(geom_ll):
    """
    Yield lists of (lat, lon) for each LineString segment found in geom_ll.
    Handles LineString, MultiLineString, and GeometryCollection.
    """
    if isinstance(geom_ll, LineString):
        yield [(lat, lon) for lon, lat in geom_ll.coords]
    elif isinstance(geom_ll, MultiLineString):
        for part in geom_ll.geoms:
            yield [(lat, lon) for lon, lat in part.coords]
    elif isinstance(geom_ll, GeometryCollection):
        for part in geom_ll.geoms:
            if isinstance(part, LineString):
                yield [(lat, lon) for lon, lat in part.coords]

def flatten_route_if_nested(path):
    """If a route is nested like [[n1, n2, ...]], flatten it to [n1, n2, ...]."""
    if isinstance(path, (list, tuple)) and len(path) > 0 and isinstance(path, (list, tuple)):
        # Only flatten if the first inner element looks like a node id
        inner = path
        if len(inner) > 0 and isinstance(inner, (int, str)):
            return list(inner)
    return path

