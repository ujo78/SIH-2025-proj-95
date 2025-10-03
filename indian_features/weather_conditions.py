"""
Weather Conditions Module

This module implements weather condition classes and effects for Indian traffic simulation,
including weather impact calculations and time-based traffic density variations.
"""

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

from .enums import WeatherType, VehicleType, SeverityLevel
from .interfaces import Point3D


@dataclass
class WeatherCondition:
    """Represents current weather conditions affecting traffic"""
    condition_type: WeatherType
    intensity: float  # 0.0 to 1.0
    visibility: float  # 0.0 to 1.0 (1.0 = perfect visibility)
    road_wetness: float  # 0.0 to 1.0 (1.0 = completely wet)
    temperature: float  # Celsius
    wind_speed: float  # km/h
    duration_minutes: int  # Expected duration
    start_time: datetime
    
    def __post_init__(self):
        """Calculate derived properties based on weather type and intensity"""
        self._calculate_visibility()
        self._calculate_road_wetness()
        self._set_typical_temperature()
        self._set_typical_wind_speed()
    
    def _calculate_visibility(self):
        """Calculate visibility based on weather type and intensity"""
        base_visibility = {
            WeatherType.CLEAR: 1.0,
            WeatherType.LIGHT_RAIN: 0.8,
            WeatherType.HEAVY_RAIN: 0.4,
            WeatherType.FOG: 0.2,
            WeatherType.DUST_STORM: 0.1
        }
        
        base_vis = base_visibility.get(self.condition_type, 1.0)
        # Intensity reduces visibility further
        self.visibility = base_vis * (1.0 - self.intensity * 0.5)
        self.visibility = max(0.05, min(1.0, self.visibility))  # Clamp between 0.05 and 1.0
    
    def _calculate_road_wetness(self):
        """Calculate road wetness based on weather type and intensity"""
        if self.condition_type in [WeatherType.LIGHT_RAIN, WeatherType.HEAVY_RAIN]:
            base_wetness = 0.3 if self.condition_type == WeatherType.LIGHT_RAIN else 0.8
            self.road_wetness = min(1.0, base_wetness + self.intensity * 0.5)
        else:
            self.road_wetness = 0.0
    
    def _set_typical_temperature(self):
        """Set typical temperature for Indian conditions"""
        if self.condition_type == WeatherType.CLEAR:
            self.temperature = random.uniform(25, 40)  # Hot Indian climate
        elif self.condition_type in [WeatherType.LIGHT_RAIN, WeatherType.HEAVY_RAIN]:
            self.temperature = random.uniform(20, 30)  # Cooler during rain
        elif self.condition_type == WeatherType.FOG:
            self.temperature = random.uniform(15, 25)  # Cool foggy conditions
        elif self.condition_type == WeatherType.DUST_STORM:
            self.temperature = random.uniform(30, 45)  # Hot and dusty
    
    def _set_typical_wind_speed(self):
        """Set typical wind speed for weather condition"""
        if self.condition_type == WeatherType.DUST_STORM:
            self.wind_speed = random.uniform(40, 80)  # High winds
        elif self.condition_type == WeatherType.HEAVY_RAIN:
            self.wind_speed = random.uniform(20, 40)  # Moderate winds
        else:
            self.wind_speed = random.uniform(5, 20)  # Light winds
    
    def get_speed_impact_factor(self, vehicle_type: VehicleType) -> float:
        """Get speed impact factor for a specific vehicle type"""
        base_factors = {
            WeatherType.CLEAR: 1.0,
            WeatherType.LIGHT_RAIN: 0.85,
            WeatherType.HEAVY_RAIN: 0.6,
            WeatherType.FOG: 0.5,
            WeatherType.DUST_STORM: 0.4
        }
        
        base_factor = base_factors.get(self.condition_type, 1.0)
        
        # Vehicle-specific adjustments
        vehicle_adjustments = {
            VehicleType.MOTORCYCLE: 0.8,  # More affected by weather
            VehicleType.AUTO_RICKSHAW: 0.85,
            VehicleType.BICYCLE: 0.7,  # Very affected
            VehicleType.CAR: 1.0,  # Baseline
            VehicleType.BUS: 1.1,  # Less affected due to size
            VehicleType.TRUCK: 1.05
        }
        
        vehicle_factor = vehicle_adjustments.get(vehicle_type, 1.0)
        
        # Apply intensity
        final_factor = base_factor * vehicle_factor
        final_factor = final_factor * (1.0 - self.intensity * 0.2)  # Intensity reduces speed further
        
        return max(0.2, min(1.0, final_factor))  # Clamp between 0.2 and 1.0
    
    def get_following_distance_factor(self, vehicle_type: VehicleType) -> float:
        """Get following distance multiplier based on weather"""
        base_factors = {
            WeatherType.CLEAR: 1.0,
            WeatherType.LIGHT_RAIN: 1.3,
            WeatherType.HEAVY_RAIN: 1.8,
            WeatherType.FOG: 2.0,
            WeatherType.DUST_STORM: 1.6
        }
        
        base_factor = base_factors.get(self.condition_type, 1.0)
        
        # Motorcycles and bicycles need even more distance in bad weather
        if vehicle_type in [VehicleType.MOTORCYCLE, VehicleType.BICYCLE]:
            base_factor *= 1.2
        
        # Apply intensity
        final_factor = base_factor * (1.0 + self.intensity * 0.5)
        
        return max(1.0, final_factor)
    
    def get_accident_probability_multiplier(self) -> float:
        """Get accident probability multiplier for current weather"""
        multipliers = {
            WeatherType.CLEAR: 1.0,
            WeatherType.LIGHT_RAIN: 1.5,
            WeatherType.HEAVY_RAIN: 3.0,
            WeatherType.FOG: 2.5,
            WeatherType.DUST_STORM: 2.8
        }
        
        base_multiplier = multipliers.get(self.condition_type, 1.0)
        return base_multiplier * (1.0 + self.intensity * 0.5)
    
    def is_active(self, current_time: datetime) -> bool:
        """Check if weather condition is still active"""
        end_time = self.start_time + timedelta(minutes=self.duration_minutes)
        return self.start_time <= current_time <= end_time


class WeatherManager:
    """Manages weather conditions and their effects on traffic simulation"""
    
    def __init__(self):
        """Initialize weather manager"""
        self.current_weather = WeatherCondition(
            condition_type=WeatherType.CLEAR,
            intensity=0.0,
            visibility=1.0,
            road_wetness=0.0,
            temperature=30.0,
            wind_speed=10.0,
            duration_minutes=60,
            start_time=datetime.now()
        )
        
        # Weather transition probabilities (Indian climate patterns)
        self.transition_probabilities = {
            WeatherType.CLEAR: {
                WeatherType.CLEAR: 0.7,
                WeatherType.LIGHT_RAIN: 0.15,
                WeatherType.FOG: 0.1,
                WeatherType.DUST_STORM: 0.05
            },
            WeatherType.LIGHT_RAIN: {
                WeatherType.CLEAR: 0.4,
                WeatherType.LIGHT_RAIN: 0.3,
                WeatherType.HEAVY_RAIN: 0.25,
                WeatherType.FOG: 0.05
            },
            WeatherType.HEAVY_RAIN: {
                WeatherType.LIGHT_RAIN: 0.5,
                WeatherType.HEAVY_RAIN: 0.3,
                WeatherType.CLEAR: 0.15,
                WeatherType.FOG: 0.05
            },
            WeatherType.FOG: {
                WeatherType.CLEAR: 0.6,
                WeatherType.FOG: 0.25,
                WeatherType.LIGHT_RAIN: 0.15
            },
            WeatherType.DUST_STORM: {
                WeatherType.CLEAR: 0.7,
                WeatherType.DUST_STORM: 0.2,
                WeatherType.LIGHT_RAIN: 0.1
            }
        }
        
        # Seasonal weather patterns (month -> weather probabilities)
        self.seasonal_patterns = {
            # Winter (Dec, Jan, Feb)
            12: {WeatherType.CLEAR: 0.6, WeatherType.FOG: 0.3, WeatherType.LIGHT_RAIN: 0.1},
            1: {WeatherType.CLEAR: 0.5, WeatherType.FOG: 0.4, WeatherType.LIGHT_RAIN: 0.1},
            2: {WeatherType.CLEAR: 0.7, WeatherType.FOG: 0.2, WeatherType.DUST_STORM: 0.1},
            
            # Spring (Mar, Apr, May)
            3: {WeatherType.CLEAR: 0.8, WeatherType.DUST_STORM: 0.15, WeatherType.LIGHT_RAIN: 0.05},
            4: {WeatherType.CLEAR: 0.7, WeatherType.DUST_STORM: 0.2, WeatherType.LIGHT_RAIN: 0.1},
            5: {WeatherType.CLEAR: 0.6, WeatherType.DUST_STORM: 0.25, WeatherType.LIGHT_RAIN: 0.15},
            
            # Monsoon (Jun, Jul, Aug, Sep)
            6: {WeatherType.LIGHT_RAIN: 0.4, WeatherType.HEAVY_RAIN: 0.3, WeatherType.CLEAR: 0.3},
            7: {WeatherType.HEAVY_RAIN: 0.5, WeatherType.LIGHT_RAIN: 0.3, WeatherType.CLEAR: 0.2},
            8: {WeatherType.HEAVY_RAIN: 0.4, WeatherType.LIGHT_RAIN: 0.4, WeatherType.CLEAR: 0.2},
            9: {WeatherType.LIGHT_RAIN: 0.5, WeatherType.CLEAR: 0.3, WeatherType.HEAVY_RAIN: 0.2},
            
            # Post-monsoon (Oct, Nov)
            10: {WeatherType.CLEAR: 0.7, WeatherType.LIGHT_RAIN: 0.2, WeatherType.FOG: 0.1},
            11: {WeatherType.CLEAR: 0.6, WeatherType.FOG: 0.25, WeatherType.LIGHT_RAIN: 0.15}
        }
    
    def update_weather(self, current_time: datetime, force_change: bool = False) -> WeatherCondition:
        """Update weather conditions based on time and patterns"""
        
        # Check if current weather is still active
        if not force_change and self.current_weather.is_active(current_time):
            return self.current_weather
        
        # Determine new weather based on seasonal patterns and transitions
        current_month = current_time.month
        seasonal_probs = self.seasonal_patterns.get(current_month, 
                                                   {WeatherType.CLEAR: 1.0})
        
        # Combine seasonal and transition probabilities
        if not force_change:
            transition_probs = self.transition_probabilities.get(
                self.current_weather.condition_type, {WeatherType.CLEAR: 1.0}
            )
            
            # Weighted combination of seasonal and transition probabilities
            combined_probs = {}
            for weather_type in WeatherType:
                seasonal_prob = seasonal_probs.get(weather_type, 0.0)
                transition_prob = transition_probs.get(weather_type, 0.0)
                combined_probs[weather_type] = (seasonal_prob * 0.6 + transition_prob * 0.4)
        else:
            combined_probs = seasonal_probs
        
        # Select new weather type
        new_weather_type = self._select_weather_type(combined_probs)
        
        # Generate new weather condition
        self.current_weather = self._generate_weather_condition(new_weather_type, current_time)
        
        return self.current_weather
    
    def _select_weather_type(self, probabilities: Dict[WeatherType, float]) -> WeatherType:
        """Select weather type based on probabilities"""
        # Normalize probabilities
        total_prob = sum(probabilities.values())
        if total_prob == 0:
            return WeatherType.CLEAR
        
        normalized_probs = {k: v / total_prob for k, v in probabilities.items()}
        
        # Random selection
        rand_val = random.random()
        cumulative_prob = 0.0
        
        for weather_type, prob in normalized_probs.items():
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                return weather_type
        
        return WeatherType.CLEAR  # Fallback
    
    def _generate_weather_condition(self, weather_type: WeatherType, 
                                  start_time: datetime) -> WeatherCondition:
        """Generate a new weather condition with realistic parameters"""
        
        # Duration based on weather type
        duration_ranges = {
            WeatherType.CLEAR: (120, 480),  # 2-8 hours
            WeatherType.LIGHT_RAIN: (30, 180),  # 30 minutes - 3 hours
            WeatherType.HEAVY_RAIN: (15, 120),  # 15 minutes - 2 hours
            WeatherType.FOG: (60, 300),  # 1-5 hours
            WeatherType.DUST_STORM: (20, 90)  # 20 minutes - 1.5 hours
        }
        
        min_duration, max_duration = duration_ranges.get(weather_type, (60, 180))
        duration = random.randint(min_duration, max_duration)
        
        # Intensity based on weather type
        intensity_ranges = {
            WeatherType.CLEAR: (0.0, 0.1),
            WeatherType.LIGHT_RAIN: (0.2, 0.6),
            WeatherType.HEAVY_RAIN: (0.6, 1.0),
            WeatherType.FOG: (0.3, 0.8),
            WeatherType.DUST_STORM: (0.4, 0.9)
        }
        
        min_intensity, max_intensity = intensity_ranges.get(weather_type, (0.0, 0.5))
        intensity = random.uniform(min_intensity, max_intensity)
        
        return WeatherCondition(
            condition_type=weather_type,
            intensity=intensity,
            visibility=1.0,  # Will be calculated in __post_init__
            road_wetness=0.0,  # Will be calculated in __post_init__
            temperature=30.0,  # Will be set in __post_init__
            wind_speed=10.0,  # Will be set in __post_init__
            duration_minutes=duration,
            start_time=start_time
        )
    
    def get_current_weather_effects(self, vehicle_type: VehicleType) -> Dict[str, float]:
        """Get current weather effects for a vehicle type"""
        return {
            'speed_factor': self.current_weather.get_speed_impact_factor(vehicle_type),
            'following_distance_factor': self.current_weather.get_following_distance_factor(vehicle_type),
            'accident_probability_multiplier': self.current_weather.get_accident_probability_multiplier(),
            'visibility': self.current_weather.visibility,
            'road_wetness': self.current_weather.road_wetness
        }
    
    def update_weather_effects(self, dt: float) -> None:
        """Update weather effects based on elapsed time"""
        # Update weather conditions periodically
        current_time = datetime.now()
        
        # Check if we should update weather (every 5 minutes of simulation time)
        if not hasattr(self, '_last_weather_update'):
            self._last_weather_update = 0.0
        
        self._last_weather_update += dt
        
        # Update weather every 300 seconds (5 minutes) of simulation time
        if self._last_weather_update >= 300.0:
            self.update_weather(current_time)
            self._last_weather_update = 0.0


class TimeOfDayManager:
    """Manages time-of-day effects on traffic patterns"""
    
    def __init__(self):
        """Initialize time-of-day manager with Indian traffic patterns"""
        
        # Peak hour multipliers for traffic density (hour -> multiplier)
        self.peak_hour_multipliers = {
            # Early morning
            5: 0.3, 6: 0.6, 7: 1.5, 8: 2.0, 9: 1.8, 10: 1.2,
            # Midday
            11: 1.0, 12: 1.1, 13: 1.2, 14: 1.0, 15: 1.1, 16: 1.3,
            # Evening peak
            17: 1.8, 18: 2.2, 19: 2.0, 20: 1.6, 21: 1.2, 22: 0.8,
            # Night
            23: 0.5, 0: 0.3, 1: 0.2, 2: 0.15, 3: 0.1, 4: 0.2
        }
        
        # Speed adjustments by hour (due to traffic density and visibility)
        self.speed_adjustments = {
            # Early morning - less traffic, good visibility
            5: 1.2, 6: 1.1, 7: 0.8, 8: 0.6, 9: 0.7, 10: 0.9,
            # Midday - moderate traffic
            11: 1.0, 12: 0.95, 13: 0.9, 14: 1.0, 15: 0.95, 16: 0.85,
            # Evening - heavy traffic
            17: 0.7, 18: 0.5, 19: 0.6, 20: 0.75, 21: 0.9, 22: 1.1,
            # Night - less traffic but reduced visibility
            23: 1.0, 0: 0.9, 1: 0.8, 2: 0.8, 3: 0.8, 4: 0.9
        }
        
        # Behavior aggressiveness by hour
        self.aggressiveness_multipliers = {
            # Morning rush - high stress
            7: 1.3, 8: 1.5, 9: 1.4,
            # Midday - moderate
            12: 1.1, 13: 1.0,
            # Evening rush - highest stress
            17: 1.4, 18: 1.6, 19: 1.5, 20: 1.3,
            # Night - more relaxed but some reckless behavior
            22: 0.8, 23: 0.9, 0: 1.2, 1: 1.3, 2: 1.4
        }
        
        # Default values for hours not specified
        for hour in range(24):
            if hour not in self.peak_hour_multipliers:
                self.peak_hour_multipliers[hour] = 1.0
            if hour not in self.speed_adjustments:
                self.speed_adjustments[hour] = 1.0
            if hour not in self.aggressiveness_multipliers:
                self.aggressiveness_multipliers[hour] = 1.0
    
    def get_traffic_density_multiplier(self, hour: int) -> float:
        """Get traffic density multiplier for given hour"""
        return self.peak_hour_multipliers.get(hour, 1.0)
    
    def get_speed_adjustment(self, hour: int) -> float:
        """Get speed adjustment factor for given hour"""
        return self.speed_adjustments.get(hour, 1.0)
    
    def get_aggressiveness_multiplier(self, hour: int) -> float:
        """Get behavior aggressiveness multiplier for given hour"""
        return self.aggressiveness_multipliers.get(hour, 1.0)
    
    def get_spawn_rate_adjustment(self, hour: int, base_spawn_rate: float) -> float:
        """Get adjusted spawn rate based on time of day"""
        density_multiplier = self.get_traffic_density_multiplier(hour)
        return base_spawn_rate * density_multiplier
    
    def is_peak_hour(self, hour: int) -> bool:
        """Check if given hour is a peak traffic hour"""
        return self.peak_hour_multipliers.get(hour, 1.0) >= 1.5
    
    def get_time_effects_summary(self, hour: int) -> Dict[str, Any]:
        """Get comprehensive time effects for given hour"""
        return {
            'hour': hour,
            'is_peak_hour': self.is_peak_hour(hour),
            'traffic_density_multiplier': self.get_traffic_density_multiplier(hour),
            'speed_adjustment': self.get_speed_adjustment(hour),
            'aggressiveness_multiplier': self.get_aggressiveness_multiplier(hour),
            'period': self._get_time_period(hour)
        }
    
    def _get_time_period(self, hour: int) -> str:
        """Get descriptive time period for hour"""
        if 5 <= hour <= 10:
            return "morning_rush"
        elif 11 <= hour <= 16:
            return "midday"
        elif 17 <= hour <= 21:
            return "evening_rush"
        elif 22 <= hour <= 4:
            return "night"
        else:
            return "early_morning"