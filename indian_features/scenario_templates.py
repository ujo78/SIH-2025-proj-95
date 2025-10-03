"""
Pre-built Indian Traffic Scenario Templates

This module contains pre-defined scenario templates for common Indian traffic
situations including intersections, emergencies, peak hours, and regional variations.
"""

from datetime import timedelta
from typing import Dict, List, Any

from .enums import (
    VehicleType, EmergencyType, WeatherType, SeverityLevel,
    IntersectionType, RoadQuality
)
from .config import IndianTrafficConfig
from .scenario_manager import ScenarioTemplate


class IndianScenarioTemplates:
    """Factory class for creating pre-built Indian traffic scenario templates"""
    
    @staticmethod
    def create_mumbai_intersection_template() -> ScenarioTemplate:
        """Create template for typical Mumbai intersection scenario"""
        
        # Mumbai-specific vehicle mix (higher auto-rickshaw and taxi density)
        mumbai_vehicle_mix = {
            VehicleType.CAR: 0.30,
            VehicleType.MOTORCYCLE: 0.35,
            VehicleType.AUTO_RICKSHAW: 0.20,
            VehicleType.BUS: 0.08,
            VehicleType.TRUCK: 0.05,
            VehicleType.BICYCLE: 0.02
        }
        
        # Mumbai peak hour patterns (extended peak hours)
        mumbai_peak_hours = {
            6: 1.5, 7: 2.2, 8: 3.0, 9: 3.2, 10: 2.8,
            11: 2.0, 12: 1.8, 13: 1.9, 14: 1.8, 15: 2.0,
            16: 2.5, 17: 3.0, 18: 3.5, 19: 3.2, 20: 2.8,
            21: 2.2, 22: 1.8, 23: 1.2, 0: 0.8, 1: 0.5,
            2: 0.3, 3: 0.3, 4: 0.5, 5: 1.0
        }
        
        # Mumbai weather patterns (monsoon heavy)
        mumbai_weather = {
            WeatherType.CLEAR: 0.4,
            WeatherType.LIGHT_RAIN: 0.3,
            WeatherType.HEAVY_RAIN: 0.2,
            WeatherType.FOG: 0.05,
            WeatherType.DUST_STORM: 0.05
        }
        
        traffic_config = IndianTrafficConfig(
            vehicle_mix_ratios=mumbai_vehicle_mix,
            peak_hour_multipliers=mumbai_peak_hours,
            weather_probabilities=mumbai_weather,
            spawn_rate=0.8,  # Higher spawn rate for Mumbai density
            max_vehicles=1500
        )
        
        return ScenarioTemplate(
            template_id="mumbai_intersection",
            name="Mumbai Busy Intersection",
            description="Typical busy intersection in Mumbai with high density mixed traffic, frequent auto-rickshaws, and monsoon considerations",
            category="intersection",
            traffic_config=traffic_config,
            simulation_duration=3600.0,
            time_of_day=18,  # Evening peak
            day_of_week=1,   # Tuesday
            weather_type=WeatherType.LIGHT_RAIN,
            weather_intensity=0.6,
            network_bounds={
                "north": 19.0760,
                "south": 19.0740,
                "east": 72.8777,
                "west": 72.8757
            },
            custom_parameters={
                "intersection_type": "signalized",
                "signal_cycle_time": 120,  # seconds
                "pedestrian_density": "high",
                "street_vendor_presence": True,
                "parking_availability": "limited"
            }
        )
    
    @staticmethod
    def create_bangalore_tech_corridor_template() -> ScenarioTemplate:
        """Create template for Bangalore tech corridor traffic"""
        
        # Bangalore vehicle mix (higher car and bus usage)
        bangalore_vehicle_mix = {
            VehicleType.CAR: 0.45,
            VehicleType.MOTORCYCLE: 0.25,
            VehicleType.AUTO_RICKSHAW: 0.12,
            VehicleType.BUS: 0.15,
            VehicleType.TRUCK: 0.02,
            VehicleType.BICYCLE: 0.01
        }
        
        # Tech corridor peak hours (office timings)
        tech_peak_hours = {
            6: 1.0, 7: 1.5, 8: 2.0, 9: 3.5, 10: 3.8,
            11: 2.5, 12: 2.0, 13: 2.2, 14: 2.0, 15: 2.5,
            16: 2.8, 17: 3.2, 18: 4.0, 19: 3.8, 20: 3.0,
            21: 2.0, 22: 1.5, 23: 1.0, 0: 0.6, 1: 0.4,
            2: 0.2, 3: 0.2, 4: 0.3, 5: 0.8
        }
        
        traffic_config = IndianTrafficConfig(
            vehicle_mix_ratios=bangalore_vehicle_mix,
            peak_hour_multipliers=tech_peak_hours,
            spawn_rate=0.7,
            max_vehicles=1200
        )
        
        return ScenarioTemplate(
            template_id="bangalore_tech_corridor",
            name="Bangalore Tech Corridor",
            description="IT corridor in Bangalore with office-going traffic, higher car density, and organized bus services",
            category="regional",
            traffic_config=traffic_config,
            simulation_duration=7200.0,  # 2 hours
            time_of_day=9,   # Morning office hours
            day_of_week=1,   # Tuesday
            weather_type=WeatherType.CLEAR,
            weather_intensity=1.0,
            network_bounds={
                "north": 12.9716,
                "south": 12.9696,
                "east": 77.5946,
                "west": 77.5926
            },
            custom_parameters={
                "office_density": "high",
                "bus_frequency": "high",
                "traffic_police_presence": True,
                "road_quality": "good",
                "signal_coordination": True
            }
        )
    
    @staticmethod
    def create_delhi_roundabout_template() -> ScenarioTemplate:
        """Create template for Delhi roundabout scenario"""
        
        # Delhi vehicle mix (higher truck and bus presence)
        delhi_vehicle_mix = {
            VehicleType.CAR: 0.40,
            VehicleType.MOTORCYCLE: 0.28,
            VehicleType.AUTO_RICKSHAW: 0.10,
            VehicleType.BUS: 0.12,
            VehicleType.TRUCK: 0.08,
            VehicleType.BICYCLE: 0.02
        }
        
        # Delhi weather (dust storms and fog)
        delhi_weather = {
            WeatherType.CLEAR: 0.5,
            WeatherType.LIGHT_RAIN: 0.15,
            WeatherType.HEAVY_RAIN: 0.05,
            WeatherType.FOG: 0.15,
            WeatherType.DUST_STORM: 0.15
        }
        
        traffic_config = IndianTrafficConfig(
            vehicle_mix_ratios=delhi_vehicle_mix,
            weather_probabilities=delhi_weather,
            spawn_rate=0.6,
            max_vehicles=1000
        )
        
        return ScenarioTemplate(
            template_id="delhi_roundabout",
            name="Delhi Roundabout",
            description="Major roundabout in Delhi with mixed heavy traffic, dust storms, and winter fog conditions",
            category="intersection",
            traffic_config=traffic_config,
            simulation_duration=3600.0,
            time_of_day=16,  # Afternoon
            day_of_week=3,   # Thursday
            weather_type=WeatherType.DUST_STORM,
            weather_intensity=0.7,
            network_bounds={
                "north": 28.6139,
                "south": 28.6119,
                "east": 77.2090,
                "west": 77.2070
            },
            custom_parameters={
                "intersection_type": "roundabout",
                "roundabout_diameter": 80,  # meters
                "entry_lanes": 3,
                "exit_lanes": 3,
                "central_island": True,
                "visibility_issues": True
            }
        )
    
    @staticmethod
    def create_accident_emergency_template() -> ScenarioTemplate:
        """Create template for traffic accident emergency scenario"""
        
        traffic_config = IndianTrafficConfig()
        
        # Define accident scenario
        accident_scenario = {
            "scenario_type": "ACCIDENT",
            "severity": "HIGH",
            "location": {"x": 0.0, "y": 0.0, "z": 0.0},
            "estimated_duration_minutes": 45,
            "lanes_blocked": 2,
            "vehicles_involved": 3,
            "emergency_services": ["ambulance", "police", "tow_truck"],
            "traffic_diversion": True
        }
        
        return ScenarioTemplate(
            template_id="accident_emergency",
            name="Multi-Vehicle Accident",
            description="Major traffic accident scenario with emergency response, lane blockage, and traffic diversion",
            category="emergency",
            traffic_config=traffic_config,
            simulation_duration=3600.0,
            time_of_day=14,  # Afternoon
            day_of_week=5,   # Saturday
            weather_type=WeatherType.CLEAR,
            weather_intensity=1.0,
            emergency_scenarios=[accident_scenario],
            custom_parameters={
                "emergency_response_time": 8,  # minutes
                "tow_truck_arrival_time": 25,  # minutes
                "police_traffic_management": True,
                "media_presence": False,
                "crowd_gathering": True
            }
        )
    
    @staticmethod
    def create_monsoon_flooding_template() -> ScenarioTemplate:
        """Create template for monsoon flooding emergency"""
        
        # Reduced vehicle mix during flooding
        flooding_vehicle_mix = {
            VehicleType.CAR: 0.25,
            VehicleType.MOTORCYCLE: 0.20,
            VehicleType.AUTO_RICKSHAW: 0.15,
            VehicleType.BUS: 0.25,  # Increased bus usage
            VehicleType.TRUCK: 0.10,
            VehicleType.BICYCLE: 0.05
        }
        
        traffic_config = IndianTrafficConfig(
            vehicle_mix_ratios=flooding_vehicle_mix,
            spawn_rate=0.3,  # Reduced traffic during flooding
            max_vehicles=500
        )
        
        # Define flooding scenario
        flooding_scenario = {
            "scenario_type": "FLOODING",
            "severity": "CRITICAL",
            "location": {"x": 100.0, "y": 100.0, "z": 0.0},
            "estimated_duration_minutes": 180,  # 3 hours
            "water_level": 0.8,  # meters
            "affected_area_radius": 500,  # meters
            "road_closure": True,
            "alternative_routes": True
        }
        
        return ScenarioTemplate(
            template_id="monsoon_flooding",
            name="Monsoon Flooding",
            description="Heavy monsoon flooding scenario with road closures, reduced traffic, and emergency rerouting",
            category="emergency",
            traffic_config=traffic_config,
            simulation_duration=7200.0,  # 2 hours
            time_of_day=11,  # Late morning
            day_of_week=2,   # Wednesday
            weather_type=WeatherType.HEAVY_RAIN,
            weather_intensity=1.0,
            emergency_scenarios=[flooding_scenario],
            custom_parameters={
                "drainage_capacity": "poor",
                "water_logging_areas": ["low_lying_roads", "underpasses"],
                "traffic_police_deployment": True,
                "public_transport_disruption": True,
                "emergency_shelters": True
            }
        )
    
    @staticmethod
    def create_construction_zone_template() -> ScenarioTemplate:
        """Create template for road construction scenario"""
        
        traffic_config = IndianTrafficConfig(
            spawn_rate=0.5,  # Reduced due to construction
            max_vehicles=800
        )
        
        # Define construction scenario
        construction_scenario = {
            "scenario_type": "CONSTRUCTION",
            "severity": "MEDIUM",
            "location": {"x": 200.0, "y": 50.0, "z": 0.0},
            "estimated_duration_minutes": 480,  # 8 hours (full day work)
            "lanes_blocked": 1,
            "work_type": "road_resurfacing",
            "equipment": ["excavator", "roller", "asphalt_truck"],
            "worker_safety_zone": True
        }
        
        return ScenarioTemplate(
            template_id="construction_zone",
            name="Road Construction Zone",
            description="Active road construction with lane restrictions, reduced speeds, and worker safety considerations",
            category="emergency",
            traffic_config=traffic_config,
            simulation_duration=3600.0,
            time_of_day=10,  # Morning work hours
            day_of_week=1,   # Tuesday
            weather_type=WeatherType.CLEAR,
            weather_intensity=1.0,
            emergency_scenarios=[construction_scenario],
            custom_parameters={
                "speed_limit_reduction": 0.5,  # 50% of normal speed
                "flagman_present": True,
                "construction_signs": True,
                "dust_generation": True,
                "noise_levels": "high"
            }
        )
    
    @staticmethod
    def create_festival_traffic_template() -> ScenarioTemplate:
        """Create template for festival/celebration traffic"""
        
        # Festival vehicle mix (more private vehicles, fewer commercial)
        festival_vehicle_mix = {
            VehicleType.CAR: 0.50,
            VehicleType.MOTORCYCLE: 0.35,
            VehicleType.AUTO_RICKSHAW: 0.10,
            VehicleType.BUS: 0.03,
            VehicleType.TRUCK: 0.01,  # Restricted during festivals
            VehicleType.BICYCLE: 0.01
        }
        
        # Festival peak hours (evening celebrations)
        festival_peak_hours = {
            6: 1.2, 7: 1.5, 8: 2.0, 9: 2.5, 10: 2.8,
            11: 2.5, 12: 2.2, 13: 2.0, 14: 2.5, 15: 3.0,
            16: 3.5, 17: 4.0, 18: 4.5, 19: 5.0, 20: 4.8,
            21: 4.2, 22: 3.5, 23: 2.8, 0: 2.0, 1: 1.5,
            2: 1.0, 3: 0.8, 4: 0.6, 5: 1.0
        }
        
        traffic_config = IndianTrafficConfig(
            vehicle_mix_ratios=festival_vehicle_mix,
            peak_hour_multipliers=festival_peak_hours,
            spawn_rate=1.2,  # Increased festival traffic
            max_vehicles=2000
        )
        
        return ScenarioTemplate(
            template_id="festival_traffic",
            name="Festival Traffic",
            description="Heavy festival traffic with increased private vehicle usage, restricted commercial traffic, and evening peak celebrations",
            category="peak_hour",
            traffic_config=traffic_config,
            simulation_duration=5400.0,  # 1.5 hours
            time_of_day=19,  # Evening celebrations
            day_of_week=6,   # Sunday
            weather_type=WeatherType.CLEAR,
            weather_intensity=1.0,
            custom_parameters={
                "festival_type": "diwali",
                "commercial_restrictions": True,
                "increased_pedestrians": True,
                "temporary_parking": True,
                "street_decorations": True,
                "noise_levels": "very_high",
                "police_deployment": "heavy"
            }
        )
    
    @staticmethod
    def create_early_morning_template() -> ScenarioTemplate:
        """Create template for early morning low-traffic scenario"""
        
        # Early morning vehicle mix (more commercial vehicles)
        morning_vehicle_mix = {
            VehicleType.CAR: 0.20,
            VehicleType.MOTORCYCLE: 0.15,
            VehicleType.AUTO_RICKSHAW: 0.05,
            VehicleType.BUS: 0.20,
            VehicleType.TRUCK: 0.35,  # Delivery trucks
            VehicleType.BICYCLE: 0.05
        }
        
        traffic_config = IndianTrafficConfig(
            vehicle_mix_ratios=morning_vehicle_mix,
            spawn_rate=0.2,  # Low traffic
            max_vehicles=300
        )
        
        return ScenarioTemplate(
            template_id="early_morning",
            name="Early Morning Traffic",
            description="Low-density early morning traffic with delivery trucks, buses, and minimal private vehicles",
            category="peak_hour",
            traffic_config=traffic_config,
            simulation_duration=3600.0,
            time_of_day=5,   # Early morning
            day_of_week=1,   # Tuesday
            weather_type=WeatherType.FOG,
            weather_intensity=0.8,
            custom_parameters={
                "visibility": "poor",
                "delivery_activity": "high",
                "street_cleaning": True,
                "milk_vendors": True,
                "newspaper_delivery": True
            }
        )
    
    @staticmethod
    def create_t_junction_template() -> ScenarioTemplate:
        """Create template for T-junction intersection"""
        
        traffic_config = IndianTrafficConfig()
        
        return ScenarioTemplate(
            template_id="t_junction",
            name="T-Junction Intersection",
            description="Typical T-junction with right-of-way conflicts and mixed vehicle interactions",
            category="intersection",
            traffic_config=traffic_config,
            simulation_duration=3600.0,
            time_of_day=15,  # Afternoon
            day_of_week=2,   # Wednesday
            weather_type=WeatherType.CLEAR,
            weather_intensity=1.0,
            custom_parameters={
                "intersection_type": "t_junction",
                "traffic_signals": False,
                "right_of_way_rules": "informal",
                "turning_conflicts": True,
                "pedestrian_crossings": 2
            }
        )


def create_all_default_templates() -> Dict[str, ScenarioTemplate]:
    """Create all default Indian traffic scenario templates"""
    
    templates = {}
    
    # Intersection templates
    templates["mumbai_intersection"] = IndianScenarioTemplates.create_mumbai_intersection_template()
    templates["delhi_roundabout"] = IndianScenarioTemplates.create_delhi_roundabout_template()
    templates["t_junction"] = IndianScenarioTemplates.create_t_junction_template()
    
    # Regional templates
    templates["bangalore_tech_corridor"] = IndianScenarioTemplates.create_bangalore_tech_corridor_template()
    
    # Emergency templates
    templates["accident_emergency"] = IndianScenarioTemplates.create_accident_emergency_template()
    templates["monsoon_flooding"] = IndianScenarioTemplates.create_monsoon_flooding_template()
    templates["construction_zone"] = IndianScenarioTemplates.create_construction_zone_template()
    
    # Peak hour templates
    templates["festival_traffic"] = IndianScenarioTemplates.create_festival_traffic_template()
    templates["early_morning"] = IndianScenarioTemplates.create_early_morning_template()
    
    return templates


def initialize_default_templates(scenario_manager) -> int:
    """Initialize all default templates in a scenario manager"""
    
    templates = create_all_default_templates()
    saved_count = 0
    
    for template_id, template in templates.items():
        try:
            scenario_manager.save_template(template, overwrite=True)
            saved_count += 1
        except Exception as e:
            print(f"Error saving template '{template_id}': {str(e)}")
    
    return saved_count