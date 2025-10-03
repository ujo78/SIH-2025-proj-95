"""
Indian Vehicle Factory

This module implements the IndianVehicleFactory class for creating Indian vehicles
with specific characteristics and behavior parameters based on vehicle type.
"""

import random
from typing import Dict, Optional, List
from dataclasses import dataclass, field
import uuid

from .enums import VehicleType, BehaviorProfile, WeatherType, RoadQuality
from .interfaces import IndianVehicleInterface, Point3D
from .config import IndianTrafficConfig, VehicleConfig, BehaviorConfig


@dataclass
class BehaviorParameters:
    """Behavior parameters for a specific vehicle instance"""
    lane_discipline_factor: float  # 0.0 to 1.0
    overtaking_aggressiveness: float  # 0.0 to 1.0
    following_distance_factor: float  # multiplier for safe following distance
    speed_compliance: float  # 0.0 to 1.0 (adherence to speed limits)
    horn_usage_frequency: float  # times per minute
    traffic_light_compliance: float  # 0.0 to 1.0
    right_of_way_respect: float  # 0.0 to 1.0
    risk_tolerance: float  # 0.0 to 1.0 (higher = more risky behavior)


@dataclass
class IndianVehicle(IndianVehicleInterface):
    """Implementation of Indian vehicle with specific characteristics"""
    
    # Basic properties
    vehicle_id: str
    vehicle_type: VehicleType
    behavior_profile: BehaviorProfile
    
    # Physical characteristics
    length: float
    width: float
    height: float
    max_speed: float
    acceleration: float
    deceleration: float
    
    # Position and movement
    current_position: Point3D
    destination: Optional[Point3D] = None
    route: List[int] = field(default_factory=list)
    current_speed: float = 0.0
    heading: float = 0.0  # degrees
    
    # Behavior parameters
    behavior_params: BehaviorParameters = field(default_factory=lambda: BehaviorParameters(
        lane_discipline_factor=0.5,
        overtaking_aggressiveness=0.5,
        following_distance_factor=1.5,
        speed_compliance=0.8,
        horn_usage_frequency=2.0,
        traffic_light_compliance=0.8,
        right_of_way_respect=0.7,
        risk_tolerance=0.5
    ))
    
    # State tracking
    is_overtaking: bool = False
    time_since_last_horn: float = 0.0
    emergency_braking: bool = False
    
    def get_vehicle_type(self) -> VehicleType:
        """Get the type of this vehicle"""
        return self.vehicle_type
    
    def get_behavior_profile(self) -> BehaviorProfile:
        """Get the behavior profile of this vehicle"""
        return self.behavior_profile
    
    def get_lane_discipline_factor(self) -> float:
        """Get lane discipline factor (0.0 to 1.0)"""
        return self.behavior_params.lane_discipline_factor
    
    def update_position(self, new_position: Point3D) -> None:
        """Update vehicle position"""
        self.current_position = new_position
    
    def calculate_speed_adjustment(self, road_quality: RoadQuality, weather: WeatherType) -> float:
        """Calculate speed adjustment based on conditions"""
        # Base speed adjustment factors
        road_factors = {
            RoadQuality.EXCELLENT: 1.0,
            RoadQuality.GOOD: 0.9,
            RoadQuality.POOR: 0.7,
            RoadQuality.VERY_POOR: 0.5
        }
        
        weather_factors = {
            WeatherType.CLEAR: 1.0,
            WeatherType.LIGHT_RAIN: 0.8,
            WeatherType.HEAVY_RAIN: 0.5,
            WeatherType.FOG: 0.6,
            WeatherType.DUST_STORM: 0.4
        }
        
        # Apply vehicle-specific adjustments
        road_factor = road_factors.get(road_quality, 0.7)
        weather_factor = weather_factors.get(weather, 0.8)
        
        # Motorcycles and auto-rickshaws are more affected by poor conditions
        if self.vehicle_type in [VehicleType.MOTORCYCLE, VehicleType.AUTO_RICKSHAW]:
            road_factor *= 0.9
            weather_factor *= 0.8
        
        # Trucks and buses are less affected but more cautious
        elif self.vehicle_type in [VehicleType.TRUCK, VehicleType.BUS]:
            road_factor = max(road_factor, 0.6)  # Minimum speed maintenance
            weather_factor = max(weather_factor, 0.7)
        
        return road_factor * weather_factor
    
    def should_use_horn(self, traffic_density: float) -> bool:
        """Determine if vehicle should use horn based on behavior and conditions"""
        base_probability = self.behavior_params.horn_usage_frequency / 60.0  # per second
        
        # Increase probability with traffic density and aggressiveness
        adjusted_probability = base_probability * (1 + traffic_density) * (1 + self.behavior_params.overtaking_aggressiveness)
        
        # Auto-rickshaws and motorcycles use horn more frequently
        if self.vehicle_type in [VehicleType.AUTO_RICKSHAW, VehicleType.MOTORCYCLE]:
            adjusted_probability *= 1.5
        
        return random.random() < adjusted_probability
    
    def calculate_following_distance(self, leading_vehicle_speed: float) -> float:
        """Calculate safe following distance based on behavior and conditions"""
        # Base following distance (2-second rule)
        base_distance = leading_vehicle_speed * 2.0 / 3.6  # Convert km/h to m/s
        
        # Apply behavior factor
        adjusted_distance = base_distance * self.behavior_params.following_distance_factor
        
        # Motorcycles follow closer, trucks follow farther
        if self.vehicle_type == VehicleType.MOTORCYCLE:
            adjusted_distance *= 0.7
        elif self.vehicle_type in [VehicleType.TRUCK, VehicleType.BUS]:
            adjusted_distance *= 1.3
        
        return max(adjusted_distance, 2.0)  # Minimum 2 meters


class IndianVehicleFactory:
    """Factory class for creating Indian vehicles with appropriate characteristics"""
    
    def __init__(self, config: Optional[IndianTrafficConfig] = None):
        """Initialize the factory with configuration"""
        self.config = config or IndianTrafficConfig()
        self._vehicle_counter = 0
    
    def create_vehicle(self, vehicle_type: VehicleType, 
                      position: Point3D,
                      behavior_profile: Optional[BehaviorProfile] = None,
                      destination: Optional[Point3D] = None) -> IndianVehicle:
        """Create a vehicle of the specified type with Indian-specific characteristics"""
        
        # Get vehicle configuration
        vehicle_config = self.config.vehicle_configs[vehicle_type]
        
        # Determine behavior profile
        if behavior_profile is None:
            behavior_profile = vehicle_config.default_behavior_profile
        
        # Generate unique vehicle ID
        self._vehicle_counter += 1
        vehicle_id = f"{vehicle_type.name}_{self._vehicle_counter:06d}"
        
        # Create behavior parameters with some randomization
        behavior_params = self._generate_behavior_parameters(vehicle_type, behavior_profile, vehicle_config)
        
        # Create the vehicle
        vehicle = IndianVehicle(
            vehicle_id=vehicle_id,
            vehicle_type=vehicle_type,
            behavior_profile=behavior_profile,
            length=vehicle_config.length,
            width=vehicle_config.width,
            height=vehicle_config.height,
            max_speed=vehicle_config.max_speed,
            acceleration=vehicle_config.acceleration,
            deceleration=vehicle_config.deceleration,
            current_position=position,
            destination=destination,
            behavior_params=behavior_params
        )
        
        return vehicle
    
    def create_random_vehicle(self, position: Point3D, 
                            destination: Optional[Point3D] = None) -> IndianVehicle:
        """Create a random vehicle based on configured mix ratios"""
        
        # Select vehicle type based on mix ratios
        vehicle_type = self._select_random_vehicle_type()
        
        # Create vehicle with random behavior variation
        return self.create_vehicle(vehicle_type, position, destination=destination)
    
    def create_vehicle_batch(self, count: int, positions: List[Point3D],
                           destinations: Optional[List[Point3D]] = None) -> List[IndianVehicle]:
        """Create a batch of vehicles for efficient spawning"""
        
        vehicles = []
        dest_list = destinations or [None] * count
        
        for i in range(min(count, len(positions))):
            position = positions[i]
            destination = dest_list[i] if i < len(dest_list) else None
            vehicle = self.create_random_vehicle(position, destination)
            vehicles.append(vehicle)
        
        return vehicles
    
    def get_behavior_parameters(self, vehicle_type: VehicleType, 
                              behavior_profile: BehaviorProfile) -> BehaviorParameters:
        """Get behavior parameters for a specific vehicle type and profile"""
        vehicle_config = self.config.vehicle_configs[vehicle_type]
        return self._generate_behavior_parameters(vehicle_type, behavior_profile, vehicle_config)
    
    def _select_random_vehicle_type(self) -> VehicleType:
        """Select a random vehicle type based on configured mix ratios"""
        
        # Create cumulative probability distribution
        vehicle_types = list(self.config.vehicle_mix_ratios.keys())
        probabilities = list(self.config.vehicle_mix_ratios.values())
        
        # Normalize probabilities to ensure they sum to 1.0
        total_prob = sum(probabilities)
        if total_prob > 0:
            probabilities = [p / total_prob for p in probabilities]
        else:
            # Equal probability if no ratios configured
            probabilities = [1.0 / len(vehicle_types)] * len(vehicle_types)
        
        # Select based on random value
        rand_val = random.random()
        cumulative_prob = 0.0
        
        for vehicle_type, prob in zip(vehicle_types, probabilities):
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                return vehicle_type
        
        # Fallback to first vehicle type
        return vehicle_types[0] if vehicle_types else VehicleType.CAR
    
    def _generate_behavior_parameters(self, vehicle_type: VehicleType, 
                                    behavior_profile: BehaviorProfile,
                                    vehicle_config: VehicleConfig) -> BehaviorParameters:
        """Generate behavior parameters with appropriate randomization"""
        
        # Base parameters from configuration
        base_lane_discipline = self.config.behavior_config.lane_discipline_by_vehicle.get(vehicle_type, 0.5)
        base_overtaking = self.config.behavior_config.overtaking_aggressiveness.get(vehicle_type, 0.5)
        base_following = self.config.behavior_config.following_distance_factors.get(behavior_profile, 1.5)
        
        # Apply behavior profile modifiers
        profile_modifiers = {
            BehaviorProfile.CONSERVATIVE: {
                'lane_discipline': 1.2,
                'overtaking': 0.6,
                'following_distance': 1.3,
                'speed_compliance': 1.1,
                'risk_tolerance': 0.7
            },
            BehaviorProfile.NORMAL: {
                'lane_discipline': 1.0,
                'overtaking': 1.0,
                'following_distance': 1.0,
                'speed_compliance': 1.0,
                'risk_tolerance': 1.0
            },
            BehaviorProfile.AGGRESSIVE: {
                'lane_discipline': 0.8,
                'overtaking': 1.4,
                'following_distance': 0.8,
                'speed_compliance': 0.9,
                'risk_tolerance': 1.3
            },
            BehaviorProfile.ERRATIC: {
                'lane_discipline': 0.6,
                'overtaking': 1.2,
                'following_distance': 0.9,
                'speed_compliance': 0.7,
                'risk_tolerance': 1.5
            }
        }
        
        modifiers = profile_modifiers.get(behavior_profile, profile_modifiers[BehaviorProfile.NORMAL])
        
        # Add randomization (±20% variation)
        def randomize(value: float, variation: float = 0.2) -> float:
            factor = 1.0 + random.uniform(-variation, variation)
            return max(0.0, min(1.0, value * factor))
        
        return BehaviorParameters(
            lane_discipline_factor=randomize(base_lane_discipline * modifiers['lane_discipline']),
            overtaking_aggressiveness=randomize(base_overtaking * modifiers['overtaking']),
            following_distance_factor=max(0.5, base_following * modifiers['following_distance'] * random.uniform(0.8, 1.2)),
            speed_compliance=randomize(0.8 * modifiers['speed_compliance']),
            horn_usage_frequency=max(0.1, vehicle_config.horn_usage_frequency * random.uniform(0.5, 1.5)),
            traffic_light_compliance=randomize(vehicle_config.traffic_light_compliance),
            right_of_way_respect=randomize(vehicle_config.right_of_way_respect),
            risk_tolerance=randomize(0.5 * modifiers['risk_tolerance'])
        )
    
    def get_vehicle_statistics(self) -> Dict[str, any]:
        """Get statistics about created vehicles"""
        return {
            'total_vehicles_created': self._vehicle_counter,
            'configured_vehicle_types': list(self.config.vehicle_mix_ratios.keys()),
            'vehicle_mix_ratios': self.config.vehicle_mix_ratios
        }