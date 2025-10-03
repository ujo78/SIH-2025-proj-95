"""
Base Interfaces for Indian Traffic Components

This module defines abstract base classes and interfaces for Indian traffic
modeling components to ensure consistent implementation across the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import networkx as nx

from .enums import (
    VehicleType, RoadQuality, WeatherType, EmergencyType, 
    BehaviorProfile, IntersectionType, LaneDiscipline
)


@dataclass
class Point3D:
    """3D coordinate point"""
    x: float
    y: float
    z: float = 0.0


@dataclass
class TrajectoryPoint:
    """Point in vehicle trajectory with timestamp"""
    position: Point3D
    timestamp: float
    speed: float
    heading: float


class IndianVehicleInterface(ABC):
    """Interface for Indian vehicle implementations"""
    
    @abstractmethod
    def get_vehicle_type(self) -> VehicleType:
        """Get the type of this vehicle"""
        pass
    
    @abstractmethod
    def get_behavior_profile(self) -> BehaviorProfile:
        """Get the behavior profile of this vehicle"""
        pass
    
    @abstractmethod
    def get_lane_discipline_factor(self) -> float:
        """Get lane discipline factor (0.0 to 1.0)"""
        pass
    
    @abstractmethod
    def update_position(self, new_position: Point3D) -> None:
        """Update vehicle position"""
        pass
    
    @abstractmethod
    def calculate_speed_adjustment(self, road_quality: RoadQuality, weather: WeatherType) -> float:
        """Calculate speed adjustment based on conditions"""
        pass


class RoadConditionInterface(ABC):
    """Interface for road condition analysis"""
    
    @abstractmethod
    def analyze_road_quality(self, graph: nx.Graph) -> Dict[Tuple[int, int], RoadQuality]:
        """Analyze road quality for all edges in the graph"""
        pass
    
    @abstractmethod
    def detect_potholes(self, edge_data: Dict[str, Any]) -> List[Point3D]:
        """Detect potential pothole locations on a road segment"""
        pass
    
    @abstractmethod
    def identify_construction_zones(self, graph: nx.Graph) -> List[Dict[str, Any]]:
        """Identify construction zones in the road network"""
        pass
    
    @abstractmethod
    def update_dynamic_conditions(self, conditions: Dict[str, Any]) -> None:
        """Update dynamic road conditions"""
        pass


class BehaviorModelInterface(ABC):
    """Interface for driver behavior modeling"""
    
    @abstractmethod
    def calculate_lane_discipline(self, vehicle_type: VehicleType, road_conditions: Dict[str, Any]) -> LaneDiscipline:
        """Calculate lane discipline for given conditions"""
        pass
    
    @abstractmethod
    def determine_overtaking_probability(self, vehicle_type: VehicleType, traffic_density: float) -> float:
        """Determine probability of overtaking maneuver"""
        pass
    
    @abstractmethod
    def model_intersection_behavior(self, vehicle_type: VehicleType, intersection_type: IntersectionType) -> Dict[str, float]:
        """Model behavior at intersections"""
        pass
    
    @abstractmethod
    def apply_weather_effects(self, base_behavior: Dict[str, float], weather: WeatherType) -> Dict[str, float]:
        """Apply weather effects to behavior parameters"""
        pass


class EmergencyScenarioInterface(ABC):
    """Interface for emergency scenario handling"""
    
    @abstractmethod
    def create_emergency_scenario(self, emergency_type: EmergencyType, location: Point3D) -> Dict[str, Any]:
        """Create an emergency scenario"""
        pass
    
    @abstractmethod
    def calculate_impact_area(self, scenario: Dict[str, Any]) -> List[Tuple[int, int]]:
        """Calculate which road segments are affected"""
        pass
    
    @abstractmethod
    def generate_alternative_routes(self, affected_edges: List[Tuple[int, int]], graph: nx.Graph) -> List[List[int]]:
        """Generate alternative routes around affected areas"""
        pass