"""
Configuration Classes for Indian Traffic Features

This module defines configuration classes for vehicle types, road conditions,
and behavior parameters specific to Indian traffic scenarios.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from .enums import (
    VehicleType, RoadQuality, WeatherType, BehaviorProfile, 
    SurfaceType, MaintenanceLevel, ConstructionStatus
)


@dataclass
class VehicleConfig:
    """Configuration for Indian vehicle types"""
    
    # Vehicle physical characteristics
    length: float  # meters
    width: float   # meters
    height: float  # meters
    max_speed: float  # km/h
    acceleration: float  # m/s²
    deceleration: float  # m/s²
    
    # Behavior characteristics
    default_behavior_profile: BehaviorProfile
    lane_discipline_base: float  # 0.0 to 1.0
    overtaking_aggressiveness: float  # 0.0 to 1.0
    following_distance_factor: float  # multiplier for safe following distance
    
    # Indian-specific attributes
    horn_usage_frequency: float  # times per minute
    traffic_light_compliance: float  # 0.0 to 1.0
    right_of_way_respect: float  # 0.0 to 1.0


@dataclass
class RoadConditionConfig:
    """Configuration for road condition parameters"""
    
    # Quality scoring weights
    surface_type_weights: Dict[SurfaceType, float] = field(default_factory=lambda: {
        SurfaceType.ASPHALT: 1.0,
        SurfaceType.CONCRETE: 0.9,
        SurfaceType.GRAVEL: 0.6,
        SurfaceType.DIRT: 0.3,
        SurfaceType.COBBLESTONE: 0.7
    })
    
    maintenance_weights: Dict[MaintenanceLevel, float] = field(default_factory=lambda: {
        MaintenanceLevel.WELL_MAINTAINED: 1.0,
        MaintenanceLevel.MODERATELY_MAINTAINED: 0.8,
        MaintenanceLevel.POORLY_MAINTAINED: 0.5,
        MaintenanceLevel.UNMAINTAINED: 0.2
    })
    
    # Pothole detection parameters
    pothole_probability_by_age: Dict[int, float] = field(default_factory=lambda: {
        0: 0.01,   # new roads
        5: 0.05,   # 5 years old
        10: 0.15,  # 10 years old
        15: 0.30,  # 15 years old
        20: 0.50   # 20+ years old
    })
    
    # Construction zone parameters
    construction_speed_reduction: float = 0.5  # factor to reduce speed
    construction_lane_reduction: int = 1  # number of lanes typically blocked


@dataclass
class BehaviorConfig:
    """Configuration for driver behavior parameters"""
    
    # Lane discipline by vehicle type
    lane_discipline_by_vehicle: Dict[VehicleType, float] = field(default_factory=lambda: {
        VehicleType.CAR: 0.7,
        VehicleType.BUS: 0.5,
        VehicleType.AUTO_RICKSHAW: 0.3,
        VehicleType.MOTORCYCLE: 0.2,
        VehicleType.TRUCK: 0.8,
        VehicleType.BICYCLE: 0.1
    })
    
    # Overtaking aggressiveness by vehicle type
    overtaking_aggressiveness: Dict[VehicleType, float] = field(default_factory=lambda: {
        VehicleType.CAR: 0.6,
        VehicleType.BUS: 0.4,
        VehicleType.AUTO_RICKSHAW: 0.8,
        VehicleType.MOTORCYCLE: 0.9,
        VehicleType.TRUCK: 0.3,
        VehicleType.BICYCLE: 0.2
    })
    
    # Speed adjustment factors for different conditions
    weather_speed_factors: Dict[WeatherType, float] = field(default_factory=lambda: {
        WeatherType.CLEAR: 1.0,
        WeatherType.LIGHT_RAIN: 0.8,
        WeatherType.HEAVY_RAIN: 0.5,
        WeatherType.FOG: 0.6,
        WeatherType.DUST_STORM: 0.4
    })
    
    road_quality_speed_factors: Dict[RoadQuality, float] = field(default_factory=lambda: {
        RoadQuality.EXCELLENT: 1.0,
        RoadQuality.GOOD: 0.9,
        RoadQuality.POOR: 0.7,
        RoadQuality.VERY_POOR: 0.5
    })
    
    # Following distance factors by behavior profile
    following_distance_factors: Dict[BehaviorProfile, float] = field(default_factory=lambda: {
        BehaviorProfile.CONSERVATIVE: 2.0,
        BehaviorProfile.NORMAL: 1.5,
        BehaviorProfile.AGGRESSIVE: 1.0,
        BehaviorProfile.ERRATIC: 0.8
    })


@dataclass
class IndianTrafficConfig:
    """Main configuration class for Indian traffic simulation"""
    
    # Vehicle mix ratios (should sum to 1.0)
    vehicle_mix_ratios: Dict[VehicleType, float] = field(default_factory=lambda: {
        VehicleType.CAR: 0.35,
        VehicleType.MOTORCYCLE: 0.30,
        VehicleType.AUTO_RICKSHAW: 0.15,
        VehicleType.BUS: 0.10,
        VehicleType.TRUCK: 0.08,
        VehicleType.BICYCLE: 0.02
    })
    
    # Peak hour multipliers (hour of day -> traffic multiplier)
    peak_hour_multipliers: Dict[int, float] = field(default_factory=lambda: {
        6: 1.2, 7: 1.8, 8: 2.5, 9: 2.8, 10: 2.2,  # Morning peak
        11: 1.5, 12: 1.3, 13: 1.4, 14: 1.3, 15: 1.5,  # Midday
        16: 1.8, 17: 2.3, 18: 2.8, 19: 2.5, 20: 2.0,  # Evening peak
        21: 1.5, 22: 1.2, 23: 0.8, 0: 0.5, 1: 0.3,   # Night
        2: 0.2, 3: 0.2, 4: 0.3, 5: 0.8   # Early morning
    })
    
    # Weather probabilities by season (can be customized by region)
    weather_probabilities: Dict[WeatherType, float] = field(default_factory=lambda: {
        WeatherType.CLEAR: 0.6,
        WeatherType.LIGHT_RAIN: 0.2,
        WeatherType.HEAVY_RAIN: 0.1,
        WeatherType.FOG: 0.05,
        WeatherType.DUST_STORM: 0.05
    })
    
    # Road quality distribution
    road_quality_distribution: Dict[RoadQuality, float] = field(default_factory=lambda: {
        RoadQuality.EXCELLENT: 0.15,
        RoadQuality.GOOD: 0.35,
        RoadQuality.POOR: 0.35,
        RoadQuality.VERY_POOR: 0.15
    })
    
    # Individual component configurations
    vehicle_configs: Dict[VehicleType, VehicleConfig] = field(default_factory=dict)
    road_condition_config: RoadConditionConfig = field(default_factory=RoadConditionConfig)
    behavior_config: BehaviorConfig = field(default_factory=BehaviorConfig)
    
    # Simulation parameters
    simulation_timestep: float = 0.1  # seconds
    max_vehicles: int = 1000
    spawn_rate: float = 0.5  # vehicles per second
    
    def __post_init__(self):
        """Initialize default vehicle configurations if not provided"""
        if not self.vehicle_configs:
            self.vehicle_configs = self._create_default_vehicle_configs()
    
    def _create_default_vehicle_configs(self) -> Dict[VehicleType, VehicleConfig]:
        """Create default vehicle configurations for Indian vehicles"""
        return {
            VehicleType.CAR: VehicleConfig(
                length=4.0, width=1.8, height=1.5, max_speed=120,
                acceleration=3.0, deceleration=8.0,
                default_behavior_profile=BehaviorProfile.NORMAL,
                lane_discipline_base=0.7, overtaking_aggressiveness=0.6,
                following_distance_factor=1.5, horn_usage_frequency=2.0,
                traffic_light_compliance=0.8, right_of_way_respect=0.7
            ),
            VehicleType.MOTORCYCLE: VehicleConfig(
                length=2.0, width=0.8, height=1.2, max_speed=100,
                acceleration=4.0, deceleration=6.0,
                default_behavior_profile=BehaviorProfile.AGGRESSIVE,
                lane_discipline_base=0.2, overtaking_aggressiveness=0.9,
                following_distance_factor=0.8, horn_usage_frequency=3.0,
                traffic_light_compliance=0.6, right_of_way_respect=0.4
            ),
            VehicleType.AUTO_RICKSHAW: VehicleConfig(
                length=2.8, width=1.4, height=1.8, max_speed=60,
                acceleration=2.0, deceleration=5.0,
                default_behavior_profile=BehaviorProfile.ERRATIC,
                lane_discipline_base=0.3, overtaking_aggressiveness=0.8,
                following_distance_factor=1.0, horn_usage_frequency=4.0,
                traffic_light_compliance=0.5, right_of_way_respect=0.3
            ),
            VehicleType.BUS: VehicleConfig(
                length=12.0, width=2.5, height=3.0, max_speed=80,
                acceleration=1.5, deceleration=6.0,
                default_behavior_profile=BehaviorProfile.NORMAL,
                lane_discipline_base=0.5, overtaking_aggressiveness=0.4,
                following_distance_factor=2.0, horn_usage_frequency=1.5,
                traffic_light_compliance=0.9, right_of_way_respect=0.8
            ),
            VehicleType.TRUCK: VehicleConfig(
                length=15.0, width=2.5, height=3.5, max_speed=70,
                acceleration=1.0, deceleration=5.0,
                default_behavior_profile=BehaviorProfile.CONSERVATIVE,
                lane_discipline_base=0.8, overtaking_aggressiveness=0.3,
                following_distance_factor=2.5, horn_usage_frequency=1.0,
                traffic_light_compliance=0.9, right_of_way_respect=0.9
            ),
            VehicleType.BICYCLE: VehicleConfig(
                length=1.8, width=0.6, height=1.0, max_speed=25,
                acceleration=2.0, deceleration=3.0,
                default_behavior_profile=BehaviorProfile.CONSERVATIVE,
                lane_discipline_base=0.1, overtaking_aggressiveness=0.2,
                following_distance_factor=0.5, horn_usage_frequency=0.1,
                traffic_light_compliance=0.4, right_of_way_respect=0.2
            )
        }