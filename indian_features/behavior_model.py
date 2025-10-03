"""
Indian Driver Behavior Model

This module implements behavior models for Indian driving patterns including
lane discipline, overtaking behavior, and intersection handling.
"""

import random
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .enums import (
    VehicleType, WeatherType, RoadQuality, BehaviorProfile, 
    LaneDiscipline, IntersectionType, SeverityLevel
)
from .interfaces import BehaviorModelInterface, Point3D
from .config import BehaviorConfig


@dataclass
class TrafficState:
    """Current traffic state information"""
    density: float  # vehicles per km
    average_speed: float  # km/h
    congestion_level: float  # 0.0 to 1.0
    lane_count: int
    road_width: float  # meters


@dataclass
class OvertakeDecision:
    """Decision result for overtaking maneuver"""
    should_overtake: bool
    confidence: float  # 0.0 to 1.0
    required_gap: float  # seconds
    risk_level: float  # 0.0 to 1.0
    estimated_time_savings: float  # seconds


@dataclass
class IntersectionBehavior:
    """Behavior parameters at intersections"""
    approach_speed_factor: float  # multiplier for approach speed
    stopping_probability: float  # probability of stopping at yellow light
    right_turn_aggressiveness: float  # 0.0 to 1.0
    gap_acceptance_threshold: float  # minimum gap in seconds
    horn_usage_probability: float  # probability of using horn


@dataclass
class LaneDisciplineResult:
    """Result of lane discipline calculation"""
    discipline_level: LaneDiscipline
    lane_change_probability: float  # per minute
    lateral_deviation: float  # meters from lane center
    speed_variance: float  # coefficient of variation


class IndianBehaviorModel(BehaviorModelInterface):
    """Implementation of Indian driver behavior patterns"""
    
    def __init__(self, config: Optional[BehaviorConfig] = None):
        """Initialize behavior model with configuration"""
        self.config = config or BehaviorConfig()
        
        # Calibrated parameters based on Indian traffic studies
        self.lane_discipline_thresholds = {
            LaneDiscipline.STRICT: 0.8,
            LaneDiscipline.MODERATE: 0.6,
            LaneDiscipline.LOOSE: 0.4,
            LaneDiscipline.CHAOTIC: 0.0
        }
        
        # Intersection behavior by type
        self.intersection_behaviors = {
            IntersectionType.SIGNALIZED: {
                'base_stopping_prob': 0.8,
                'yellow_light_aggression': 0.6,
                'red_light_compliance': 0.9
            },
            IntersectionType.ROUNDABOUT: {
                'yield_probability': 0.7,
                'gap_acceptance': 3.0,
                'speed_reduction': 0.6
            },
            IntersectionType.T_JUNCTION: {
                'right_of_way_respect': 0.6,
                'gap_acceptance': 2.5,
                'horn_usage': 0.8
            },
            IntersectionType.UNCONTROLLED: {
                'aggressive_entry': 0.7,
                'gap_acceptance': 2.0,
                'horn_usage': 0.9
            }
        }
    
    def calculate_lane_discipline(self, vehicle_type: VehicleType, 
                                road_conditions: Dict[str, Any]) -> LaneDisciplineResult:
        """Calculate lane discipline for given conditions"""
        
        # Base discipline from vehicle type
        base_discipline = self.config.lane_discipline_by_vehicle.get(vehicle_type, 0.5)
        
        # Adjust for road conditions
        road_quality = road_conditions.get('quality', RoadQuality.GOOD)
        lane_count = road_conditions.get('lane_count', 2)
        road_width = road_conditions.get('width', 7.0)  # meters
        traffic_density = road_conditions.get('traffic_density', 0.5)
        
        # Road quality impact
        quality_factors = {
            RoadQuality.EXCELLENT: 1.2,
            RoadQuality.GOOD: 1.0,
            RoadQuality.POOR: 0.8,
            RoadQuality.VERY_POOR: 0.6
        }
        discipline_factor = base_discipline * quality_factors.get(road_quality, 1.0)
        
        # Lane count impact (more lanes = less discipline)
        if lane_count > 2:
            discipline_factor *= (0.9 ** (lane_count - 2))
        
        # Road width impact (narrow roads = worse discipline)
        if road_width < 6.0:
            discipline_factor *= 0.8
        elif road_width > 10.0:
            discipline_factor *= 1.1
        
        # Traffic density impact (high density = worse discipline)
        discipline_factor *= (1.0 - 0.3 * traffic_density)
        
        # Vehicle-specific adjustments
        if vehicle_type == VehicleType.MOTORCYCLE:
            discipline_factor *= 0.7  # Motorcycles weave more
        elif vehicle_type == VehicleType.AUTO_RICKSHAW:
            discipline_factor *= 0.6  # Auto-rickshaws are very undisciplined
        elif vehicle_type in [VehicleType.BUS, VehicleType.TRUCK]:
            discipline_factor *= 1.2  # Larger vehicles more disciplined
        
        # Determine discipline level
        discipline_level = LaneDiscipline.CHAOTIC
        for level, threshold in sorted(self.lane_discipline_thresholds.items(), 
                                     key=lambda x: x[1], reverse=True):
            if discipline_factor >= threshold:
                discipline_level = level
                break
        
        # Calculate derived metrics
        lane_change_prob = self._calculate_lane_change_probability(discipline_factor, traffic_density)
        lateral_deviation = self._calculate_lateral_deviation(discipline_factor, vehicle_type)
        speed_variance = self._calculate_speed_variance(discipline_factor, vehicle_type)
        
        return LaneDisciplineResult(
            discipline_level=discipline_level,
            lane_change_probability=lane_change_prob,
            lateral_deviation=lateral_deviation,
            speed_variance=speed_variance
        )
    
    def determine_overtaking_probability(self, vehicle_type: VehicleType, 
                                       traffic_density: float) -> float:
        """Determine probability of overtaking maneuver"""
        
        base_aggressiveness = self.config.overtaking_aggressiveness.get(vehicle_type, 0.5)
        
        # Reduce overtaking in high density traffic
        density_factor = max(0.1, 1.0 - traffic_density)
        
        # Vehicle-specific overtaking tendencies
        vehicle_factors = {
            VehicleType.MOTORCYCLE: 1.5,  # Very aggressive
            VehicleType.AUTO_RICKSHAW: 1.3,  # Quite aggressive
            VehicleType.CAR: 1.0,  # Baseline
            VehicleType.BUS: 0.7,  # Less aggressive
            VehicleType.TRUCK: 0.5,  # Conservative
            VehicleType.BICYCLE: 0.3  # Very conservative
        }
        
        vehicle_factor = vehicle_factors.get(vehicle_type, 1.0)
        
        return base_aggressiveness * density_factor * vehicle_factor
    
    def determine_overtaking_behavior(self, vehicle_type: VehicleType, 
                                    traffic_state: TrafficState,
                                    leading_vehicle_speed: float,
                                    own_desired_speed: float) -> OvertakeDecision:
        """Determine detailed overtaking behavior"""
        
        # Speed differential (key factor in overtaking decision)
        speed_diff = own_desired_speed - leading_vehicle_speed
        
        if speed_diff <= 5:  # Not worth overtaking for small speed difference
            return OvertakeDecision(
                should_overtake=False,
                confidence=0.0,
                required_gap=0.0,
                risk_level=0.0,
                estimated_time_savings=0.0
            )
        
        # Base overtaking probability
        base_prob = self.determine_overtaking_probability(vehicle_type, traffic_state.density)
        
        # Adjust for speed differential
        speed_factor = min(2.0, speed_diff / 20.0)  # Normalize to reasonable range
        
        # Adjust for traffic conditions
        congestion_penalty = traffic_state.congestion_level * 0.5
        
        # Calculate final probability
        overtake_prob = base_prob * speed_factor * (1.0 - congestion_penalty)
        
        # Determine if should overtake
        should_overtake = random.random() < overtake_prob
        
        if not should_overtake:
            return OvertakeDecision(
                should_overtake=False,
                confidence=overtake_prob,
                required_gap=0.0,
                risk_level=0.0,
                estimated_time_savings=0.0
            )
        
        # Calculate overtaking parameters
        required_gap = self._calculate_required_overtaking_gap(vehicle_type, speed_diff)
        risk_level = self._calculate_overtaking_risk(vehicle_type, traffic_state, speed_diff)
        time_savings = self._estimate_overtaking_time_savings(speed_diff, traffic_state.density)
        
        return OvertakeDecision(
            should_overtake=True,
            confidence=overtake_prob,
            required_gap=required_gap,
            risk_level=risk_level,
            estimated_time_savings=time_savings
        )
    
    def model_intersection_behavior(self, vehicle_type: VehicleType, 
                                  intersection_type: IntersectionType) -> IntersectionBehavior:
        """Model behavior at intersections"""
        
        base_behavior = self.intersection_behaviors.get(intersection_type, {})
        
        # Vehicle-specific adjustments
        vehicle_adjustments = {
            VehicleType.MOTORCYCLE: {
                'aggressiveness_multiplier': 1.4,
                'gap_acceptance_reduction': 0.7,
                'horn_usage_increase': 1.5
            },
            VehicleType.AUTO_RICKSHAW: {
                'aggressiveness_multiplier': 1.3,
                'gap_acceptance_reduction': 0.8,
                'horn_usage_increase': 1.8
            },
            VehicleType.CAR: {
                'aggressiveness_multiplier': 1.0,
                'gap_acceptance_reduction': 1.0,
                'horn_usage_increase': 1.0
            },
            VehicleType.BUS: {
                'aggressiveness_multiplier': 0.8,
                'gap_acceptance_reduction': 1.2,
                'horn_usage_increase': 0.8
            },
            VehicleType.TRUCK: {
                'aggressiveness_multiplier': 0.7,
                'gap_acceptance_reduction': 1.3,
                'horn_usage_increase': 0.6
            }
        }
        
        adjustments = vehicle_adjustments.get(vehicle_type, vehicle_adjustments[VehicleType.CAR])
        
        # Calculate behavior parameters
        approach_speed_factor = 0.8 * adjustments['aggressiveness_multiplier']
        
        stopping_probability = base_behavior.get('base_stopping_prob', 0.7)
        if vehicle_type in [VehicleType.MOTORCYCLE, VehicleType.AUTO_RICKSHAW]:
            stopping_probability *= 0.8  # More likely to run lights
        
        right_turn_aggressiveness = 0.6 * adjustments['aggressiveness_multiplier']
        
        gap_acceptance = base_behavior.get('gap_acceptance', 3.0) * adjustments['gap_acceptance_reduction']
        
        horn_probability = base_behavior.get('horn_usage', 0.5) * adjustments['horn_usage_increase']
        
        return IntersectionBehavior(
            approach_speed_factor=approach_speed_factor,
            stopping_probability=stopping_probability,
            right_turn_aggressiveness=right_turn_aggressiveness,
            gap_acceptance_threshold=gap_acceptance,
            horn_usage_probability=horn_probability
        )
    
    def apply_weather_effects(self, base_behavior: Dict[str, float], 
                            weather: WeatherType) -> Dict[str, float]:
        """Apply weather effects to behavior parameters"""
        
        weather_effects = {
            WeatherType.CLEAR: {
                'speed_factor': 1.0,
                'following_distance_factor': 1.0,
                'lane_discipline_factor': 1.0,
                'overtaking_factor': 1.0
            },
            WeatherType.LIGHT_RAIN: {
                'speed_factor': 0.9,
                'following_distance_factor': 1.2,
                'lane_discipline_factor': 0.9,
                'overtaking_factor': 0.8
            },
            WeatherType.HEAVY_RAIN: {
                'speed_factor': 0.7,
                'following_distance_factor': 1.5,
                'lane_discipline_factor': 0.7,
                'overtaking_factor': 0.5
            },
            WeatherType.FOG: {
                'speed_factor': 0.6,
                'following_distance_factor': 1.8,
                'lane_discipline_factor': 0.8,
                'overtaking_factor': 0.3
            },
            WeatherType.DUST_STORM: {
                'speed_factor': 0.5,
                'following_distance_factor': 2.0,
                'lane_discipline_factor': 0.6,
                'overtaking_factor': 0.2
            }
        }
        
        effects = weather_effects.get(weather, weather_effects[WeatherType.CLEAR])
        
        # Apply effects to base behavior
        modified_behavior = {}
        for key, value in base_behavior.items():
            if 'speed' in key.lower():
                modified_behavior[key] = value * effects['speed_factor']
            elif 'following' in key.lower() or 'distance' in key.lower():
                modified_behavior[key] = value * effects['following_distance_factor']
            elif 'lane' in key.lower() or 'discipline' in key.lower():
                modified_behavior[key] = value * effects['lane_discipline_factor']
            elif 'overtaking' in key.lower() or 'overtake' in key.lower():
                modified_behavior[key] = value * effects['overtaking_factor']
            else:
                modified_behavior[key] = value
        
        return modified_behavior
    
    def calculate_stress_level(self, vehicle_type: VehicleType, 
                             traffic_conditions: Dict[str, Any]) -> float:
        """Calculate driver stress level based on conditions"""
        
        base_stress = 0.3  # Base stress level
        
        # Traffic density stress
        density = traffic_conditions.get('density', 0.5)
        density_stress = density * 0.4
        
        # Speed frustration stress
        current_speed = traffic_conditions.get('current_speed', 30)
        desired_speed = traffic_conditions.get('desired_speed', 50)
        speed_ratio = current_speed / max(desired_speed, 1)
        speed_stress = max(0, (1 - speed_ratio) * 0.3)
        
        # Weather stress
        weather = traffic_conditions.get('weather', WeatherType.CLEAR)
        weather_stress_factors = {
            WeatherType.CLEAR: 0.0,
            WeatherType.LIGHT_RAIN: 0.1,
            WeatherType.HEAVY_RAIN: 0.3,
            WeatherType.FOG: 0.25,
            WeatherType.DUST_STORM: 0.35
        }
        weather_stress = weather_stress_factors.get(weather, 0.0)
        
        # Vehicle-specific stress tolerance
        stress_tolerance = {
            VehicleType.MOTORCYCLE: 0.8,  # Lower tolerance (higher stress)
            VehicleType.AUTO_RICKSHAW: 0.7,
            VehicleType.CAR: 1.0,
            VehicleType.BUS: 1.2,  # Higher tolerance (lower stress)
            VehicleType.TRUCK: 1.1,
            VehicleType.BICYCLE: 0.6
        }
        
        tolerance = stress_tolerance.get(vehicle_type, 1.0)
        
        total_stress = (base_stress + density_stress + speed_stress + weather_stress) / tolerance
        
        return min(1.0, max(0.0, total_stress))
    
    def _calculate_lane_change_probability(self, discipline_factor: float, 
                                         traffic_density: float) -> float:
        """Calculate probability of lane changes per minute"""
        
        # Base rate inversely related to discipline
        base_rate = 2.0 * (1.0 - discipline_factor)
        
        # Increase with traffic density (more opportunities and frustration)
        density_factor = 1.0 + traffic_density
        
        return base_rate * density_factor
    
    def _calculate_lateral_deviation(self, discipline_factor: float, 
                                   vehicle_type: VehicleType) -> float:
        """Calculate lateral deviation from lane center"""
        
        # Base deviation inversely related to discipline
        base_deviation = 0.5 * (1.0 - discipline_factor)  # meters
        
        # Vehicle-specific adjustments
        if vehicle_type == VehicleType.MOTORCYCLE:
            base_deviation *= 1.5  # Motorcycles weave more
        elif vehicle_type == VehicleType.AUTO_RICKSHAW:
            base_deviation *= 1.3
        elif vehicle_type in [VehicleType.BUS, VehicleType.TRUCK]:
            base_deviation *= 0.8  # Larger vehicles more stable
        
        return base_deviation
    
    def _calculate_speed_variance(self, discipline_factor: float, 
                                vehicle_type: VehicleType) -> float:
        """Calculate coefficient of variation in speed"""
        
        # Base variance inversely related to discipline
        base_variance = 0.2 * (1.0 - discipline_factor)
        
        # Vehicle-specific adjustments
        if vehicle_type in [VehicleType.MOTORCYCLE, VehicleType.AUTO_RICKSHAW]:
            base_variance *= 1.4  # More erratic speed
        elif vehicle_type in [VehicleType.BUS, VehicleType.TRUCK]:
            base_variance *= 0.7  # More consistent speed
        
        return base_variance
    
    def _calculate_required_overtaking_gap(self, vehicle_type: VehicleType, 
                                         speed_diff: float) -> float:
        """Calculate required gap for safe overtaking"""
        
        # Base gap requirements by vehicle type (seconds)
        base_gaps = {
            VehicleType.MOTORCYCLE: 2.0,
            VehicleType.AUTO_RICKSHAW: 2.5,
            VehicleType.CAR: 3.0,
            VehicleType.BUS: 4.0,
            VehicleType.TRUCK: 5.0,
            VehicleType.BICYCLE: 1.5
        }
        
        base_gap = base_gaps.get(vehicle_type, 3.0)
        
        # Adjust for speed differential
        speed_factor = 1.0 + (speed_diff / 50.0)  # More gap needed for higher speed diff
        
        return base_gap * speed_factor
    
    def _calculate_overtaking_risk(self, vehicle_type: VehicleType, 
                                 traffic_state: TrafficState, 
                                 speed_diff: float) -> float:
        """Calculate risk level of overtaking maneuver"""
        
        # Base risk factors
        density_risk = traffic_state.density * 0.4
        congestion_risk = traffic_state.congestion_level * 0.3
        speed_risk = min(0.3, speed_diff / 100.0)  # Higher speed diff = higher risk
        
        # Vehicle-specific risk adjustments
        vehicle_risk_factors = {
            VehicleType.MOTORCYCLE: 0.8,  # Lower perceived risk
            VehicleType.AUTO_RICKSHAW: 0.9,
            VehicleType.CAR: 1.0,
            VehicleType.BUS: 1.3,  # Higher risk due to size
            VehicleType.TRUCK: 1.5,
            VehicleType.BICYCLE: 0.6
        }
        
        vehicle_factor = vehicle_risk_factors.get(vehicle_type, 1.0)
        
        total_risk = (density_risk + congestion_risk + speed_risk) * vehicle_factor
        
        return min(1.0, max(0.0, total_risk))
    
    def _estimate_overtaking_time_savings(self, speed_diff: float, 
                                        traffic_density: float) -> float:
        """Estimate time savings from overtaking maneuver"""
        
        # Base time savings proportional to speed difference
        base_savings = speed_diff * 0.1  # seconds per km/h difference
        
        # Reduce savings in dense traffic (less opportunity to maintain higher speed)
        density_factor = 1.0 - (traffic_density * 0.5)
        
        return max(0.0, base_savings * density_factor)