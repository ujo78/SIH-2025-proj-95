#!/usr/bin/env python3
"""
Full 3D Traffic Simulation with Cars, Roads, and Interactive Controls

This creates a complete traffic simulation with:
- 3D roads and intersections
- Moving vehicles (cars, buses, trucks, motorcycles)
- Real-time traffic flow visualization
- Interactive camera with zoom and pan
- Traffic lights and signs
- Indian traffic scenarios and behaviors
"""

from indian_features.scenario_templates import create_all_default_templates
from indian_features.scenario_manager import ScenarioManager
from indian_features.weather_conditions import WeatherManager
from indian_features.emergency_scenarios import EmergencyManager
from indian_features.behavior_model import IndianBehaviorModel
from indian_features.mixed_traffic_manager import MixedTrafficManager
from indian_features.vehicle_factory import IndianVehicleFactory
from indian_features.config import IndianTrafficConfig
from indian_features.interfaces import Point3D
from indian_features.enums import VehicleType, WeatherType, EmergencyType
import sys
import os
import math
import random
import time
from typing import Dict, List, Any, Tuple, Optional
import networkx as nx

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Panda3D imports
    from panda3d.core import (
        loadPrcFileData, WindowProperties, Vec3, Vec4, Point3,
        DirectionalLight, AmbientLight, CardMaker, PandaNode,
        GeomNode, Geom, GeomVertexFormat, GeomVertexData, GeomVertexWriter,
        GeomTriangles, GeomLines, Material, Texture, TextNode,
        CollisionTraverser, CollisionNode, CollisionSphere, CollisionHandlerQueue,
        TransformState, RenderState, ColorAttrib, LightAttrib, LineSegs
    )
    from direct.showbase.ShowBase import ShowBase
    from direct.task import Task
    from direct.gui.OnscreenText import OnscreenText
    from direct.gui.DirectGui import DirectButton, DirectFrame, DirectSlider, DirectLabel
    from direct.interval.IntervalGlobal import Sequence, Parallel, LerpPosInterval, LerpHprInterval
    PANDA3D_AVAILABLE = True
except ImportError:
    print("Panda3D not available. Using mock implementation.")
    PANDA3D_AVAILABLE = False

# OSMnx for road networks
try:
    import osmnx as ox
    OSMNX_AVAILABLE = True
except ImportError:
    print("OSMnx not available. Using mock road network.")
    OSMNX_AVAILABLE = False

# Project imports


class Vehicle3D:
    """3D representation of a vehicle"""

    def __init__(self, vehicle_id: str, vehicle_type: VehicleType, position: Point3, render_root):
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.position = position
        self.heading = 0.0
        self.speed = 0.0
        self.target_position = position
        self.render_root = render_root

        # Create 3D model
        self.model = self._create_vehicle_model()
        if self.model:
            self.model.reparentTo(render_root)
            self.model.setPos(position)

        # Animation
        self.move_interval = None

    def _create_vehicle_model(self):
        """Create a simple 3D vehicle model"""
        if not PANDA3D_AVAILABLE:
            return None

        # Create different shapes for different vehicle types
        if self.vehicle_type == VehicleType.CAR:
            return self._create_car_model()
        elif self.vehicle_type == VehicleType.BUS:
            return self._create_bus_model()
        elif self.vehicle_type == VehicleType.TRUCK:
            return self._create_truck_model()
        elif self.vehicle_type == VehicleType.MOTORCYCLE:
            return self._create_motorcycle_model()
        elif self.vehicle_type == VehicleType.AUTO_RICKSHAW:
            return self._create_rickshaw_model()
        else:
            return self._create_car_model()  # Default

    def _create_car_model(self):
        """Create a car model using 3D model or fallback to simple geometry"""
        try:
            # Try to load the car.egg model with different case variations
            car_model = self.render_root.attachNewNode("car_container")

            # Try different filename variations
            model_files = ["car.egg", "Car.egg", "CAR.egg", "car.EGG"]
            car_3d = None

            for model_file in model_files:
                if os.path.exists(model_file):
                    try:
                        car_3d = loader.loadModel(model_file)
                        if car_3d and not car_3d.isEmpty():
                            print(f"Successfully loaded {model_file}")
                            break
                    except:
                        continue

            if car_3d and not car_3d.isEmpty():
                car_3d.reparentTo(car_model)
                # Scale and position the model appropriately
                car_3d.setScale(1.5, 1.5, 1.5)  # Adjust scale as needed
                car_3d.setZ(0.1)

                # Random car color
                colors = [(0.8, 0.2, 0.2, 1), (0.2, 0.8, 0.2, 1), (0.2, 0.2, 0.8, 1),
                          (0.8, 0.8, 0.2, 1), (0.8, 0.2,
                                               0.8, 1), (0.2, 0.8, 0.8, 1),
                          # Added white and black
                          (0.9, 0.9, 0.9, 1), (0.1, 0.1, 0.1, 1)]
                car_3d.setColor(random.choice(colors))

                return car_model
            else:
                print("3D car model not found or failed to load, using simple geometry")

        except Exception as e:
            print(f"Error loading 3D car model: {e}, using simple geometry")

        # Fallback: Create car body using CardMaker with improved appearance
        cm = CardMaker("car_body")
        cm.setFrame(-1.5, 1.5, -0.8, 0.8)
        car_body = self.render_root.attachNewNode(cm.generate())
        car_body.setP(-90)  # Flat on ground
        car_body.setZ(0.3)

        # Random car color with better variety
        colors = [(0.8, 0.2, 0.2, 1), (0.2, 0.8, 0.2, 1), (0.2, 0.2, 0.8, 1),
                  (0.8, 0.8, 0.2, 1), (0.8, 0.2, 0.8, 1), (0.2, 0.8, 0.8, 1),
                  (0.9, 0.9, 0.9, 1), (0.1, 0.1, 0.1, 1), (0.6, 0.3, 0.1, 1)]
        car_body.setColor(random.choice(colors))

        # Add roof with better proportions
        cm_roof = CardMaker("car_roof")
        cm_roof.setFrame(-1.0, 1.0, -0.6, 0.6)
        car_roof = car_body.attachNewNode(cm_roof.generate())
        car_roof.setZ(0.6)
        car_roof.setColor(0.2, 0.2, 0.2, 1)

        # Add windows
        cm_windows = CardMaker("car_windows")
        cm_windows.setFrame(-0.8, 0.8, -0.5, 0.5)
        car_windows = car_roof.attachNewNode(cm_windows.generate())
        car_windows.setZ(0.1)
        car_windows.setColor(0.3, 0.5, 0.8, 0.7)  # Blue tinted windows

        return car_body

    def _create_bus_model(self):
        """Create a bus model"""
        cm = CardMaker("bus_body")
        cm.setFrame(-3.0, 3.0, -1.2, 1.2)
        bus_body = self.render_root.attachNewNode(cm.generate())
        bus_body.setP(-90)
        bus_body.setZ(0.5)
        bus_body.setColor(0.9, 0.7, 0.1, 1)  # Yellow bus

        # Add windows
        cm_windows = CardMaker("bus_windows")
        cm_windows.setFrame(-2.5, 2.5, -1.0, 1.0)
        bus_windows = bus_body.attachNewNode(cm_windows.generate())
        bus_windows.setZ(0.8)
        bus_windows.setColor(0.6, 0.8, 1.0, 0.7)

        return bus_body

    def _create_truck_model(self):
        """Create a truck model"""
        cm = CardMaker("truck_body")
        cm.setFrame(-2.5, 2.5, -1.0, 1.0)
        truck_body = self.render_root.attachNewNode(cm.generate())
        truck_body.setP(-90)
        truck_body.setZ(0.6)
        truck_body.setColor(0.5, 0.3, 0.1, 1)  # Brown truck

        # Add cargo area
        cm_cargo = CardMaker("truck_cargo")
        cm_cargo.setFrame(-1.5, 1.5, -0.8, 0.8)
        truck_cargo = truck_body.attachNewNode(cm_cargo.generate())
        truck_cargo.setZ(0.8)
        truck_cargo.setColor(0.7, 0.7, 0.7, 1)

        return truck_body

    def _create_motorcycle_model(self):
        """Create a motorcycle model"""
        cm = CardMaker("motorcycle_body")
        cm.setFrame(-0.8, 0.8, -0.3, 0.3)
        motorcycle_body = self.render_root.attachNewNode(cm.generate())
        motorcycle_body.setP(-90)
        motorcycle_body.setZ(0.2)
        motorcycle_body.setColor(0.2, 0.2, 0.2, 1)  # Black motorcycle

        return motorcycle_body

    def _create_rickshaw_model(self):
        """Create an auto-rickshaw model"""
        cm = CardMaker("rickshaw_body")
        cm.setFrame(-1.2, 1.2, -0.6, 0.6)
        rickshaw_body = self.render_root.attachNewNode(cm.generate())
        rickshaw_body.setP(-90)
        rickshaw_body.setZ(0.4)
        rickshaw_body.setColor(0.9, 0.9, 0.1, 1)  # Yellow rickshaw

        # Add canopy
        cm_canopy = CardMaker("rickshaw_canopy")
        cm_canopy.setFrame(-1.0, 1.0, -0.5, 0.5)
        rickshaw_canopy = rickshaw_body.attachNewNode(cm_canopy.generate())
        rickshaw_canopy.setZ(0.6)
        rickshaw_canopy.setColor(0.1, 0.1, 0.1, 1)

        return rickshaw_body

    def update_position(self, new_position: Point3, new_heading: float = None):
        """Update vehicle position with smooth animation"""
        if not self.model:
            return

        self.target_position = new_position

        if new_heading is not None:
            self.heading = new_heading

        # Stop current animation
        if self.move_interval:
            self.move_interval.finish()

        # Create smooth movement
        duration = 0.5  # Animation duration
        self.move_interval = Parallel(
            LerpPosInterval(self.model, duration, new_position),
            LerpHprInterval(self.model, duration, Vec3(
                math.degrees(self.heading), 0, 0))
        )
        self.move_interval.start()

    def remove(self):
        """Remove vehicle from scene"""
        if self.move_interval:
            self.move_interval.finish()
        if self.model:
            self.model.removeNode()


class Road3D:
    """3D representation of a road segment"""

    def __init__(self, start_pos: Point3, end_pos: Point3, width: float, render_root):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.width = width
        self.render_root = render_root

        # Create road geometry
        self.road_node = self._create_road_geometry()
        if self.road_node:
            self.road_node.reparentTo(render_root)

    def _create_road_geometry(self):
        """Create road geometry using LineSegs"""
        if not PANDA3D_AVAILABLE:
            return None

        # Create road as a thick line with better visibility
        ls = LineSegs()
        ls.setThickness(max(30, self.width * 25))  # Much thicker roads
        ls.setColor(0.05, 0.05, 0.05, 1)  # Very dark road for maximum contrast

        ls.moveTo(self.start_pos)
        ls.drawTo(self.end_pos)

        road_node = self.render_root.attachNewNode(ls.create())

        # Add elevation to prevent z-fighting and improve visibility
        road_node.setZ(0.1)

        # Add road markings
        self._add_road_markings(road_node)

        return road_node

    def _add_road_markings(self, road_node):
        """Add lane markings to the road"""
        # Create center line with better visibility
        ls_center = LineSegs()
        ls_center.setThickness(3)
        ls_center.setColor(1, 0.9, 0, 1)  # Bright yellow center line

        # Calculate center line points along the road
        ls_center.moveTo(self.start_pos.x, self.start_pos.y,
                         self.start_pos.z + 0.02)
        ls_center.drawTo(self.end_pos.x, self.end_pos.y, self.end_pos.z + 0.02)

        center_node = road_node.attachNewNode(ls_center.create())

        # Add white edge lines for better road definition
        ls_edge1 = LineSegs()
        ls_edge1.setThickness(2)
        ls_edge1.setColor(0.9, 0.9, 0.9, 1)  # White edge lines

        # Calculate perpendicular offset for edge lines
        dx = self.end_pos.x - self.start_pos.x
        dy = self.end_pos.y - self.start_pos.y
        length = math.sqrt(dx*dx + dy*dy)

        if length > 0:
            # Normalize and get perpendicular
            nx = -dy / length
            ny = dx / length
            offset = self.width * 0.4  # Edge offset

            # Left edge
            ls_edge1.moveTo(
                self.start_pos.x + nx * offset,
                self.start_pos.y + ny * offset,
                self.start_pos.z + 0.02
            )
            ls_edge1.drawTo(
                self.end_pos.x + nx * offset,
                self.end_pos.y + ny * offset,
                self.end_pos.z + 0.02
            )

            # Right edge
            ls_edge1.moveTo(
                self.start_pos.x - nx * offset,
                self.start_pos.y - ny * offset,
                self.start_pos.z + 0.02
            )
            ls_edge1.drawTo(
                self.end_pos.x - nx * offset,
                self.end_pos.y - ny * offset,
                self.end_pos.z + 0.02
            )

            edge_node = road_node.attachNewNode(ls_edge1.create())


class TrafficLight3D:
    """3D representation of a traffic light"""

    def __init__(self, position: Point3, render_root):
        self.position = position
        self.render_root = render_root
        self.state = "red"  # red, yellow, green

        # Create traffic light model
        self.light_node = self._create_traffic_light()
        if self.light_node:
            self.light_node.reparentTo(render_root)
            self.light_node.setPos(position)

    def _create_traffic_light(self):
        """Create traffic light geometry"""
        if not PANDA3D_AVAILABLE:
            return None

        # Create pole
        cm_pole = CardMaker("light_pole")
        cm_pole.setFrame(-0.1, 0.1, -0.1, 0.1)
        pole = self.render_root.attachNewNode(cm_pole.generate())
        pole.setZ(3.0)
        pole.setColor(0.2, 0.2, 0.2, 1)

        # Create light box
        cm_box = CardMaker("light_box")
        cm_box.setFrame(-0.3, 0.3, -0.8, 0.8)
        light_box = pole.attachNewNode(cm_box.generate())
        light_box.setP(-90)
        light_box.setZ(2.5)
        light_box.setColor(0.1, 0.1, 0.1, 1)

        # Create lights (red, yellow, green)
        self.red_light = self._create_light_circle(
            light_box, Vec3(0, 0, 0.4), (1, 0, 0, 1))
        self.yellow_light = self._create_light_circle(
            light_box, Vec3(0, 0, 0), (1, 1, 0, 1))
        self.green_light = self._create_light_circle(
            light_box, Vec3(0, 0, -0.4), (0, 1, 0, 1))

        self.update_state("red")

        return pole

    def _create_light_circle(self, parent, pos, color):
        """Create a circular light"""
        cm = CardMaker("light_circle")
        cm.setFrame(-0.15, 0.15, -0.15, 0.15)
        light = parent.attachNewNode(cm.generate())
        light.setPos(pos)
        light.setColor(*color)
        return light

    def update_state(self, new_state):
        """Update traffic light state"""
        self.state = new_state

        if not PANDA3D_AVAILABLE:
            return

        # Dim all lights
        if hasattr(self, 'red_light'):
            self.red_light.setColorScale(0.3, 0.3, 0.3, 1)
        if hasattr(self, 'yellow_light'):
            self.yellow_light.setColorScale(0.3, 0.3, 0.3, 1)
        if hasattr(self, 'green_light'):
            self.green_light.setColorScale(0.3, 0.3, 0.3, 1)

        # Brighten active light
        if new_state == "red" and hasattr(self, 'red_light'):
            self.red_light.setColorScale(1, 1, 1, 1)
        elif new_state == "yellow" and hasattr(self, 'yellow_light'):
            self.yellow_light.setColorScale(1, 1, 1, 1)
        elif new_state == "green" and hasattr(self, 'green_light'):
            self.green_light.setColorScale(1, 1, 1, 1)


class FullTrafficSimulation(ShowBase if PANDA3D_AVAILABLE else object):
    """Complete 3D traffic simulation with Indian traffic features"""

    def __init__(self):
        if not PANDA3D_AVAILABLE:
            print("Panda3D not available. Running in console mode.")
            self.run_console_simulation()
            return

        # Configure Panda3D
        loadPrcFileData("", "window-title Full Indian Traffic Simulation")
        loadPrcFileData("", "win-size 1200 800")
        loadPrcFileData("", "show-frame-rate-meter true")

        # Initialize ShowBase
        super().__init__()

        # Simulation parameters
        self.simulation_running = False
        self.simulation_speed = 1.0
        self.current_time = 0.0

        # Initialize Indian traffic components
        self.setup_indian_traffic_system()

        # Create road network
        self.setup_road_network()

        # 3D objects
        self.vehicles_3d: Dict[str, Vehicle3D] = {}
        self.roads_3d: List[Road3D] = []
        self.traffic_lights_3d: List[TrafficLight3D] = []

        # Setup 3D scene
        self.setup_scene()
        self.setup_lighting()
        self.setup_camera()
        self.setup_ui()

        # Create initial roads and intersections
        self.create_road_network_3d()

        # Start simulation
        self.start_simulation()

    def setup_indian_traffic_system(self):
        """Initialize Indian traffic management system"""
        # Load scenario templates
        self.scenario_manager = ScenarioManager()
        templates = create_all_default_templates()
        for template_id, template in templates.items():
            self.scenario_manager.templates[template_id] = template

        # Use Mumbai intersection scenario as default
        self.current_scenario = self.scenario_manager.get_template(
            "mumbai_intersection")
        if not self.current_scenario:
            # Fallback to default config
            self.traffic_config = IndianTrafficConfig()
        else:
            self.traffic_config = self.current_scenario.traffic_config

        # Initialize traffic components
        self.vehicle_factory = IndianVehicleFactory(self.traffic_config)
        self.behavior_model = IndianBehaviorModel()
        self.mixed_traffic_manager = MixedTrafficManager(self.behavior_model)
        self.weather_manager = WeatherManager()

        # Create mock road network for emergency manager
        self.road_graph = self.create_mock_road_network()
        self.emergency_manager = EmergencyManager(
            self.road_graph, self.mixed_traffic_manager)

        # Simulation state
        self.active_vehicles: Dict[str, Any] = {}
        self.vehicle_counter = 0
        self.spawn_timer = 0.0

        print(
            f"Loaded scenario: {self.current_scenario.name if self.current_scenario else 'Default'}")

    def create_mock_road_network(self):
        """Create a simple mock road network for the simulation"""
        G = nx.Graph()

        # Create a grid of intersections
        grid_size = 5
        node_spacing = 50.0

        # Add nodes
        for i in range(grid_size):
            for j in range(grid_size):
                node_id = i * grid_size + j
                x = (i - grid_size//2) * node_spacing
                y = (j - grid_size//2) * node_spacing
                G.add_node(node_id, x=x, y=y, z=0)

        # Add edges (roads)
        for i in range(grid_size):
            for j in range(grid_size):
                node_id = i * grid_size + j

                # Connect to right neighbor
                if i < grid_size - 1:
                    right_neighbor = (i + 1) * grid_size + j
                    G.add_edge(node_id, right_neighbor,
                               length=node_spacing,
                               travel_time=node_spacing/30.0)  # 30 km/h average

                # Connect to top neighbor
                if j < grid_size - 1:
                    top_neighbor = i * grid_size + (j + 1)
                    G.add_edge(node_id, top_neighbor,
                               length=node_spacing,
                               travel_time=node_spacing/30.0)

        return G

    def setup_road_network(self):
        """Setup road network (mock or from OSMnx)"""
        if OSMNX_AVAILABLE:
            try:
                # Try to load a real road network
                center_point = (19.0760, 72.8777)  # Mumbai coordinates
                self.road_graph = ox.graph_from_point(
                    center_point, dist=1000, network_type="drive")
                self.road_graph = ox.add_edge_speeds(self.road_graph)
                self.road_graph = ox.add_edge_travel_times(self.road_graph)
                print("Loaded real road network from OSMnx")
            except Exception as e:
                print(f"Failed to load OSMnx network: {e}")
                self.road_graph = self.create_mock_road_network()
        else:
            self.road_graph = self.create_mock_road_network()

    def setup_scene(self):
        """Setup 3D scene"""
        # Set background color (sky blue)
        self.setBackgroundColor(0.5, 0.8, 1.0)

        # Create ground plane
        self.create_ground_plane()

        # Enable collision detection
        self.cTrav = CollisionTraverser()
        self.collision_handler = CollisionHandlerQueue()

    def create_ground_plane(self):
        """Create a ground plane"""
        cm = CardMaker("ground")
        cm.setFrame(-500, 500, -500, 500)
        ground = self.render.attachNewNode(cm.generate())
        ground.setP(-90)  # Flat
        # Brighter green ground for better contrast
        ground.setColor(0.3, 0.7, 0.3, 1)
        ground.setZ(-0.2)  # Further below roads to prevent z-fighting

    def setup_lighting(self):
        """Setup scene lighting"""
        # Ambient light
        ambient_light = AmbientLight("ambient_light")
        ambient_light.setColor((0.3, 0.3, 0.3, 1))
        ambient_light_np = self.render.attachNewNode(ambient_light)
        self.render.setLight(ambient_light_np)

        # Directional light (sun)
        directional_light = DirectionalLight("directional_light")
        directional_light.setColor((0.8, 0.8, 0.8, 1))
        directional_light.setDirection(Vec3(-1, -1, -1))
        directional_light_np = self.render.attachNewNode(directional_light)
        self.render.setLight(directional_light_np)

    def setup_camera(self):
        """Setup camera controls"""
        # Position camera above the scene for better visibility
        self.camera.setPos(0, -50, 30)  # Closer and lower for better road visibility
        self.camera.lookAt(0, 0, 0)

        # Enable mouse camera control
        self.disableMouse()

        # Camera control variables
        self.camera_speed = 50.0
        self.zoom_factor = 0.1  # Relative zoom factor

        # Mouse rotation variables
        self.mouse_rotating = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.camera_h = 0  # Horizontal rotation
        self.camera_p = -30  # Pitch (looking down)

        # Accept input events
        self.accept("w", self.move_camera_forward)
        self.accept("s", self.move_camera_backward)
        self.accept("a", self.move_camera_left)
        self.accept("d", self.move_camera_right)
        self.accept("q", self.move_camera_up)
        self.accept("e", self.move_camera_down)
        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)

        # Mouse controls for camera rotation
        self.accept("mouse3", self.start_mouse_rotation)  # Right mouse button
        self.accept("mouse3-up", self.stop_mouse_rotation)

        # Continuous key handling
        self.accept("w-repeat", self.move_camera_forward)
        self.accept("s-repeat", self.move_camera_backward)
        self.accept("a-repeat", self.move_camera_left)
        self.accept("d-repeat", self.move_camera_right)
        self.accept("q-repeat", self.move_camera_up)
        self.accept("e-repeat", self.move_camera_down)

        # Start mouse rotation task
        self.taskMgr.add(self.mouse_rotation_task, "mouse_rotation_task")

    def setup_ui(self):
        """Setup user interface"""
        # Title
        self.title_text = OnscreenText(
            text="Full Indian Traffic Simulation",
            pos=(0, 0.9),
            scale=0.08,
            fg=(1, 1, 1, 1),
            shadow=(0, 0, 0, 0.5)
        )

        # Instructions
        self.instructions = OnscreenText(
            text="WASD: Move Camera | Q/E: Up/Down | Mouse Wheel: Relative Zoom | Right-Click+Drag: Rotate | Space: Pause/Resume",
            pos=(-1.3, -0.9),
            scale=0.045,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft
        )

        # Statistics display
        self.stats_text = OnscreenText(
            text="",
            pos=(1.2, 0.8),
            scale=0.05,
            fg=(1, 1, 1, 1),
            align=TextNode.ARight
        )

        # Control panel
        self.create_control_panel()

        # Accept space for pause/resume
        self.accept("space", self.toggle_simulation)

    def create_control_panel(self):
        """Create UI control panel"""
        # Control frame
        self.control_frame = DirectFrame(
            frameColor=(0, 0, 0, 0.7),
            frameSize=(-0.3, 0.3, -0.4, 0.4),
            pos=(-1.0, 0, 0.5)
        )

        # Speed control
        DirectLabel(
            text="Simulation Speed",
            parent=self.control_frame,
            pos=(0, 0, 0.3),
            scale=0.05,
            text_fg=(1, 1, 1, 1)
        )

        self.speed_slider = DirectSlider(
            parent=self.control_frame,
            range=(0.1, 3.0),
            value=1.0,
            pageSize=0.1,
            pos=(0, 0, 0.2),
            scale=0.3,
            command=self.update_simulation_speed
        )

        # Emergency buttons
        DirectButton(
            text="Accident",
            parent=self.control_frame,
            pos=(-0.1, 0, -0.1),
            scale=0.04,
            command=self.trigger_accident
        )

        DirectButton(
            text="Flooding",
            parent=self.control_frame,
            pos=(0.1, 0, -0.1),
            scale=0.04,
            command=self.trigger_flooding
        )

    def create_road_network_3d(self):
        """Create 3D representation of road network"""
        print("Creating 3D road network...")

        # Create roads from graph edges with proper coordinate normalization
        # Get coordinate bounds for normalization
        x_coords = [data.get('x', 0) for _, data in self.road_graph.nodes(data=True)]
        y_coords = [data.get('y', 0) for _, data in self.road_graph.nodes(data=True)]
        
        if x_coords and y_coords:
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)
            x_center = (x_min + x_max) / 2
            y_center = (y_min + y_max) / 2
            
            # Scale to fit in a reasonable 3D space (e.g., 200x200 units)
            x_range = x_max - x_min
            y_range = y_max - y_min
            max_range = max(x_range, y_range)
            scale_factor = 200.0 / max_range if max_range > 0 else 1.0
            
            print(f"Normalizing coordinates: center=({x_center:.6f}, {y_center:.6f}), scale={scale_factor:.6f}")
        
        for u, v in self.road_graph.edges():
            u_data = self.road_graph.nodes[u]
            v_data = self.road_graph.nodes[v]

            # Normalize coordinates to center around origin
            start_pos = Point3(
                (u_data.get('x', 0) - x_center) * scale_factor,
                (u_data.get('y', 0) - y_center) * scale_factor,
                0
            )
            end_pos = Point3(
                (v_data.get('x', 0) - x_center) * scale_factor,
                (v_data.get('y', 0) - y_center) * scale_factor,
                0
            )

            road = Road3D(start_pos, end_pos, 2.0, self.render)  # Appropriate road width
            self.roads_3d.append(road)
            
        # Store normalization parameters for vehicle spawning
        self.x_center = x_center
        self.y_center = y_center
        self.scale_factor = scale_factor

        # Create traffic lights at major intersections
        major_intersections = [node for node,
                               degree in self.road_graph.degree() if degree >= 3]

        for node in major_intersections[:10]:  # Limit to 10 traffic lights
            node_data = self.road_graph.nodes[node]
            
            # Use same normalization as roads
            light_pos = Point3(
                (node_data.get('x', 0) - x_center) * scale_factor,
                (node_data.get('y', 0) - y_center) * scale_factor,
                0
            )

            traffic_light = TrafficLight3D(light_pos, self.render)
            self.traffic_lights_3d.append(traffic_light)

        print(f"Created {len(self.roads_3d)} roads and {len(self.traffic_lights_3d)} traffic lights")
        
        # Debug: Print some road coordinates to verify scaling
        if self.roads_3d:
            first_road = self.roads_3d[0]
            print(f"Sample road coordinates: {first_road.start_pos} to {first_road.end_pos}")
            
        # Debug: Print coordinate ranges
        if self.road_graph.nodes:
            x_coords = [data.get('x', 0) for _, data in self.road_graph.nodes(data=True)]
            y_coords = [data.get('y', 0) for _, data in self.road_graph.nodes(data=True)]
            print(f"Coordinate ranges: X({min(x_coords):.1f} to {max(x_coords):.1f}), Y({min(y_coords):.1f} to {max(y_coords):.1f})")

    def start_simulation(self):
        """Start the traffic simulation"""
        self.simulation_running = True

        # Start simulation task
        self.taskMgr.add(self.simulation_task, "simulation_task")

        # Start vehicle spawning task
        self.taskMgr.add(self.spawn_vehicles_task, "spawn_vehicles_task")

        # Start traffic light cycling task
        self.taskMgr.add(self.traffic_light_task, "traffic_light_task")

        # Start UI update task
        self.taskMgr.add(self.update_ui_task, "update_ui_task")

        print("Traffic simulation started!")

    def simulation_task(self, task):
        """Main simulation update task"""
        if not self.simulation_running:
            return task.cont

        dt = globalClock.getDt() * self.simulation_speed
        self.current_time += dt

        # Update vehicle positions
        self.update_vehicles(dt)

        # Update emergency scenarios
        from datetime import datetime
        self.emergency_manager.update_emergencies(datetime.now())

        # Update weather effects
        self.weather_manager.update_weather_effects(dt)

        return task.cont

    def spawn_vehicles_task(self, task):
        """Vehicle spawning task"""
        if not self.simulation_running:
            return task.cont

        dt = globalClock.getDt() * self.simulation_speed
        self.spawn_timer += dt

        # Spawn rate from traffic config
        spawn_interval = 1.0 / self.traffic_config.spawn_rate

        if self.spawn_timer >= spawn_interval and len(self.active_vehicles) < self.traffic_config.max_vehicles:
            self.spawn_vehicle()
            self.spawn_timer = 0.0

        return task.cont

    def spawn_vehicle(self):
        """Spawn a new vehicle"""
        # Select random spawn and destination nodes
        nodes = list(self.road_graph.nodes())
        if len(nodes) < 2:
            return

        spawn_node = random.choice(nodes)
        dest_node = random.choice(nodes)

        if spawn_node == dest_node:
            return

        # Create vehicle
        vehicle_id = f"vehicle_{self.vehicle_counter}"
        self.vehicle_counter += 1

        # Select vehicle type based on traffic config
        vehicle_type = self.select_vehicle_type()

        # Get spawn position with consistent normalization
        spawn_data = self.road_graph.nodes[spawn_node]
        
        spawn_pos = Point3(
            (spawn_data.get('x', 0) - self.x_center) * self.scale_factor,
            (spawn_data.get('y', 0) - self.y_center) * self.scale_factor,
            0.5  # Slightly elevated for visibility
        )

        # Create 3D vehicle
        vehicle_3d = Vehicle3D(vehicle_id, vehicle_type,
                               spawn_pos, self.render)
        self.vehicles_3d[vehicle_id] = vehicle_3d

        # Store vehicle data
        self.active_vehicles[vehicle_id] = {
            'type': vehicle_type,
            'current_node': spawn_node,
            'destination_node': dest_node,
            'position': spawn_pos,
            'speed': random.uniform(20, 60),  # km/h
            'path': None
        }

        # Calculate path
        try:
            path = nx.shortest_path(self.road_graph, spawn_node, dest_node)
            self.active_vehicles[vehicle_id]['path'] = path
        except nx.NetworkXNoPath:
            # Remove vehicle if no path found
            self.remove_vehicle(vehicle_id)

    def select_vehicle_type(self):
        """Select vehicle type based on traffic config ratios"""
        ratios = self.traffic_config.vehicle_mix_ratios

        # Create weighted list
        vehicle_types = []
        weights = []

        for vehicle_type, ratio in ratios.items():
            vehicle_types.append(vehicle_type)
            weights.append(ratio)

        # Select random vehicle type
        return random.choices(vehicle_types, weights=weights)[0]

    def update_vehicles(self, dt):
        """Update all vehicle positions"""
        vehicles_to_remove = []

        for vehicle_id, vehicle_data in self.active_vehicles.items():
            if vehicle_id not in self.vehicles_3d:
                continue

            # Simple movement along path
            if vehicle_data['path'] and len(vehicle_data['path']) > 1:
                # Move towards next node in path
                current_node = vehicle_data['current_node']
                path = vehicle_data['path']

                if current_node in path:
                    current_index = path.index(current_node)
                    if current_index < len(path) - 1:
                        next_node = path[current_index + 1]

                        # Get positions
                        current_pos = self.road_graph.nodes[current_node]
                        next_pos = self.road_graph.nodes[next_node]

                        # Calculate movement with consistent normalization
                        dx = (next_pos.get('x', 0) - current_pos.get('x', 0)) * self.scale_factor
                        dy = (next_pos.get('y', 0) - current_pos.get('y', 0)) * self.scale_factor

                        distance = math.sqrt(dx*dx + dy*dy)
                        if distance > 0.1:  # Minimum distance threshold
                            # Normalize direction
                            dx /= distance
                            dy /= distance

                            # Move vehicle (slower speed for better visibility)
                            speed_ms = vehicle_data['speed'] * dt * 0.1  # Reduced speed
                            new_x = vehicle_data['position'].x + dx * speed_ms
                            new_y = vehicle_data['position'].y + dy * speed_ms

                            new_pos = Point3(new_x, new_y, 0.5)  # Elevated for visibility
                            vehicle_data['position'] = new_pos

                            # Calculate heading
                            heading = math.atan2(dy, dx)

                            # Update 3D model
                            self.vehicles_3d[vehicle_id].update_position(new_pos, heading)

                            # Check if reached next node (appropriate threshold)
                            next_pos_3d = Point3(
                                (next_pos.get('x', 0) - self.x_center) * self.scale_factor,
                                (next_pos.get('y', 0) - self.y_center) * self.scale_factor,
                                0
                            )

                            if (new_pos - next_pos_3d).length() < 2.0:  # Appropriate threshold
                                vehicle_data['current_node'] = next_node

                                # Check if reached destination
                                if next_node == vehicle_data['destination_node']:
                                    vehicles_to_remove.append(vehicle_id)
                    else:
                        # Reached end of path
                        vehicles_to_remove.append(vehicle_id)
                else:
                    # Vehicle not on path, remove it
                    vehicles_to_remove.append(vehicle_id)
            else:
                # No valid path, remove vehicle
                vehicles_to_remove.append(vehicle_id)

        # Remove vehicles that reached destination
        for vehicle_id in vehicles_to_remove:
            self.remove_vehicle(vehicle_id)

    def remove_vehicle(self, vehicle_id):
        """Remove a vehicle from simulation"""
        if vehicle_id in self.vehicles_3d:
            self.vehicles_3d[vehicle_id].remove()
            del self.vehicles_3d[vehicle_id]

        if vehicle_id in self.active_vehicles:
            del self.active_vehicles[vehicle_id]

    def traffic_light_task(self, task):
        """Update traffic lights"""
        if not self.simulation_running:
            return task.cont

        # Simple traffic light cycling (30 seconds per cycle)
        cycle_time = 30.0
        phase_time = cycle_time / 3  # 10 seconds per phase

        current_phase = int(self.current_time / phase_time) % 3

        if current_phase == 0:
            state = "red"
        elif current_phase == 1:
            state = "yellow"
        else:
            state = "green"

        # Update all traffic lights
        for traffic_light in self.traffic_lights_3d:
            traffic_light.update_state(state)

        return task.cont

    def update_ui_task(self, task):
        """Update UI elements"""
        if not self.simulation_running:
            return task.cont

        # Update statistics
        stats_text = f"""
Simulation Time: {self.current_time:.1f}s
Active Vehicles: {len(self.active_vehicles)}
Speed: {self.simulation_speed:.1f}x
Weather: {self.weather_manager.current_weather.condition_type.name}
Emergencies: {len(self.emergency_manager.active_emergencies)}
        """.strip()

        self.stats_text.setText(stats_text)

        return task.cont

    # Camera control methods
    def move_camera_forward(self):
        self.camera.setY(self.camera, self.camera_speed)

    def move_camera_backward(self):
        self.camera.setY(self.camera, -self.camera_speed)

    def move_camera_left(self):
        self.camera.setX(self.camera, -self.camera_speed)

    def move_camera_right(self):
        self.camera.setX(self.camera, self.camera_speed)

    def move_camera_up(self):
        self.camera.setZ(self.camera, self.camera_speed)

    def move_camera_down(self):
        self.camera.setZ(self.camera, -self.camera_speed)

    def zoom_in(self):
        """Zoom in relative to current distance"""
        current_pos = self.camera.getPos()
        # Move camera closer by zoom_factor percentage
        zoom_distance = current_pos.length() * self.zoom_factor
        direction = current_pos.normalized()
        new_pos = current_pos - direction * zoom_distance
        # Prevent getting too close
        if new_pos.length() > 5.0:
            self.camera.setPos(new_pos)

    def zoom_out(self):
        """Zoom out relative to current distance"""
        current_pos = self.camera.getPos()
        # Move camera farther by zoom_factor percentage
        zoom_distance = current_pos.length() * self.zoom_factor
        direction = current_pos.normalized()
        new_pos = current_pos + direction * zoom_distance
        # Prevent getting too far
        if new_pos.length() < 1000.0:
            self.camera.setPos(new_pos)

    def start_mouse_rotation(self):
        """Start mouse rotation mode"""
        self.mouse_rotating = True
        if self.mouseWatcherNode.hasMouse():
            self.last_mouse_x = self.mouseWatcherNode.getMouseX()
            self.last_mouse_y = self.mouseWatcherNode.getMouseY()

    def stop_mouse_rotation(self):
        """Stop mouse rotation mode"""
        self.mouse_rotating = False

    def mouse_rotation_task(self, task):
        """Handle mouse rotation"""
        if self.mouse_rotating and self.mouseWatcherNode.hasMouse():
            mouse_x = self.mouseWatcherNode.getMouseX()
            mouse_y = self.mouseWatcherNode.getMouseY()

            # Calculate mouse movement
            dx = mouse_x - self.last_mouse_x
            dy = mouse_y - self.last_mouse_y

            # Update camera rotation
            self.camera_h -= dx * 100  # Horizontal rotation (yaw)
            self.camera_p += dy * 100  # Vertical rotation (pitch)

            # Clamp pitch to prevent flipping
            self.camera_p = max(-89, min(89, self.camera_p))

            # Apply rotation
            self.camera.setHpr(self.camera_h, self.camera_p, 0)

            # Update last mouse position
            self.last_mouse_x = mouse_x
            self.last_mouse_y = mouse_y

        return task.cont

    # Control methods
    def toggle_simulation(self):
        """Toggle simulation pause/resume"""
        self.simulation_running = not self.simulation_running
        print(
            f"Simulation {'resumed' if self.simulation_running else 'paused'}")

    def update_simulation_speed(self):
        """Update simulation speed from slider"""
        self.simulation_speed = self.speed_slider['value']

    def trigger_accident(self):
        """Trigger an accident emergency"""
        nodes = list(self.road_graph.nodes())
        if nodes:
            accident_node = random.choice(nodes)
            node_data = self.road_graph.nodes[accident_node]
            location = Point3D(
                x=node_data.get('x', 0),
                y=node_data.get('y', 0),
                z=0
            )

            self.emergency_manager.create_emergency_scenario(
                EmergencyType.ACCIDENT,
                location=location
            )
            print("Accident emergency triggered!")

    def trigger_flooding(self):
        """Trigger a flooding emergency"""
        nodes = list(self.road_graph.nodes())
        if nodes:
            flood_node = random.choice(nodes)
            node_data = self.road_graph.nodes[flood_node]
            location = Point3D(
                x=node_data.get('x', 0),
                y=node_data.get('y', 0),
                z=0
            )

            self.emergency_manager.create_emergency_scenario(
                EmergencyType.FLOODING,
                location=location
            )
            print("Flooding emergency triggered!")

    def run_console_simulation(self):
        """Run simulation in console mode when Panda3D is not available"""
        print("Running traffic simulation in console mode...")
        print("=" * 50)

        # Initialize systems
        self.setup_indian_traffic_system()

        # Run simulation loop
        self.current_time = 0.0
        dt = 1.0  # 1 second steps

        while self.current_time < 300:  # Run for 5 minutes
            # Spawn vehicles
            if len(self.active_vehicles) < self.traffic_config.max_vehicles and random.random() < 0.3:
                self.spawn_console_vehicle()

            # Update vehicles (simple console version)
            self.update_console_vehicles(dt)

            # Update time
            self.current_time += dt

            # Print status every 10 seconds
            if int(self.current_time) % 10 == 0:
                print(f"Time: {self.current_time:.0f}s | Vehicles: {len(self.active_vehicles)} | "
                      f"Emergencies: {len(self.emergency_manager.active_emergencies)}")

            time.sleep(0.1)  # Small delay for readability

        print("Console simulation completed!")

    def spawn_console_vehicle(self):
        """Spawn vehicle in console mode"""
        vehicle_id = f"console_vehicle_{self.vehicle_counter}"
        self.vehicle_counter += 1

        vehicle_type = self.select_vehicle_type()

        self.active_vehicles[vehicle_id] = {
            'type': vehicle_type,
            'spawn_time': self.current_time,
            'speed': random.uniform(20, 60)
        }

        print(f"Spawned {vehicle_type.name} (ID: {vehicle_id})")

    def update_console_vehicles(self, dt):
        """Update vehicles in console mode"""
        vehicles_to_remove = []

        for vehicle_id, vehicle_data in self.active_vehicles.items():
            # Simple aging - remove vehicles after 30 seconds
            age = self.current_time - vehicle_data['spawn_time']
            if age > 30:
                vehicles_to_remove.append(vehicle_id)

        for vehicle_id in vehicles_to_remove:
            print(f"Removed vehicle {vehicle_id}")
            del self.active_vehicles[vehicle_id]


def main():
    """Main function to run the traffic simulation"""
    print("Starting Full Indian Traffic Simulation...")
    print("=" * 50)

    if PANDA3D_AVAILABLE:
        print("Panda3D available - Starting 3D simulation")
        app = FullTrafficSimulation()
        app.run()
    else:
        print("Panda3D not available - Starting console simulation")
        sim = FullTrafficSimulation()


if __name__ == "__main__":
    main()
