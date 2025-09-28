from panda3d.core import LineSegs, NodePath, Vec3, AmbientLight, DirectionalLight, Vec4, CardMaker
from direct.showbase.ShowBase import ShowBase
import sys
# simulate_india_traffic_iter_popup.py
import random
from typing import List, Tuple, Iterable

import osmnx as ox
import networkx as nx
from shapely.geometry import LineString, MultiLineString, GeometryCollection
import folium
import simpy

from helpers import *
from routers import *
from traffic_model import *



ox.settings.use_cache = True


CENTER_LAT = 20.2590372
CENTER_LON = 85.79181
CENTER = (CENTER_LAT, CENTER_LON)

# Compact drivable network around ITER to keep it snappy
G = ox.graph_from_point(CENTER, dist=2000, network_type="drive", simplify=True)
G = ox.add_edge_speeds(G)
G = ox.add_edge_travel_times(G)

Gp = ox.projection.project_graph(G)


model = TrafficModel(G, max_vehicles=14, spawn_rate_per_s=1/18.0, sim_seconds=240)
from panda3d.core import ClockObject
globalClock = ClockObject.getGlobalClock()


# Assume you have these from your simulation code
# Gp - projected graph with 2D (x, y) coords in meters
# model.routes[vid] - list of node IDs for vehicle vid
# Functions: route_geoms_projected, concat_lines (from previous code)

class Traffic3DApp(ShowBase):
    def __init__(self, Gp, model):
        super().__init__()
        self.Gp = Gp
        self.model = model
        self.disableMouse()  # Disable default mouse-based camera control

        # Set camera position and orientation to view the scene properly
        self.camera.setPos(0, -100, 60)
        self.camera.lookAt(0, 0, 0)

        # Setup ambient light to light whole scene softly
        ambient_light = AmbientLight('ambient')
        ambient_light.setColor(Vec4(0.6, 0.6, 0.6, 1))
        ambient_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_np)

        # Setup directional light to simulate sunlight
        directional_light = DirectionalLight('directional')
        directional_light.setDirection(Vec3(-5, -5, -5))
        directional_light.setColor(Vec4(0.8, 0.8, 0.8, 1))
        directional_np = self.render.attachNewNode(directional_light)
        self.render.setLight(directional_np)

        # Draw roads with the LineSegs utility
        self.draw_roads()

        # Add a simple test quad to verify visibility (red square)
        cm = CardMaker("test_quad")
        cm.setFrame(-10, 10, -10, 10)
        test_np = NodePath(cm.generate())
        test_np.setPos(0, 0, 0)
        test_np.setColor(1, 0, 0, 1)  # Red color
        test_np.reparentTo(self.render)

        # Create vehicle nodes for simulation routes
        self.vehicle_nodes = []
        for vid, path in self.model.routes.items():
            pts_3d = self.get_route_3d_points(path)
            vehicle_np = self.create_vehicle(vid)
            vehicle_np.reparentTo(self.render)
            vehicle_np.setPos(*pts_3d[0])
            self.vehicle_nodes.append((vehicle_np, pts_3d, 0, vid)) 

        # Add update task to move vehicles along their route
        self.taskMgr.add(self.update_vehicles, "update-vehicles")

    def draw_roads(self):
        for vid, path in self.model.routes.items():
            segs = route_geoms_projected(self.Gp, path)
            line = LineSegs()
            line.setThickness(3)
            line.setColor(0.7, 0.7, 0.7, 1)
            for seg in segs:
                coords = list(seg.coords)
                for i in range(len(coords)-1):
                    x1, y1 = coords[i]
                    x2, y2 = coords[i+1]
                    line.moveTo(x1, y1, 0)
                    line.drawTo(x2, y2, 0)
            node = line.create()
            NodePath(node).reparentTo(self.render)

    def get_route_3d_points(self, path):
        segs = route_geoms_projected(self.Gp, path)
        line = concat_lines(segs)
        coords_2d = list(line.coords)
        # Add elevation 0 to create 3D points
        return [(x, y, 0) for x, y in coords_2d]

    def create_vehicle(self, vid):
        cm = CardMaker(f"vehicle_{vid}")
        cm.setFrame(-1, 1, -0.5, 0.5)
        np = NodePath(cm.generate())
        colors = [(1,0,0,1), (0,1,0,1), (0,0,1,1), (1,1,0,1), (1,0,1,1), (0,1,1,1)]
        color = colors[vid % len(colors)]
        np.setColor(*color)
        return np

    def update_vehicles(self, task):
        speed = 20.0  # meters/second
        dt = globalClock.getDt()
        for idx, (vehicle_np, pts, pos_idx, vid) in enumerate(self.vehicle_nodes):
            if pos_idx >= len(pts)-1:
                continue  # Finished this vehicle's route
            p1 = pts[pos_idx]
            p2 = pts[min(pos_idx+1, len(pts)-1)]
            vec = (p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2])
            dist = (vec[0]**2 + vec[1]**2 + vec[2]**2)**0.5
            travel_dist = speed * dt
            if travel_dist >= dist:
                vehicle_np.setPos(*p2)
                self.vehicle_nodes[idx] = (vehicle_np, pts, pos_idx+1, vid)
            else:
                frac = travel_dist / dist
                x = p1[0] + vec[0]*frac
                y = p1[1] + vec[1]*frac
                z = p1[2] + vec[2]*frac
                vehicle_np.setPos(x, y, z)
        return task.cont

# Usage (replace your main simulation run and visualization with this):
# After finishing your current simulation run and model.routes generated:

app = Traffic3DApp(Gp, model)
app.run()