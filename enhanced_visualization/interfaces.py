"""
Interfaces for Enhanced Visualization Components

This module defines abstract interfaces for 3D city rendering, vehicle asset management,
and traffic flow visualization extending the existing Panda3D implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import networkx as nx

from indian_features.enums import VehicleType, WeatherType, RoadQuality, EmergencyType
from indian_features.interfaces import Point3D


@dataclass
class BuildingInfo:
    """Information about a building for 3D rendering"""
    building_id: str
    footprint: List[Point3D]
    height: float
    building_type: str
    texture_type: Optional[str] = None


@dataclass
class RoadSegmentVisual:
    """Visual representation data for road segments"""
    segment_id: str
    geometry: List[Point3D]
    width: float
    road_quality: RoadQuality
    surface_type: str
    lane_markings: List[Dict[str, Any]]
    potholes: List[Point3D]
    construction_zones: List[Dict[str, Any]]


@dataclass
class VehicleVisual:
    """Visual representation data for vehicles"""
    vehicle_id: int
    vehicle_type: VehicleType
    position: Point3D
    heading: float
    speed: float
    model_path: str
    scale: float = 1.0
    color: Optional[Tuple[float, float, float]] = None


class CityRendererInterface(ABC):
    """Interface for rendering Indian city environments in 3D"""
    
    @abstractmethod
    def initialize_scene(self, bounds: Tuple[float, float, float, float]) -> None:
        """Initialize 3D scene with given geographic bounds"""
        pass
    
    @abstractmethod
    def render_buildings(self, buildings: List[BuildingInfo]) -> None:
        """Render building models in the scene"""
        pass
    
    @abstractmethod
    def render_road_infrastructure(self, road_segments: List[RoadSegmentVisual]) -> None:
        """Render road infrastructure including potholes and construction"""
        pass
    
    @abstractmethod
    def add_terrain(self, elevation_data: Optional[Dict[str, Any]] = None) -> None:
        """Add terrain/ground plane to the scene"""
        pass
    
    @abstractmethod
    def update_lighting(self, time_of_day: float, weather: WeatherType) -> None:
        """Update scene lighting based on time and weather"""
        pass
    
    @abstractmethod
    def add_environmental_effects(self, weather: WeatherType, intensity: float) -> None:
        """Add weather effects like rain, fog, or dust"""
        pass
    
    @abstractmethod
    def show_construction_zones(self, zones: List[Dict[str, Any]]) -> None:
        """Visualize construction zones with barriers and signage"""
        pass


class VehicleAssetInterface(ABC):
    """Interface for managing 3D vehicle assets and animations"""
    
    @abstractmethod
    def load_vehicle_models(self) -> Dict[VehicleType, str]:
        """Load 3D models for different Indian vehicle types"""
        pass
    
    @abstractmethod
    def create_vehicle_instance(self, vehicle: VehicleVisual) -> Any:
        """Create a 3D instance of a vehicle in the scene"""
        pass
    
    @abstractmethod
    def update_vehicle_position(self, vehicle_id: int, position: Point3D, heading: float) -> None:
        """Update vehicle position and orientation"""
        pass
    
    @abstractmethod
    def animate_vehicle_movement(self, vehicle_id: int, path: List[Point3D], duration: float) -> None:
        """Animate vehicle movement along a path"""
        pass
    
    @abstractmethod
    def show_vehicle_interactions(self, interactions: List[Dict[str, Any]]) -> None:
        """Visualize vehicle interactions (overtaking, following, etc.)"""
        pass
    
    @abstractmethod
    def remove_vehicle(self, vehicle_id: int) -> None:
        """Remove vehicle from the scene"""
        pass
    
    @abstractmethod
    def set_vehicle_visibility(self, vehicle_id: int, visible: bool) -> None:
        """Set vehicle visibility in the scene"""
        pass


class TrafficVisualizerInterface(ABC):
    """Interface for visualizing traffic flow and congestion"""
    
    @abstractmethod
    def initialize_traffic_overlay(self, road_network: nx.Graph) -> None:
        """Initialize traffic flow visualization overlay"""
        pass
    
    @abstractmethod
    def update_traffic_density(self, edge_densities: Dict[Tuple[int, int], float]) -> None:
        """Update traffic density visualization on road segments"""
        pass
    
    @abstractmethod
    def show_congestion_hotspots(self, hotspots: List[Dict[str, Any]]) -> None:
        """Highlight congestion hotspots in the visualization"""
        pass
    
    @abstractmethod
    def display_emergency_alerts(self, emergencies: List[Dict[str, Any]]) -> None:
        """Display emergency scenario alerts and affected areas"""
        pass
    
    @abstractmethod
    def show_route_alternatives(self, original_route: List[int], alternatives: List[List[int]]) -> None:
        """Visualize original and alternative routes"""
        pass
    
    @abstractmethod
    def create_traffic_flow_animation(self, flow_data: Dict[str, Any]) -> None:
        """Create animated visualization of traffic flow patterns"""
        pass
    
    @abstractmethod
    def add_performance_indicators(self, metrics: Dict[str, float]) -> None:
        """Add real-time performance indicators to the display"""
        pass


class CameraControlInterface(ABC):
    """Interface for advanced camera controls and scene navigation"""
    
    @abstractmethod
    def set_camera_position(self, position: Point3D, target: Point3D) -> None:
        """Set camera position and target"""
        pass
    
    @abstractmethod
    def create_smooth_transition(self, start_pos: Point3D, end_pos: Point3D, duration: float) -> None:
        """Create smooth camera transition between positions"""
        pass
    
    @abstractmethod
    def follow_vehicle(self, vehicle_id: int, offset: Point3D) -> None:
        """Set camera to follow a specific vehicle"""
        pass
    
    @abstractmethod
    def set_preset_view(self, preset_name: str) -> None:
        """Switch to a predefined camera preset"""
        pass
    
    @abstractmethod
    def enable_free_camera(self, enable: bool) -> None:
        """Enable/disable free camera movement"""
        pass
    
    @abstractmethod
    def create_cinematic_path(self, waypoints: List[Point3D], duration: float) -> None:
        """Create cinematic camera path through waypoints"""
        pass


class UIOverlayInterface(ABC):
    """Interface for user interface overlays and controls"""
    
    @abstractmethod
    def create_simulation_controls(self) -> None:
        """Create simulation control UI (play, pause, speed, etc.)"""
        pass
    
    @abstractmethod
    def add_information_panel(self, panel_data: Dict[str, Any]) -> None:
        """Add information panel with simulation statistics"""
        pass
    
    @abstractmethod
    def show_vehicle_details(self, vehicle_id: int, details: Dict[str, Any]) -> None:
        """Show detailed information about a selected vehicle"""
        pass
    
    @abstractmethod
    def display_road_conditions(self, segment_id: str, conditions: Dict[str, Any]) -> None:
        """Display road condition information for a segment"""
        pass
    
    @abstractmethod
    def create_scenario_selector(self, scenarios: List[str]) -> None:
        """Create UI for selecting simulation scenarios"""
        pass
    
    @abstractmethod
    def add_weather_controls(self, weather_options: List[WeatherType]) -> None:
        """Add weather control interface"""
        pass
    
    @abstractmethod
    def show_emergency_controls(self, emergency_types: List[EmergencyType]) -> None:
        """Show controls for triggering emergency scenarios"""
        pass