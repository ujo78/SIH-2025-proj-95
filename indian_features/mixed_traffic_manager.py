"""
Mixed Traffic Manager

This module manages interactions between different vehicle types in Indian traffic,
including priority handling, congestion behavior, and mixed vehicle dynamics.
"""

import math
import random
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import heapq

from .enums import VehicleType, EmergencyType, SeverityLevel, BehaviorProfile
from .interfaces import Point3D
from .vehicle_factory import IndianVehicle, BehaviorParameters
from .behavior_model import IndianBehaviorModel, TrafficState, OvertakeDecision


class VehiclePriority(Enum):
    """Priority levels for different vehicle types"""
    EMERGENCY = 1
    BUS = 2
    TRUCK = 3
    CAR = 4
    AUTO_RICKSHAW = 5
    MOTORCYCLE = 6
    BICYCLE = 7


@dataclass
class VehicleInteraction:
    """Represents an interaction between two vehicles"""
    primary_vehicle_id: str
    secondary_vehicle_id: str
    interaction_type: str  # 'overtaking', 'following', 'merging', 'blocking'
    distance: float  # meters
    relative_speed: float  # km/h (positive = primary faster)
    priority_difference: int  # priority levels difference
    conflict_severity: float  # 0.0 to 1.0


@dataclass
class CongestionZone:
    """Represents a congestion zone in the traffic network"""
    center_point: Point3D
    radius: float  # meters
    severity: float  # 0.0 to 1.0
    vehicle_count: int
    average_speed: float  # km/h
    density: float  # vehicles per km
    formation_time: float  # simulation time when formed
    

@dataclass
class EmergencyVehicle:
    """Special handling for emergency vehicles"""
    vehicle_id: str
    emergency_type: EmergencyType
    priority_level: int
    siren_range: float  # meters
    route_clearance_needed: bool


class MixedTrafficManager:
    """Manages interactions and behavior in mixed Indian traffic"""
    
    def __init__(self, behavior_model: Optional[IndianBehaviorModel] = None):
        """Initialize the mixed traffic manager"""
        self.behavior_model = behavior_model or IndianBehaviorModel()
        
        # Vehicle tracking
        self.active_vehicles: Dict[str, IndianVehicle] = {}
        self.vehicle_positions: Dict[str, Point3D] = {}
        self.vehicle_interactions: List[VehicleInteraction] = []
        
        # Priority system
        self.vehicle_priorities = {
            VehicleType.BUS: VehiclePriority.BUS,
            VehicleType.TRUCK: VehiclePriority.TRUCK,
            VehicleType.CAR: VehiclePriority.CAR,
            VehicleType.AUTO_RICKSHAW: VehiclePriority.AUTO_RICKSHAW,
            VehicleType.MOTORCYCLE: VehiclePriority.MOTORCYCLE,
            VehicleType.BICYCLE: VehiclePriority.BICYCLE
        }
        
        # Emergency vehicles
        self.emergency_vehicles: Dict[str, EmergencyVehicle] = {}
        
        # Congestion management
        self.congestion_zones: List[CongestionZone] = []
        self.congestion_threshold = 0.7  # density threshold for congestion
        
        # Interaction rules
        self.interaction_rules = self._initialize_interaction_rules()
        
        # Performance tracking
        self.interaction_count = 0
        self.congestion_events = 0
    
    def register_vehicle(self, vehicle: IndianVehicle) -> None:
        """Register a vehicle with the traffic manager"""
        self.active_vehicles[vehicle.vehicle_id] = vehicle
        self.vehicle_positions[vehicle.vehicle_id] = vehicle.current_position
    
    def unregister_vehicle(self, vehicle_id: str) -> None:
        """Remove a vehicle from the traffic manager"""
        if vehicle_id in self.active_vehicles:
            del self.active_vehicles[vehicle_id]
        if vehicle_id in self.vehicle_positions:
            del self.vehicle_positions[vehicle_id]
        if vehicle_id in self.emergency_vehicles:
            del self.emergency_vehicles[vehicle_id]
    
    def register_emergency_vehicle(self, vehicle: IndianVehicle, 
                                 emergency_type: EmergencyType,
                                 siren_range: float = 100.0) -> None:
        """Register an emergency vehicle with special handling"""
        self.register_vehicle(vehicle)
        
        emergency_vehicle = EmergencyVehicle(
            vehicle_id=vehicle.vehicle_id,
            emergency_type=emergency_type,
            priority_level=VehiclePriority.EMERGENCY.value,
            siren_range=siren_range,
            route_clearance_needed=True
        )
        
        self.emergency_vehicles[vehicle.vehicle_id] = emergency_vehicle
    
    def update_vehicle_position(self, vehicle_id: str, new_position: Point3D) -> None:
        """Update vehicle position and trigger interaction analysis"""
        if vehicle_id in self.vehicle_positions:
            self.vehicle_positions[vehicle_id] = new_position
            
            # Update vehicle object
            if vehicle_id in self.active_vehicles:
                self.active_vehicles[vehicle_id].update_position(new_position)
    
    def analyze_vehicle_interactions(self, interaction_radius: float = 50.0) -> List[VehicleInteraction]:
        """Analyze interactions between vehicles within specified radius"""
        interactions = []
        vehicle_ids = list(self.active_vehicles.keys())
        
        for i, vehicle_id_1 in enumerate(vehicle_ids):
            for vehicle_id_2 in vehicle_ids[i+1:]:
                interaction = self._analyze_pair_interaction(
                    vehicle_id_1, vehicle_id_2, interaction_radius
                )
                if interaction:
                    interactions.append(interaction)
        
        self.vehicle_interactions = interactions
        self.interaction_count += len(interactions)
        
        return interactions
    
    def handle_vehicle_priority(self, vehicle_interactions: List[VehicleInteraction]) -> Dict[str, Dict[str, Any]]:
        """Handle priority-based vehicle interactions"""
        priority_actions = {}
        
        for interaction in vehicle_interactions:
            primary_vehicle = self.active_vehicles.get(interaction.primary_vehicle_id)
            secondary_vehicle = self.active_vehicles.get(interaction.secondary_vehicle_id)
            
            if not primary_vehicle or not secondary_vehicle:
                continue
            
            # Determine priority
            primary_priority = self._get_vehicle_priority(primary_vehicle)
            secondary_priority = self._get_vehicle_priority(secondary_vehicle)
            
            # Handle emergency vehicles
            if interaction.primary_vehicle_id in self.emergency_vehicles:
                action = self._handle_emergency_vehicle_interaction(
                    interaction.primary_vehicle_id, interaction.secondary_vehicle_id
                )
                priority_actions[interaction.secondary_vehicle_id] = action
            
            elif interaction.secondary_vehicle_id in self.emergency_vehicles:
                action = self._handle_emergency_vehicle_interaction(
                    interaction.secondary_vehicle_id, interaction.primary_vehicle_id
                )
                priority_actions[interaction.primary_vehicle_id] = action
            
            # Handle bus priority
            elif primary_vehicle.vehicle_type == VehicleType.BUS and secondary_vehicle.vehicle_type != VehicleType.BUS:
                action = self._handle_bus_priority(interaction)
                priority_actions[interaction.secondary_vehicle_id] = action
            
            elif secondary_vehicle.vehicle_type == VehicleType.BUS and primary_vehicle.vehicle_type != VehicleType.BUS:
                action = self._handle_bus_priority(interaction, reverse=True)
                priority_actions[interaction.primary_vehicle_id] = action
            
            # Handle general priority interactions
            elif primary_priority.value < secondary_priority.value:
                action = self._handle_priority_interaction(interaction, primary_has_priority=True)
                priority_actions[interaction.secondary_vehicle_id] = action
            
            elif secondary_priority.value < primary_priority.value:
                action = self._handle_priority_interaction(interaction, primary_has_priority=False)
                priority_actions[interaction.primary_vehicle_id] = action
        
        return priority_actions
    
    def detect_congestion_zones(self, grid_size: float = 100.0) -> List[CongestionZone]:
        """Detect areas of traffic congestion"""
        # Create spatial grid for analysis
        vehicle_grid = self._create_spatial_grid(grid_size)
        
        congestion_zones = []
        
        for grid_cell, vehicles_in_cell in vehicle_grid.items():
            if len(vehicles_in_cell) < 3:  # Need minimum vehicles for congestion
                continue
            
            # Calculate congestion metrics
            center_x = sum(pos.x for pos in vehicles_in_cell) / len(vehicles_in_cell)
            center_y = sum(pos.y for pos in vehicles_in_cell) / len(vehicles_in_cell)
            center_point = Point3D(center_x, center_y, 0)
            
            # Calculate average speed and density
            total_speed = 0
            vehicle_count = len(vehicles_in_cell)
            
            for pos in vehicles_in_cell:
                # Find corresponding vehicle
                for vehicle_id, vehicle_pos in self.vehicle_positions.items():
                    if self._calculate_distance(pos, vehicle_pos) < 1.0:  # Same position
                        vehicle = self.active_vehicles.get(vehicle_id)
                        if vehicle:
                            total_speed += vehicle.current_speed
                        break
            
            average_speed = total_speed / vehicle_count if vehicle_count > 0 else 0
            density = vehicle_count / (grid_size * grid_size / 1000000)  # vehicles per km²
            
            # Determine congestion severity
            severity = self._calculate_congestion_severity(average_speed, density, vehicle_count)
            
            if severity > self.congestion_threshold:
                congestion_zone = CongestionZone(
                    center_point=center_point,
                    radius=grid_size / 2,
                    severity=severity,
                    vehicle_count=vehicle_count,
                    average_speed=average_speed,
                    density=density,
                    formation_time=0.0  # Would be set by simulation time
                )
                congestion_zones.append(congestion_zone)
        
        self.congestion_zones = congestion_zones
        self.congestion_events += len(congestion_zones)
        
        return congestion_zones
    
    def apply_congestion_behavior(self, congestion_zones: List[CongestionZone]) -> Dict[str, Dict[str, Any]]:
        """Apply congestion-specific behavior modifications"""
        behavior_modifications = {}
        
        for vehicle_id, vehicle in self.active_vehicles.items():
            vehicle_pos = self.vehicle_positions.get(vehicle_id)
            if not vehicle_pos:
                continue
            
            # Check if vehicle is in any congestion zone
            in_congestion = False
            congestion_severity = 0.0
            
            for zone in congestion_zones:
                distance = self._calculate_distance(vehicle_pos, zone.center_point)
                if distance <= zone.radius:
                    in_congestion = True
                    congestion_severity = max(congestion_severity, zone.severity)
            
            if in_congestion:
                modifications = self._generate_congestion_behavior_modifications(
                    vehicle, congestion_severity
                )
                behavior_modifications[vehicle_id] = modifications
        
        return behavior_modifications
    
    def simulate_mixed_vehicle_dynamics(self, time_step: float) -> Dict[str, Any]:
        """Simulate dynamics specific to mixed Indian traffic"""
        
        # Analyze current interactions
        interactions = self.analyze_vehicle_interactions()
        
        # Handle priority-based interactions
        priority_actions = self.handle_vehicle_priority(interactions)
        
        # Detect and handle congestion
        congestion_zones = self.detect_congestion_zones()
        congestion_behaviors = self.apply_congestion_behavior(congestion_zones)
        
        # Apply motorcycle and auto-rickshaw weaving behavior
        weaving_behaviors = self._simulate_weaving_behavior()
        
        # Handle horn usage and communication
        horn_events = self._simulate_horn_usage()
        
        # Combine all behaviors
        combined_behaviors = {}
        for vehicle_id in self.active_vehicles.keys():
            vehicle_behavior = {}
            
            if vehicle_id in priority_actions:
                vehicle_behavior.update(priority_actions[vehicle_id])
            
            if vehicle_id in congestion_behaviors:
                vehicle_behavior.update(congestion_behaviors[vehicle_id])
            
            if vehicle_id in weaving_behaviors:
                vehicle_behavior.update(weaving_behaviors[vehicle_id])
            
            if vehicle_behavior:
                combined_behaviors[vehicle_id] = vehicle_behavior
        
        return {
            'vehicle_behaviors': combined_behaviors,
            'interactions': interactions,
            'congestion_zones': congestion_zones,
            'horn_events': horn_events,
            'statistics': self.get_traffic_statistics()
        }
    
    def get_traffic_statistics(self) -> Dict[str, Any]:
        """Get current traffic statistics"""
        vehicle_type_counts = {}
        total_vehicles = len(self.active_vehicles)
        
        for vehicle in self.active_vehicles.values():
            vehicle_type = vehicle.vehicle_type
            vehicle_type_counts[vehicle_type.name] = vehicle_type_counts.get(vehicle_type.name, 0) + 1
        
        return {
            'total_vehicles': total_vehicles,
            'vehicle_type_distribution': vehicle_type_counts,
            'emergency_vehicles': len(self.emergency_vehicles),
            'active_interactions': len(self.vehicle_interactions),
            'congestion_zones': len(self.congestion_zones),
            'total_interactions_processed': self.interaction_count,
            'total_congestion_events': self.congestion_events
        }
    
    def _initialize_interaction_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize rules for vehicle interactions"""
        return {
            'emergency_clearance': {
                'clearance_distance': 20.0,  # meters
                'speed_reduction': 0.5,
                'lane_change_probability': 0.9
            },
            'bus_priority': {
                'yield_distance': 10.0,  # meters
                'speed_adjustment': 0.8,
                'lane_change_probability': 0.6
            },
            'motorcycle_weaving': {
                'weaving_probability': 0.3,  # per time step
                'lateral_movement': 0.5,  # meters
                'speed_advantage': 1.2
            },
            'truck_blocking': {
                'blocking_effect': 0.7,  # speed reduction for vehicles behind
                'overtaking_difficulty': 1.5,
                'following_distance_increase': 1.3
            }
        }
    
    def _analyze_pair_interaction(self, vehicle_id_1: str, vehicle_id_2: str, 
                                max_distance: float) -> Optional[VehicleInteraction]:
        """Analyze interaction between two specific vehicles"""
        
        pos_1 = self.vehicle_positions.get(vehicle_id_1)
        pos_2 = self.vehicle_positions.get(vehicle_id_2)
        vehicle_1 = self.active_vehicles.get(vehicle_id_1)
        vehicle_2 = self.active_vehicles.get(vehicle_id_2)
        
        if not all([pos_1, pos_2, vehicle_1, vehicle_2]):
            return None
        
        # Calculate distance
        distance = self._calculate_distance(pos_1, pos_2)
        
        if distance > max_distance:
            return None
        
        # Calculate relative speed
        relative_speed = vehicle_1.current_speed - vehicle_2.current_speed
        
        # Determine interaction type
        interaction_type = self._determine_interaction_type(
            vehicle_1, vehicle_2, distance, relative_speed
        )
        
        # Calculate priority difference
        priority_1 = self._get_vehicle_priority(vehicle_1)
        priority_2 = self._get_vehicle_priority(vehicle_2)
        priority_diff = priority_1.value - priority_2.value
        
        # Calculate conflict severity
        conflict_severity = self._calculate_conflict_severity(
            distance, relative_speed, vehicle_1.vehicle_type, vehicle_2.vehicle_type
        )
        
        return VehicleInteraction(
            primary_vehicle_id=vehicle_id_1,
            secondary_vehicle_id=vehicle_id_2,
            interaction_type=interaction_type,
            distance=distance,
            relative_speed=relative_speed,
            priority_difference=priority_diff,
            conflict_severity=conflict_severity
        )
    
    def _get_vehicle_priority(self, vehicle: IndianVehicle) -> VehiclePriority:
        """Get priority level for a vehicle"""
        if vehicle.vehicle_id in self.emergency_vehicles:
            return VehiclePriority.EMERGENCY
        
        return self.vehicle_priorities.get(vehicle.vehicle_type, VehiclePriority.CAR)
    
    def _handle_emergency_vehicle_interaction(self, emergency_id: str, 
                                            other_id: str) -> Dict[str, Any]:
        """Handle interaction with emergency vehicle"""
        rules = self.interaction_rules['emergency_clearance']
        
        return {
            'action_type': 'emergency_yield',
            'speed_adjustment': rules['speed_reduction'],
            'lane_change_required': random.random() < rules['lane_change_probability'],
            'clearance_distance': rules['clearance_distance'],
            'priority': 'emergency'
        }
    
    def _handle_bus_priority(self, interaction: VehicleInteraction, 
                           reverse: bool = False) -> Dict[str, Any]:
        """Handle bus priority interactions"""
        rules = self.interaction_rules['bus_priority']
        
        return {
            'action_type': 'bus_yield',
            'speed_adjustment': rules['speed_adjustment'],
            'lane_change_suggested': random.random() < rules['lane_change_probability'],
            'yield_distance': rules['yield_distance'],
            'priority': 'bus'
        }
    
    def _handle_priority_interaction(self, interaction: VehicleInteraction, 
                                   primary_has_priority: bool) -> Dict[str, Any]:
        """Handle general priority-based interactions"""
        
        if primary_has_priority:
            return {
                'action_type': 'yield_to_priority',
                'speed_adjustment': 0.9,
                'following_distance_increase': 1.2,
                'overtaking_discouraged': True
            }
        else:
            return {
                'action_type': 'assert_priority',
                'speed_adjustment': 1.0,
                'overtaking_encouraged': True,
                'gap_acceptance_reduced': 0.8
            }
    
    def _create_spatial_grid(self, grid_size: float) -> Dict[Tuple[int, int], List[Point3D]]:
        """Create spatial grid for congestion analysis"""
        grid = {}
        
        for vehicle_id, position in self.vehicle_positions.items():
            grid_x = int(position.x // grid_size)
            grid_y = int(position.y // grid_size)
            grid_key = (grid_x, grid_y)
            
            if grid_key not in grid:
                grid[grid_key] = []
            
            grid[grid_key].append(position)
        
        return grid
    
    def _calculate_congestion_severity(self, average_speed: float, 
                                     density: float, vehicle_count: int) -> float:
        """Calculate congestion severity based on traffic metrics"""
        
        # Speed factor (lower speed = higher congestion)
        speed_factor = max(0, 1.0 - (average_speed / 50.0))  # Normalize to 50 km/h
        
        # Density factor (higher density = higher congestion)
        density_factor = min(1.0, density / 100.0)  # Normalize to 100 vehicles/km²
        
        # Count factor (more vehicles = higher congestion)
        count_factor = min(1.0, vehicle_count / 20.0)  # Normalize to 20 vehicles
        
        # Weighted combination
        severity = (speed_factor * 0.4 + density_factor * 0.4 + count_factor * 0.2)
        
        return min(1.0, severity)
    
    def _generate_congestion_behavior_modifications(self, vehicle: IndianVehicle, 
                                                  severity: float) -> Dict[str, Any]:
        """Generate behavior modifications for congested conditions"""
        
        modifications = {
            'action_type': 'congestion_behavior',
            'speed_reduction': severity * 0.5,
            'following_distance_increase': 1.0 + severity * 0.5,
            'lane_change_frequency_increase': severity * 2.0,
            'horn_usage_increase': severity * 1.5,
            'stress_level_increase': severity * 0.3
        }
        
        # Vehicle-specific adjustments
        if vehicle.vehicle_type in [VehicleType.MOTORCYCLE, VehicleType.AUTO_RICKSHAW]:
            modifications['weaving_increase'] = severity * 1.5
            modifications['gap_acceptance_decrease'] = severity * 0.3
        
        elif vehicle.vehicle_type in [VehicleType.BUS, VehicleType.TRUCK]:
            modifications['blocking_effect'] = severity * 0.8
            modifications['lane_change_difficulty'] = severity * 1.2
        
        return modifications
    
    def _simulate_weaving_behavior(self) -> Dict[str, Dict[str, Any]]:
        """Simulate weaving behavior for motorcycles and auto-rickshaws"""
        weaving_behaviors = {}
        
        for vehicle_id, vehicle in self.active_vehicles.items():
            if vehicle.vehicle_type not in [VehicleType.MOTORCYCLE, VehicleType.AUTO_RICKSHAW]:
                continue
            
            rules = self.interaction_rules['motorcycle_weaving']
            
            if random.random() < rules['weaving_probability']:
                weaving_behaviors[vehicle_id] = {
                    'action_type': 'weaving',
                    'lateral_movement': rules['lateral_movement'] * random.uniform(-1, 1),
                    'speed_advantage': rules['speed_advantage'],
                    'lane_discipline_reduction': 0.5
                }
        
        return weaving_behaviors
    
    def _simulate_horn_usage(self) -> List[Dict[str, Any]]:
        """Simulate horn usage events"""
        horn_events = []
        
        for vehicle_id, vehicle in self.active_vehicles.items():
            # Check if vehicle should use horn based on behavior and conditions
            traffic_density = len(self.active_vehicles) / 100.0  # Simplified density
            
            if vehicle.should_use_horn(traffic_density):
                horn_events.append({
                    'vehicle_id': vehicle_id,
                    'vehicle_type': vehicle.vehicle_type.name,
                    'position': self.vehicle_positions.get(vehicle_id),
                    'reason': self._determine_horn_reason(vehicle_id)
                })
        
        return horn_events
    
    def _determine_horn_reason(self, vehicle_id: str) -> str:
        """Determine reason for horn usage"""
        reasons = ['overtaking', 'frustration', 'warning', 'greeting', 'clearing_path']
        return random.choice(reasons)
    
    def _calculate_distance(self, pos1: Point3D, pos2: Point3D) -> float:
        """Calculate Euclidean distance between two points"""
        return math.sqrt((pos1.x - pos2.x)**2 + (pos1.y - pos2.y)**2)
    
    def _determine_interaction_type(self, vehicle1: IndianVehicle, vehicle2: IndianVehicle,
                                  distance: float, relative_speed: float) -> str:
        """Determine the type of interaction between vehicles"""
        
        if abs(relative_speed) > 10:  # Significant speed difference
            if relative_speed > 0:
                return 'overtaking'
            else:
                return 'being_overtaken'
        
        elif distance < 10:  # Very close
            if abs(relative_speed) < 2:
                return 'following'
            else:
                return 'conflict'
        
        elif distance < 30:  # Moderate distance
            return 'proximity'
        
        else:
            return 'distant'
    
    def _calculate_conflict_severity(self, distance: float, relative_speed: float,
                                   type1: VehicleType, type2: VehicleType) -> float:
        """Calculate severity of potential conflict"""
        
        # Distance factor (closer = higher severity)
        distance_factor = max(0, 1.0 - (distance / 50.0))
        
        # Speed factor (higher relative speed = higher severity)
        speed_factor = min(1.0, abs(relative_speed) / 30.0)
        
        # Vehicle type factor (size mismatch = higher severity)
        size_mismatch = abs(self._get_vehicle_size_factor(type1) - self._get_vehicle_size_factor(type2))
        
        severity = (distance_factor * 0.5 + speed_factor * 0.3 + size_mismatch * 0.2)
        
        return min(1.0, severity)
    
    def _get_vehicle_size_factor(self, vehicle_type: VehicleType) -> float:
        """Get relative size factor for vehicle type"""
        size_factors = {
            VehicleType.BICYCLE: 0.1,
            VehicleType.MOTORCYCLE: 0.2,
            VehicleType.AUTO_RICKSHAW: 0.4,
            VehicleType.CAR: 0.6,
            VehicleType.BUS: 0.9,
            VehicleType.TRUCK: 1.0
        }
        
        return size_factors.get(vehicle_type, 0.5)