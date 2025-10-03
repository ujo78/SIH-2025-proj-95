#!/usr/bin/env python3
"""
Panda3D Traffic Flow Visualization Demo

This demo shows the TrafficFlowVisualizer in action with real 3D graphics,
demonstrating traffic density visualization, congestion hotspots, emergency alerts,
and route visualization in a live Panda3D scene.
"""

from indian_features.vehicle_factory import IndianVehicle, BehaviorParameters
from indian_features.mixed_traffic_manager import MixedTrafficManager, CongestionZone
from indian_features.interfaces import Point3D
from indian_features.enums import EmergencyType, VehicleType
from enhanced_visualization.config import VisualizationConfig, UIConfig
from enhanced_visualization.traffic_flow_visualizer import TrafficFlowVisualizer
from direct.interval.IntervalGlobal import Sequence, Parallel, LerpColorInterval, LerpScaleInterval, Wait
from direct.gui.DirectGui import DirectButton, DirectFrame
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    loadPrcFileData, WindowProperties, Vec3, Vec4, Point3,
    DirectionalLight, AmbientLight, CardMaker, PandaNode,
    GeomNode, Geom, GeomVertexFormat, GeomVertexData, GeomVertexWriter,
    GeomTriangles, GeomLines, Material, Texture, TextNode,
    CollisionTraverser, CollisionNode, CollisionSphere, CollisionHandlerQueue
)
import sys
import os
import math
import random
import time
from typing import Dict, List, Any
import networkx as nx

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Panda3D imports

# Project imports


class TrafficVisualizationDemo(ShowBase):
    """
    Interactive Panda3D demo showing traffic flow visualization capabilities
    """

    def __init__(self):
        """Initialize the demo application"""

        # Configure Panda3D
        loadPrcFileData("", "window-title Traffic Flow Visualization Demo")
        loadPrcFileData("", "win-size 1200 800")
        loadPrcFileData("", "show-frame-rate-meter true")
        loadPrcFileData("", "sync-video false")

        # Initialize ShowBase
        ShowBase.__init__(self)

        # Disable default mouse controls
        self.disableMouse()

        # Set up camera
        self.setup_camera()

        # Set up lighting
        self.setup_lighting()

        # Create ground plane
        self.create_ground_plane()

        # Initialize traffic visualization system
        self.setup_traffic_visualization()

        # Create road network
        self.create_road_network()

        # Set up UI
        self.setup_ui()

        # Initialize simulation data
        self.simulation_time = 0.0
        self.traffic_density_cycle = 0.0
        self.demo_phase = 0
        self.phase_timer = 0.0

        # Start the demo
        self.start_demo()

        print("🚗 Traffic Flow Visualization Demo Started!")
        print("📋 Demo Phases:")
        print("   1. Traffic Density Visualization")
        print("   2. Congestion Hotspots")
        print("   3. Emergency Alerts")
        print("   4. Route Alternatives")
        print("   5. Combined Simulation")
        print("\n🎮 Controls:")
        print("   Mouse: Look around")
        print("   Arrow Keys: Move camera")
        print("   Space: Next demo phase")
        print("   Esc: Exit")

    def setup_camera(self):
        """Set up camera position and controls"""
        self.camera.setPos(0, -200, 100)
        self.camera.lookAt(0, 0, 0)

        # Enable camera movement with arrow keys
        self.accept("arrow_left", self.move_camera, ["left"])
        self.accept("arrow_right", self.move_camera, ["right"])
        self.accept("arrow_up", self.move_camera, ["forward"])
        self.accept("arrow_down", self.move_camera, ["backward"])
        self.accept("space", self.next_demo_phase)
        self.accept("escape", sys.exit)

        # Mouse look
        self.accept("mouse1", self.start_mouse_look)
        self.accept("mouse1-up", self.stop_mouse_look)
        self.mouse_look_active = False

    def setup_lighting(self):
        """Set up scene lighting"""
        # Ambient light
        ambient_light = AmbientLight("ambient")
        ambient_light.setColor(Vec4(0.3, 0.3, 0.4, 1))
        ambient_light_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_light_np)

        # Directional light (sun)
        sun_light = DirectionalLight("sun")
        sun_light.setColor(Vec4(0.8, 0.8, 0.7, 1))
        sun_light.setDirection(Vec3(-1, -1, -1))
        sun_light_np = self.render.attachNewNode(sun_light)
        self.render.setLight(sun_light_np)

    def create_ground_plane(self):
        """Create a ground plane for the scene"""
        # Create ground geometry
        cm = CardMaker("ground")
        cm.setFrame(-500, 500, -500, 500)
        ground = self.render.attachNewNode(cm.generate())
        ground.setP(-90)  # Rotate to be horizontal
        ground.setColor(0.2, 0.3, 0.2, 1)  # Dark green

        # Add grid lines
        self.create_grid_lines()

    def create_grid_lines(self):
        """Create grid lines on the ground"""
        # Create grid geometry
        grid_geom = Geom(GeomVertexFormat.getV3())
        vertex_data = GeomVertexData(
            "grid", GeomVertexFormat.getV3(), Geom.UHStatic)

        # Calculate number of grid lines
        grid_size = 50
        grid_extent = 500
        num_lines = (grid_extent * 2) // grid_size + 1

        # 2 lines (x and y) * 2 points each
        vertex_data.setNumRows(num_lines * 4)
        vertex_writer = GeomVertexWriter(vertex_data, "vertex")

        # Create grid lines
        for i in range(num_lines):
            pos = -grid_extent + i * grid_size

            # Vertical lines
            vertex_writer.addData3f(pos, -grid_extent, 0.1)
            vertex_writer.addData3f(pos, grid_extent, 0.1)

            # Horizontal lines
            vertex_writer.addData3f(-grid_extent, pos, 0.1)
            vertex_writer.addData3f(grid_extent, pos, 0.1)

        # Create line primitives
        lines = GeomLines(Geom.UHStatic)
        for i in range(0, num_lines * 4, 2):
            lines.addVertex(i)
            lines.addVertex(i + 1)
        lines.closePrimitive()

        grid_geom.addPrimitive(lines)

        # Create grid node
        grid_node = GeomNode("grid")
        grid_node.addGeom(grid_geom)
        grid_np = self.render.attachNewNode(grid_node)
        grid_np.setColor(0.1, 0.1, 0.1, 0.5)
        grid_np.setTransparency(1)

    def setup_traffic_visualization(self):
        """Initialize the traffic visualization system"""
        # Create configuration
        ui_config = UIConfig()
        self.config = VisualizationConfig(ui_config=ui_config)

        # Create traffic flow visualizer with render root
        self.traffic_visualizer = TrafficFlowVisualizer(
            self.config, self.render)

        # Create mixed traffic manager
        self.traffic_manager = MixedTrafficManager()

        print("✅ Traffic visualization system initialized")

    def create_road_network(self):
        """Create a sample road network for demonstration"""
        self.road_network = nx.Graph()

        # Create a grid-like road network
        grid_size = 4
        spacing = 100

        # Add nodes
        for i in range(grid_size):
            for j in range(grid_size):
                node_id = i * grid_size + j
                x = (i - grid_size/2) * spacing
                y = (j - grid_size/2) * spacing
                self.road_network.add_node(node_id, x=x, y=y, z=0)

        # Add edges (roads)
        for i in range(grid_size):
            for j in range(grid_size):
                node_id = i * grid_size + j

                # Connect to right neighbor
                if i < grid_size - 1:
                    right_neighbor = (i + 1) * grid_size + j
                    self.road_network.add_edge(node_id, right_neighbor)

                # Connect to top neighbor
                if j < grid_size - 1:
                    top_neighbor = i * grid_size + (j + 1)
                    self.road_network.add_edge(node_id, top_neighbor)

        # Initialize traffic overlay
        self.traffic_visualizer.initialize_traffic_overlay(self.road_network)

        # Create visual representation of roads
        self.create_road_visuals()

        print(
            f"✅ Created road network with {len(self.road_network.nodes)} nodes and {len(self.road_network.edges)} edges")

    def create_road_visuals(self):
        """Create visual representation of roads"""
        for u, v in self.road_network.edges():
            u_data = self.road_network.nodes[u]
            v_data = self.road_network.nodes[v]

            # Create road segment
            self.create_road_segment(
                Point3(u_data['x'], u_data['y'], 0.5),
                Point3(v_data['x'], v_data['y'], 0.5)
            )

    def create_road_segment(self, start_pos, end_pos):
        """Create a visual road segment between two points"""
        # Create road geometry
        road_geom = Geom(GeomVertexFormat.getV3())
        vertex_data = GeomVertexData(
            "road", GeomVertexFormat.getV3(), Geom.UHStatic)
        vertex_data.setNumRows(4)
        vertex_writer = GeomVertexWriter(vertex_data, "vertex")

        # Calculate road width
        road_width = 8.0
        direction = end_pos - start_pos
        direction.normalize()
        perpendicular = Vec3(-direction.y, direction.x, 0) * road_width / 2

        # Add vertices for road quad
        vertex_writer.addData3f(*(start_pos - perpendicular))
        vertex_writer.addData3f(*(start_pos + perpendicular))
        vertex_writer.addData3f(*(end_pos + perpendicular))
        vertex_writer.addData3f(*(end_pos - perpendicular))

        # Create triangles
        triangles = GeomTriangles(Geom.UHStatic)
        triangles.addVertex(0)
        triangles.addVertex(1)
        triangles.addVertex(2)
        triangles.closePrimitive()

        triangles.addVertex(0)
        triangles.addVertex(2)
        triangles.addVertex(3)
        triangles.closePrimitive()

        road_geom.addPrimitive(triangles)

        # Create road node
        road_node = GeomNode("road_segment")
        road_node.addGeom(road_geom)
        road_np = self.render.attachNewNode(road_node)
        road_np.setColor(0.3, 0.3, 0.3, 1)  # Dark gray

    def setup_ui(self):
        """Set up user interface"""
        # Title
        self.title_text = OnscreenText(
            text="Traffic Flow Visualization Demo",
            pos=(0, 0.9),
            scale=0.08,
            fg=(1, 1, 1, 1),
            shadow=(0, 0, 0, 0.5)
        )

        # Phase indicator
        self.phase_text = OnscreenText(
            text="Phase 1: Traffic Density Visualization",
            pos=(-1.3, 0.8),
            scale=0.05,
            fg=(1, 1, 0, 1),
            align=0  # Left align
        )

        # Instructions
        self.instructions_text = OnscreenText(
            text="Space: Next Phase | Arrow Keys: Move Camera | Mouse: Look Around",
            pos=(0, -0.9),
            scale=0.04,
            fg=(0.8, 0.8, 0.8, 1)
        )

        # Statistics display
        self.stats_text = OnscreenText(
            text="",
            pos=(-1.3, 0.7),
            scale=0.04,
            fg=(0.8, 1, 0.8, 1),
            align=0  # Left align
        )

    def start_demo(self):
        """Start the demonstration"""
        # Start update task
        self.taskMgr.add(self.update_demo, "update_demo")

        # Start with first phase
        self.demo_phase = 1
        self.phase_timer = 0.0
        self.start_phase_1()

    def update_demo(self, task):
        """Main demo update loop"""
        dt = globalClock.getDt()
        self.simulation_time += dt
        self.phase_timer += dt

        # Update current phase
        if self.demo_phase == 1:
            self.update_phase_1(dt)
        elif self.demo_phase == 2:
            self.update_phase_2(dt)
        elif self.demo_phase == 3:
            self.update_phase_3(dt)
        elif self.demo_phase == 4:
            self.update_phase_4(dt)
        elif self.demo_phase == 5:
            self.update_phase_5(dt)

        # Update statistics
        self.update_statistics()

        return task.cont

    def start_phase_1(self):
        """Phase 1: Traffic Density Visualization"""
        self.phase_text.setText("Phase 1: Traffic Density Visualization")
        print("🚦 Starting Phase 1: Traffic Density Visualization")

        # Clear previous visualizations
        self.traffic_visualizer._clear_congestion_hotspots()
        self.traffic_visualizer._clear_emergency_alerts()
        self.traffic_visualizer._clear_route_visualizations()

    def update_phase_1(self, dt):
        """Update Phase 1: Animate traffic density changes"""
        # Create cycling traffic density
        self.traffic_density_cycle += dt * 0.5  # Slow cycle

        edge_densities = {}
        for i, edge in enumerate(self.road_network.edges()):
            # Create wave-like density pattern
            wave_offset = i * 0.5
            density = (
                math.sin(self.traffic_density_cycle + wave_offset) + 1) / 2
            density = max(0.0, min(1.0, density))
            edge_densities[edge] = density

        self.traffic_visualizer.update_traffic_density(edge_densities)

        # Auto-advance after 10 seconds
        if self.phase_timer > 10.0:
            self.next_demo_phase()

    def start_phase_2(self):
        """Phase 2: Congestion Hotspots"""
        self.phase_text.setText("Phase 2: Congestion Hotspots")
        print("🔥 Starting Phase 2: Congestion Hotspots")

        # Create some congestion hotspots
        hotspots = [
            {
                'id': 'hotspot_1',
                'x': -50,
                'y': 50,
                'z': 0,
                'radius': 40.0,
                'intensity': 0.9,
                'affected_edges': []
            },
            {
                'id': 'hotspot_2',
                'x': 100,
                'y': -100,
                'z': 0,
                'radius': 30.0,
                'intensity': 0.7,
                'affected_edges': []
            }
        ]

        self.traffic_visualizer.show_congestion_hotspots(hotspots)

    def update_phase_2(self, dt):
        """Update Phase 2: Animate hotspot intensities"""
        # Keep updating traffic density
        self.update_phase_1(dt)

        # Auto-advance after 8 seconds
        if self.phase_timer > 8.0:
            self.next_demo_phase()

    def start_phase_3(self):
        """Phase 3: Emergency Alerts"""
        self.phase_text.setText("Phase 3: Emergency Alerts")
        print("🚨 Starting Phase 3: Emergency Alerts")

        # Create emergency alerts
        emergencies = [
            {
                'id': 'accident_1',
                'type': EmergencyType.ACCIDENT,
                'x': 0,
                'y': 0,
                'z': 0,
                'severity': 0.8,
                'affected_area': []
            },
            {
                'id': 'construction_1',
                'type': EmergencyType.CONSTRUCTION,
                'x': -150,
                'y': 150,
                'z': 0,
                'severity': 0.6,
                'affected_area': []
            }
        ]

        self.traffic_visualizer.display_emergency_alerts(emergencies)

    def update_phase_3(self, dt):
        """Update Phase 3: Show emergency alerts with traffic"""
        # Keep updating traffic density
        self.update_phase_1(dt)

        # Auto-advance after 8 seconds
        if self.phase_timer > 8.0:
            self.next_demo_phase()

    def start_phase_4(self):
        """Phase 4: Route Alternatives"""
        self.phase_text.setText("Phase 4: Route Alternatives")
        print("🛣️ Starting Phase 4: Route Alternatives")

        # Show route alternatives
        original_route = [0, 1, 5, 9, 13]  # Path through network
        alternatives = [
            [0, 4, 8, 12, 13],  # Alternative path 1
            [0, 1, 2, 6, 10, 14, 13]  # Alternative path 2
        ]

        self.traffic_visualizer.show_route_alternatives(
            original_route, alternatives)

    def update_phase_4(self, dt):
        """Update Phase 4: Show routes with traffic"""
        # Keep updating traffic density
        self.update_phase_1(dt)

        # Auto-advance after 8 seconds
        if self.phase_timer > 8.0:
            self.next_demo_phase()

    def start_phase_5(self):
        """Phase 5: Combined Simulation"""
        self.phase_text.setText("Phase 5: Combined Simulation")
        print("🌟 Starting Phase 5: Combined Simulation")

        # Create traffic flow animation
        flow_data = {
            'animation_speed': 1.0,
            'particle_count': 5
        }
        self.traffic_visualizer.create_traffic_flow_animation(flow_data)

        # Add performance indicators
        metrics = {
            'fps': 60.0,
            'vehicles': 150,
            'congestion_level': 0.4,
            'emergency_count': 2
        }
        self.traffic_visualizer.add_performance_indicators(metrics)

    def update_phase_5(self, dt):
        """Update Phase 5: Full simulation"""
        # Keep all previous elements active
        self.update_phase_1(dt)

        # Update performance metrics
        metrics = {
            'fps': 60.0 + random.uniform(-5, 5),
            'vehicles': 150 + int(random.uniform(-20, 20)),
            'congestion_level': 0.4 + random.uniform(-0.2, 0.3),
            'emergency_count': 2
        }
        self.traffic_visualizer.add_performance_indicators(metrics)

    def next_demo_phase(self):
        """Advance to next demo phase"""
        self.demo_phase += 1
        self.phase_timer = 0.0

        if self.demo_phase == 2:
            self.start_phase_2()
        elif self.demo_phase == 3:
            self.start_phase_3()
        elif self.demo_phase == 4:
            self.start_phase_4()
        elif self.demo_phase == 5:
            self.start_phase_5()
        elif self.demo_phase > 5:
            # Restart from phase 1
            self.demo_phase = 1
            self.start_phase_1()

    def update_statistics(self):
        """Update statistics display"""
        stats = f"""Simulation Time: {self.simulation_time:.1f}s
Phase Timer: {self.phase_timer:.1f}s
Road Network: {len(self.road_network.nodes)} nodes, {len(self.road_network.edges)} edges
Active Hotspots: {len(self.traffic_visualizer.congestion_hotspots)}
Emergency Alerts: {len(self.traffic_visualizer.emergency_alerts)}
Route Visualizations: {len(self.traffic_visualizer.route_visualizations)}"""

        self.stats_text.setText(stats)

    def move_camera(self, direction):
        """Move camera based on input"""
        speed = 10.0

        if direction == "left":
            self.camera.setX(self.camera.getX() - speed)
        elif direction == "right":
            self.camera.setX(self.camera.getX() + speed)
        elif direction == "forward":
            self.camera.setY(self.camera.getY() + speed)
        elif direction == "backward":
            self.camera.setY(self.camera.getY() - speed)

    def start_mouse_look(self):
        """Start mouse look mode"""
        self.mouse_look_active = True
        props = WindowProperties()
        props.setCursorHidden(True)
        self.win.requestProperties(props)

    def stop_mouse_look(self):
        """Stop mouse look mode"""
        self.mouse_look_active = False
        props = WindowProperties()
        props.setCursorHidden(False)
        self.win.requestProperties(props)


def main():
    """Main function to run the demo"""
    print("🚀 Starting Traffic Flow Visualization Demo...")
    print("📦 Initializing Panda3D...")

    try:
        # Create and run the demo
        demo = TrafficVisualizationDemo()
        demo.run()

    except Exception as e:
        print(f"❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
