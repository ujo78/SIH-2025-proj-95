#!/usr/bin/env python3
"""
Indian Traffic Digital Twin - Full Visualization Demo

This demo shows the TrafficFlowVisualizer in action with real Panda3D graphics,
including traffic density visualization, congestion hotspots, emergency alerts,
and animated traffic flow.
"""

from indian_features.vehicle_factory import IndianVehicle, BehaviorParameters
from indian_features.interfaces import Point3D
from indian_features.enums import EmergencyType, VehicleType
from indian_features.mixed_traffic_manager import MixedTrafficManager, CongestionZone
from enhanced_visualization.config import VisualizationConfig, UIConfig
from enhanced_visualization.traffic_flow_visualizer import TrafficFlowVisualizer
import networkx as nx
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import Sequence, Wait, Func
from direct.task import Task
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    loadPrcFileData, WindowProperties, Vec3, Vec4, Point3,
    DirectionalLight, AmbientLight, PandaNode, CardMaker,
    TransparencyAttrib, ColorBlendAttrib, RenderState,
    LineSegs, GeomNode, TextNode
)
import sys
import os
import math
import random
import time
from typing import Dict, List, Any, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Panda3D imports

# Project imports


class TrafficVisualizationDemo(ShowBase):
    """
    Main demo application showing Indian traffic visualization
    """

    def __init__(self):
        """Initialize the demo application"""

        # Configure Panda3D
        loadPrcFileData("", "window-title Indian Traffic Digital Twin Demo")
        loadPrcFileData("", "win-size 1200 800")
        loadPrcFileData("", "show-frame-rate-meter true")
        loadPrcFileData("", "sync-video false")

        # Initialize ShowBase
        ShowBase.__init__(self)

        # Setup camera
        self.camera.setPos(0, -200, 100)
        self.camera.lookAt(0, 0, 0)

        # Setup lighting
        self.setup_lighting()

        # Create road network
        self.road_network = self.create_demo_road_network()

        # Initialize visualization components
        self.setup_visualization()

        # Initialize traffic simulation
        self.setup_traffic_simulation()

        # Setup UI
        self.setup_ui()

        # Start simulation
        self.start_simulation()

        print("🚗 Indian Traffic Digital Twin Demo Started!")
        print("📋 Controls:")
        print("   - Mouse wheel: Zoom in/out")
        print("   - Arrow Keys: Move camera")
        print("   - Space: Toggle simulation pause")
        print("   - E: Trigger emergency scenario")
        print("   - C: Clear all alerts")
        print("   - R: Reset simulation")

    def setup_lighting(self):
        """Setup scene lighting"""
        # Ambient light
        ambient_light = AmbientLight('ambient')
        ambient_light.setColor(Vec4(0.3, 0.3, 0.4, 1))
        ambient_light_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_light_np)

        # Directional light (sun)
        sun_light = DirectionalLight('sun')
        sun_light.setColor(Vec4(0.8, 0.8, 0.7, 1))
        sun_light.setDirection(Vec3(-1, -1, -1))
        sun_light_np = self.render.attachNewNode(sun_light)
        self.render.setLight(sun_light_np)

    def create_demo_road_network(self) -> nx.Graph:
        """Create a demo road network for visualization"""
        G = nx.Graph()

        # Create a grid-like road network
        grid_size = 5
        spacing = 50

        # Add nodes
        for i in range(grid_size):
            for j in range(grid_size):
                node_id = i * grid_size + j
                x = (i - grid_size//2) * spacing
                y = (j - grid_size//2) * spacing
                G.add_node(node_id, x=x, y=y, z=0)

        # Add edges (roads)
        for i in range(grid_size):
            for j in range(grid_size):
                node_id = i * grid_size + j

                # Connect to right neighbor
                if i < grid_size - 1:
                    right_neighbor = (i + 1) * grid_size + j
                    G.add_edge(node_id, right_neighbor, road_type='main')

                # Connect to top neighbor
                if j < grid_size - 1:
                    top_neighbor = i * grid_size + (j + 1)
                    G.add_edge(node_id, top_neighbor, road_type='main')

        # Add some diagonal roads for complexity
        for i in range(grid_size - 1):
            for j in range(grid_size - 1):
                node_id = i * grid_size + j
                diagonal_neighbor = (i + 1) * grid_size + (j + 1)
                if random.random() < 0.3:  # 30% chance of diagonal road
                    G.add_edge(node_id, diagonal_neighbor,
                               road_type='secondary')

        print(
            f"Created road network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G

    def setup_visualization(self):
        """Setup visualization components"""
        # Create configuration
        ui_config = UIConfig()
        self.config = VisualizationConfig(ui_config=ui_config)

        # Create traffic flow visualizer
        self.traffic_visualizer = TrafficFlowVisualizer(
            self.config, self.render)

        # Initialize with road network
        self.traffic_visualizer.initialize_traffic_overlay(self.road_network)

        # Create ground plane
        self.create_ground_plane()

        # Create road visualization
        self.create_road_visualization()

    def create_ground_plane(self):
        """Create a ground plane for the scene"""
        # Create a large ground plane
        cm = CardMaker("ground")
        cm.setFrame(-500, 500, -500, 500)
        ground = self.render.attachNewNode(cm.generate())
        ground.setPos(0, 0, -1)
        ground.setHpr(0, -90, 0)
        ground.setColor(0.2, 0.4, 0.2, 1)  # Dark green

    def create_road_visualization(self):
        """Create basic road visualization"""
        # Create road segments
        for u, v, data in self.road_network.edges(data=True):
            u_data = self.road_network.nodes[u]
            v_data = self.road_network.nodes[v]

            # Create road segment
            road_segs = LineSegs()
            road_segs.setThickness(3.0)
            road_segs.setColor(0.3, 0.3, 0.3, 1)  # Dark gray

            road_segs.moveTo(u_data['x'], u_data['y'], 0)
            road_segs.drawTo(v_data['x'], v_data['y'], 0)

            road_node = self.render.attachNewNode(road_segs.create())
            road_node.setName(f"road_{u}_{v}")

    def setup_traffic_simulation(self):
        """Setup traffic simulation components"""
        # Create mixed traffic manager
        self.traffic_manager = MixedTrafficManager()

        # Create some demo vehicles
        self.create_demo_vehicles()

        # Simulation state
        self.simulation_time = 0.0
        self.simulation_paused = False
        self.update_interval = 0.1  # Update every 100ms

    def create_demo_vehicles(self):
        """Create demo vehicles for the simulation"""
        vehicle_types = [VehicleType.CAR, VehicleType.MOTORCYCLE, VehicleType.BUS,
                         VehicleType.AUTO_RICKSHAW, VehicleType.TRUCK]

        # Create vehicles at random positions
        for i in range(20):
            vehicle_type = random.choice(vehicle_types)

            # Random position on the road network
            node_id = random.choice(list(self.road_network.nodes()))
            node_data = self.road_network.nodes[node_id]

            position = Point3D(
                node_data['x'] + random.uniform(-10, 10),
                node_data['y'] + random.uniform(-10, 10),
                0
            )

            # Create vehicle
            behavior_params = BehaviorParameters()
            vehicle = IndianVehicle(
                vehicle_id=f"vehicle_{i}",
                vehicle_type=vehicle_type,
                initial_position=position,
                behavior_params=behavior_params
            )

            # Register with traffic manager
            self.traffic_manager.register_vehicle(vehicle)

    def setup_ui(self):
        """Setup user interface"""
        # Title
        self.title = OnscreenText(
            text="Indian Traffic Digital Twin - Live Demo",
            pos=(0, 0.9),
            scale=0.08,
            fg=(1, 1, 1, 1),
            shadow=(0, 0, 0, 0.5)
        )

        # Instructions
        instructions = [
            "Controls:",
            "Mouse wheel: Zoom in/out",
            "Arrow Keys: Move camera",
            "Space: Pause/Resume",
            "E: Emergency scenario",
            "C: Clear alerts",
            "R: Reset simulation"
        ]

        self.instruction_text = OnscreenText(
            text="\n".join(instructions),
            pos=(-0.95, 0.8),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            shadow=(0, 0, 0, 0.5)
        )

        # Stats display
        self.stats_text = OnscreenText(
            text="",
            pos=(0.7, 0.8),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            shadow=(0, 0, 0, 0.5)
        )

        # Setup input handling
        self.accept("space", self.toggle_pause)
        self.accept("e", self.trigger_emergency)
        self.accept("c", self.clear_alerts)
        self.accept("r", self.reset_simulation)

        # Camera controls
        self.accept("arrow_up", self.move_camera, [Vec3(0, 10, 0)])
        self.accept("arrow_down", self.move_camera, [Vec3(0, -10, 0)])
        self.accept("arrow_left", self.move_camera, [Vec3(-10, 0, 0)])
        self.accept("arrow_right", self.move_camera, [Vec3(10, 0, 0)])

        # Mouse zoom controls
        self.accept("wheel_up", self.zoom_camera, [-15])
        self.accept("wheel_down", self.zoom_camera, [15])

    def start_simulation(self):
        """Start the simulation loop"""
        # Start update task
        self.taskMgr.add(self.update_simulation, "update_simulation")

        # Start periodic traffic updates
        self.taskMgr.add(self.update_traffic_density, "update_traffic_density")

        # Start random events
        self.taskMgr.add(self.generate_random_events, "random_events")

    def update_simulation(self, task):
        """Main simulation update loop"""
        if self.simulation_paused:
            return task.cont

        dt = globalClock.getDt()
        self.simulation_time += dt

        # Update traffic manager
        traffic_data = self.traffic_manager.simulate_mixed_vehicle_dynamics(dt)

        # Update visualization with traffic data
        self.traffic_visualizer.update_from_mixed_traffic_manager(traffic_data)

        # Update stats display
        self.update_stats_display(traffic_data)

        return task.cont

    def update_traffic_density(self, task):
        """Update traffic density visualization"""
        if self.simulation_paused:
            return task.cont

        # Generate realistic traffic density data
        edge_densities = {}

        for edge in self.road_network.edges():
            # Simulate varying traffic density
            base_density = 0.3
            time_factor = math.sin(self.simulation_time * 0.1) * 0.2
            random_factor = random.uniform(-0.1, 0.1)

            density = max(0.0, min(1.0, base_density +
                          time_factor + random_factor))
            edge_densities[edge] = density

        # Update visualization
        self.traffic_visualizer.update_traffic_density(edge_densities)

        # Generate speed data for congestion indicators
        edge_speeds = {}
        for edge, density in edge_densities.items():
            # Convert density to speed (inverse relationship)
            free_flow_speed = 50.0
            speed = free_flow_speed * (1.0 - density * 0.8)
            edge_speeds[edge] = max(5.0, speed)

        self.traffic_visualizer.create_real_time_congestion_indicators(
            edge_speeds)

        return task.cont

    def generate_random_events(self, task):
        """Generate random traffic events"""
        if self.simulation_paused:
            return task.cont

        # Random chance of events
        if random.random() < 0.02:  # 2% chance per frame
            event_type = random.choice(['congestion', 'emergency'])

            if event_type == 'congestion':
                self.create_random_congestion()
            elif event_type == 'emergency':
                self.create_random_emergency()

        return task.cont

    def create_random_congestion(self):
        """Create a random congestion hotspot"""
        # Random location
        x = random.uniform(-100, 100)
        y = random.uniform(-100, 100)

        hotspot = {
            'id': f'random_congestion_{int(self.simulation_time)}',
            'x': x,
            'y': y,
            'z': 0,
            'radius': random.uniform(20, 40),
            'intensity': random.uniform(0.6, 1.0),
            'affected_edges': []
        }

        self.traffic_visualizer.show_congestion_hotspots([hotspot])

        # Auto-clear after some time
        def clear_hotspot():
            self.traffic_visualizer._clear_congestion_hotspots()

        Sequence(Wait(5.0), Func(clear_hotspot)).start()

    def create_random_emergency(self):
        """Create a random emergency scenario"""
        # Random location
        x = random.uniform(-100, 100)
        y = random.uniform(-100, 100)

        emergency_types = [EmergencyType.ACCIDENT,
                           EmergencyType.FLOODING, EmergencyType.CONSTRUCTION]

        emergency = {
            'id': f'random_emergency_{int(self.simulation_time)}',
            'type': random.choice(emergency_types),
            'x': x,
            'y': y,
            'z': 0,
            'severity': random.uniform(0.5, 1.0),
            'affected_area': []
        }

        self.traffic_visualizer.display_emergency_alerts([emergency])

        # Auto-clear after some time
        def clear_emergency():
            self.traffic_visualizer._clear_emergency_alerts()

        Sequence(Wait(8.0), Func(clear_emergency)).start()

    def update_stats_display(self, traffic_data):
        """Update the statistics display"""
        stats = traffic_data.get('statistics', {})

        stats_text = f"""Traffic Statistics:
Vehicles: {stats.get('total_vehicles', 0)}
Interactions: {len(traffic_data.get('interactions', []))}
Congestion Zones: {len(traffic_data.get('congestion_zones', []))}
Emergency Vehicles: {stats.get('emergency_vehicles', 0)}
Simulation Time: {self.simulation_time:.1f}s
Status: {'PAUSED' if self.simulation_paused else 'RUNNING'}"""

        self.stats_text.setText(stats_text)

    def toggle_pause(self):
        """Toggle simulation pause"""
        self.simulation_paused = not self.simulation_paused
        print(
            f"Simulation {'PAUSED' if self.simulation_paused else 'RESUMED'}")

    def trigger_emergency(self):
        """Trigger an emergency scenario"""
        print("🚨 Emergency scenario triggered!")

        # Create emergency at camera focus point
        emergency = {
            'id': f'manual_emergency_{int(self.simulation_time)}',
            'type': EmergencyType.ACCIDENT,
            'x': 0,
            'y': 0,
            'z': 0,
            'severity': 0.9,
            'affected_area': []
        }

        self.traffic_visualizer.display_emergency_alerts([emergency])

    def clear_alerts(self):
        """Clear all alerts"""
        print("🧹 Clearing all alerts")
        self.traffic_visualizer._clear_congestion_hotspots()
        self.traffic_visualizer._clear_emergency_alerts()

    def reset_simulation(self):
        """Reset the simulation"""
        print("🔄 Resetting simulation")
        self.simulation_time = 0.0
        self.clear_alerts()

        # Reset traffic manager
        self.traffic_manager = MixedTrafficManager()
        self.create_demo_vehicles()

    def move_camera(self, direction):
        """Move camera in specified direction"""
        current_pos = self.camera.getPos()
        new_pos = current_pos + direction
        self.camera.setPos(new_pos)

    def zoom_camera(self, zoom_amount):
        """Zoom camera in/out by moving towards/away from the target"""
        current_pos = self.camera.getPos()
        target_pos = Vec3(0, 0, 0)  # Looking at origin

        # Calculate direction from target to camera
        direction = current_pos - target_pos
        direction.normalize()

        # Move camera along this direction
        new_pos = current_pos + direction * zoom_amount

        # Clamp distance to reasonable bounds
        distance = (new_pos - target_pos).length()
        if distance < 20:  # Too close
            direction.normalize()
            new_pos = target_pos + direction * 20
        elif distance > 800:  # Too far
            direction.normalize()
            new_pos = target_pos + direction * 800

        self.camera.setPos(new_pos)
        self.camera.lookAt(target_pos)


def main():
    """Main function to run the demo"""
    print("🚀 Starting Indian Traffic Digital Twin Visualization Demo...")

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
