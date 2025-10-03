import random
from typing import List, Tuple, Iterable, Optional, Dict, Any
from datetime import datetime, timedelta

import osmnx as ox
import networkx as nx
from shapely.geometry import LineString, MultiLineString, GeometryCollection
import folium
import simpy

from helpers import *
from routers import *
from indian_features.vehicle_factory import IndianVehicleFactory, IndianVehicle
from indian_features.behavior_model import IndianBehaviorModel
from indian_features.mixed_traffic_manager import MixedTrafficManager
from indian_features.road_analyzer import IndianRoadAnalyzer, RoadConditionMapper
from indian_features.weather_conditions import WeatherManager, TimeOfDayManager, WeatherCondition
from indian_features.emergency_scenarios import EmergencyManager, EmergencyScenario
from indian_features.interfaces import Point3D
from indian_features.enums import VehicleType, WeatherType, RoadQuality, EmergencyType, SeverityLevel
from indian_features.config import IndianTrafficConfig

class TrafficModel:
    def __init__(self, G, max_vehicles=14, spawn_rate_per_s=1/18.0, sim_seconds=240, 
                 use_indian_features=False, indian_config: Optional[IndianTrafficConfig] = None):
        self.G = G
        self.env = simpy.Environment()
        self.max_vehicles = max_vehicles
        self.spawn_rate = spawn_rate_per_s
        self.sim_seconds = sim_seconds
        self.routes = {}       # vid -> path (list of node IDs)
        self.start_nodes = {}  # vid -> start node id
        self.end_nodes = {}    # vid -> end node id
        
        # Indian features integration
        self.use_indian_features = use_indian_features
        if self.use_indian_features:
            self.indian_config = indian_config or IndianTrafficConfig()
            self.indian_vehicle_factory = IndianVehicleFactory(self.indian_config)
            self.behavior_model = IndianBehaviorModel()
            self.mixed_traffic_manager = MixedTrafficManager(self.behavior_model)
            self.road_analyzer = IndianRoadAnalyzer()
            self.road_condition_mapper = RoadConditionMapper(self.road_analyzer)
            
            # Weather and time management
            self.weather_manager = WeatherManager()
            self.time_manager = TimeOfDayManager()
            
            # Emergency scenario management
            self.emergency_manager = EmergencyManager(self.G, self.mixed_traffic_manager)
            
            # Initialize road conditions
            self.road_condition_mapper.initialize_road_states(self.G)
            
            # Indian vehicle tracking
            self.indian_vehicles: Dict[int, IndianVehicle] = {}
            self.vehicle_behaviors: Dict[int, Dict[str, Any]] = {}
            
            # Current conditions
            self.current_weather = WeatherType.CLEAR
            self.current_hour = 12  # Default to noon
            self.simulation_start_time = datetime.now()
            
            # Weather and time tracking
            self.weather_update_interval = 60.0  # Update weather every 60 sim seconds
            self.time_update_interval = 30.0  # Update time every 30 sim seconds
            self.emergency_update_interval = 45.0  # Update emergencies every 45 sim seconds
            self.last_weather_update = 0.0
            self.last_time_update = 0.0
            self.last_emergency_update = 0.0
            
            # Emergency tracking
            self.vehicle_rerouting_needed: Dict[int, bool] = {}
            self.emergency_affected_vehicles: Set[int] = set()
        else:
            # Keep original behavior for backward compatibility
            self.indian_config = None
            self.indian_vehicle_factory = None
            self.behavior_model = None
            self.mixed_traffic_manager = None
            self.road_analyzer = None
            self.road_condition_mapper = None
            self.indian_vehicles = {}
            self.vehicle_behaviors = {}

    def drive(self, vid: int, path: List[int]):
        if self.use_indian_features and vid in self.indian_vehicles:
            # Use Indian behavior model for driving
            yield from self._drive_with_indian_behavior(vid, path)
        else:
            # Original driving behavior
            tt_list = route_edge_values(self.G, path, "travel_time", default=4.0)
            for travel_t in tt_list:
                travel_t = max(0.05, float(travel_t or 4.0))
                yield self.env.timeout(travel_t)
    
    def _drive_with_indian_behavior(self, vid: int, path: List[int]):
        """Drive with Indian-specific behavior patterns"""
        indian_vehicle = self.indian_vehicles[vid]
        tt_list = route_edge_values(self.G, path, "travel_time", default=4.0)
        
        current_path = path.copy()
        
        for i, (travel_t, node_pair) in enumerate(zip(tt_list, zip(current_path[:-1], current_path[1:]))):
            # Check for emergency rerouting before proceeding
            if self._should_reroute_vehicle(vid, current_path, i):
                new_route = self._attempt_emergency_rerouting(vid, current_path, i)
                if new_route:
                    # Update route and recalculate travel times
                    current_path = new_route
                    self.routes[vid] = new_route
                    tt_list = route_edge_values(self.G, current_path, "travel_time", default=4.0)
                    # Restart from current position
                    continue
            
            # Get base travel time
            base_travel_time = max(0.05, float(travel_t or 4.0))
            
            # Get road conditions for this edge
            edge_id = node_pair
            road_conditions = self._get_road_conditions_for_edge(edge_id)
            
            # Check for emergency impacts on this edge
            emergency_impact = self.emergency_manager.get_emergency_impact_on_edge(edge_id)
            
            # Apply Indian behavior modifications
            behavior_adjustments = self._calculate_behavior_adjustments(indian_vehicle, road_conditions)
            
            # Apply emergency impacts
            emergency_speed_factor = emergency_impact['speed_reduction_factor']
            congestion_factor = 1.0 + emergency_impact['congestion_factor']  # Increases travel time
            
            # Calculate adjusted travel time
            adjusted_travel_time = (base_travel_time * behavior_adjustments['travel_time_factor'] * 
                                  congestion_factor / max(0.1, emergency_speed_factor))
            
            # Update vehicle position for traffic manager
            if i < len(current_path) - 1:
                current_node = current_path[i + 1]
                node_data = self.G.nodes[current_node]
                position = Point3D(
                    x=node_data.get('x', 0.0),
                    y=node_data.get('y', 0.0),
                    z=0.0
                )
                indian_vehicle.update_position(position)
                self.mixed_traffic_manager.update_vehicle_position(indian_vehicle.vehicle_id, position)
                
                # Check if vehicle is affected by emergencies
                self._check_emergency_vehicle_impact(vid, position)
            
            # Apply horn usage if determined by behavior or emergency stress
            use_horn = behavior_adjustments.get('use_horn', False)
            if emergency_impact['congestion_factor'] > 0.5:
                use_horn = use_horn or (random.random() < 0.3)  # Increased horn usage in emergencies
            
            if use_horn:
                # Horn usage would be logged or processed here
                pass
            
            yield self.env.timeout(adjusted_travel_time)
    
    def _should_reroute_vehicle(self, vid: int, current_path: List[int], current_index: int) -> bool:
        """Check if vehicle should be rerouted due to emergencies"""
        
        if not self.use_indian_features or vid not in self.indian_vehicles:
            return False
        
        # Check if rerouting is needed for this vehicle
        if self.vehicle_rerouting_needed.get(vid, False):
            return True
        
        # Check if any upcoming edges are blocked
        remaining_path = current_path[current_index:]
        for u, v in zip(remaining_path[:-1], remaining_path[1:]):
            edge_impact = self.emergency_manager.get_emergency_impact_on_edge((u, v))
            if edge_impact['is_blocked'] or edge_impact['accessibility'] < 0.3:
                self.vehicle_rerouting_needed[vid] = True
                return True
        
        return False
    
    def _attempt_emergency_rerouting(self, vid: int, current_path: List[int], 
                                   current_index: int) -> Optional[List[int]]:
        """Attempt to reroute vehicle around emergencies"""
        
        if current_index >= len(current_path) - 1:
            return None
        
        current_node = current_path[current_index]
        destination_node = current_path[-1]
        
        # Find alternative route
        alternative_route = self.emergency_manager.reroute_vehicle(
            self.indian_vehicles[vid].vehicle_id, 
            current_node, 
            destination_node
        )
        
        if alternative_route:
            # Mark vehicle as no longer needing rerouting
            self.vehicle_rerouting_needed[vid] = False
            return alternative_route
        
        return None
    
    def _check_emergency_vehicle_impact(self, vid: int, position: Point3D):
        """Check if vehicle is impacted by emergency scenarios"""
        
        vehicle_positions = {self.indian_vehicles[vid].vehicle_id: position}
        affected_vehicles = self.emergency_manager.get_affected_vehicles(vehicle_positions)
        
        # Check if this vehicle is affected by any emergency
        for scenario_id, affected_list in affected_vehicles.items():
            if self.indian_vehicles[vid].vehicle_id in affected_list:
                self.emergency_affected_vehicles.add(vid)
                break
    
    def _get_road_conditions_for_edge(self, edge_id: Tuple[int, int]) -> Dict[str, Any]:
        """Get current road conditions for an edge"""
        if not self.use_indian_features:
            return {}
        
        # Get edge data (handle MultiDiGraph format)
        u, v = edge_id
        edge_data = {}
        if self.G.has_edge(u, v):
            # For MultiDiGraph, get the first edge's data
            edge_data = self.G[u][v][0] if self.G[u][v] else {}
        
        # Get road quality from analyzer
        road_qualities = self.road_analyzer.analyze_road_quality(self.G)
        road_quality = road_qualities.get(edge_id, RoadQuality.GOOD)
        
        # Get dynamic conditions from mapper
        road_state = self.road_condition_mapper._road_states.get(edge_id)
        
        conditions = {
            'quality': road_quality,
            'weather': self.current_weather,
            'lane_count': edge_data.get('lanes', 2),
            'width': edge_data.get('width', 7.0),
            'traffic_density': self._estimate_traffic_density(edge_id),
            'weather_impact': road_state.weather_impact if road_state else 1.0,
            'time_impact': road_state.time_impact if road_state else 1.0,
            'temporary_obstacles': road_state.temporary_obstacles if road_state else [],
            'construction_zones': road_state.construction_zones if road_state else []
        }
        
        return conditions
    
    def _calculate_behavior_adjustments(self, vehicle: IndianVehicle, 
                                      road_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate behavior adjustments based on vehicle and road conditions"""
        
        # Calculate lane discipline
        lane_discipline = self.behavior_model.calculate_lane_discipline(
            vehicle.vehicle_type, road_conditions
        )
        
        # Get weather effects from weather manager
        weather_effects = self.weather_manager.get_current_weather_effects(vehicle.vehicle_type)
        
        # Get time-of-day effects
        time_effects = self.time_manager.get_time_effects_summary(self.current_hour)
        
        # Calculate speed adjustment based on conditions
        base_speed_adjustment = vehicle.calculate_speed_adjustment(
            road_conditions['quality'], road_conditions['weather']
        )
        
        # Apply weather effects
        weather_speed_factor = weather_effects['speed_factor']
        
        # Apply time-of-day effects
        time_speed_factor = time_effects['speed_adjustment']
        
        # Apply weather and time impacts from road conditions
        weather_impact = road_conditions.get('weather_impact', 1.0)
        time_impact = road_conditions.get('time_impact', 1.0)
        
        # Combine all speed factors
        combined_speed_factor = (base_speed_adjustment * weather_speed_factor * 
                               time_speed_factor * weather_impact * time_impact)
        
        # Calculate final travel time factor (inverse of speed)
        travel_time_factor = 1.0 / max(0.1, combined_speed_factor)
        
        # Add randomness based on lane discipline and aggressiveness
        discipline_variance = 1.0 + (1.0 - lane_discipline.discipline_level.value / 4.0) * 0.2
        aggressiveness_factor = time_effects['aggressiveness_multiplier']
        
        # Aggressive drivers in peak hours drive faster (lower travel time)
        if time_effects['is_peak_hour'] and aggressiveness_factor > 1.2:
            travel_time_factor *= random.uniform(0.8, 1.0)
        else:
            travel_time_factor *= random.uniform(0.9, discipline_variance)
        
        # Determine horn usage (increased in bad weather and peak hours)
        traffic_density = road_conditions.get('traffic_density', 0.5)
        base_horn_prob = vehicle.should_use_horn(traffic_density)
        
        # Increase horn usage in bad weather and peak hours
        weather_horn_factor = 1.0 + (1.0 - weather_effects['visibility']) * 0.5
        time_horn_factor = aggressiveness_factor
        
        enhanced_horn_prob = base_horn_prob or (
            random.random() < (0.1 * weather_horn_factor * time_horn_factor)
        )
        
        return {
            'travel_time_factor': travel_time_factor,
            'speed_adjustment': combined_speed_factor,
            'lane_discipline': lane_discipline,
            'use_horn': enhanced_horn_prob,
            'weather_impact': weather_impact,
            'time_impact': time_impact,
            'weather_effects': weather_effects,
            'time_effects': time_effects,
            'visibility': weather_effects['visibility'],
            'road_wetness': weather_effects['road_wetness'],
            'aggressiveness_multiplier': aggressiveness_factor
        }
    
    def _estimate_traffic_density(self, edge_id: Tuple[int, int]) -> float:
        """Estimate current traffic density on an edge"""
        # Simple estimation based on number of vehicles currently on the network
        # In a more sophisticated implementation, this would track vehicles per edge
        total_vehicles = len(self.indian_vehicles) if self.use_indian_features else len(self.routes)
        max_capacity = self.max_vehicles
        
        return min(1.0, total_vehicles / max_capacity) if max_capacity > 0 else 0.0

    def vehicle_source(self):
        vid = 0
        created = 0
        while created < self.max_vehicles:
            orig, dest, path = random_far_nodes(self.G, min_path_seconds=45.0)
            path = normalize_route(path)  # ensure flat list [n0, n1, ...]
            
            if self.use_indian_features:
                # Create Indian vehicle with mixed types
                self._create_indian_vehicle(vid, orig, dest, path)
            else:
                # Original vehicle creation
                self.routes[vid] = path
                self.start_nodes[vid] = orig
                self.end_nodes[vid] = dest
            
            self.env.process(self.drive(vid, path))
            created += 1
            vid += 1
            
            # Apply time-based spawn rate variations for Indian features
            if self.use_indian_features:
                inter_arrival = self._calculate_indian_spawn_interval()
            else:
                inter_arrival = random.expovariate(self.spawn_rate)
            
            yield self.env.timeout(inter_arrival)
    
    def _create_indian_vehicle(self, vid: int, orig: int, dest: int, path: List[int]):
        """Create an Indian vehicle with specific characteristics"""
        
        # Get origin position
        orig_node_data = self.G.nodes[orig]
        origin_position = Point3D(
            x=orig_node_data.get('x', 0.0),
            y=orig_node_data.get('y', 0.0),
            z=0.0
        )
        
        # Get destination position
        dest_node_data = self.G.nodes[dest]
        destination_position = Point3D(
            x=dest_node_data.get('x', 0.0),
            y=dest_node_data.get('y', 0.0),
            z=0.0
        )
        
        # Create Indian vehicle using factory
        indian_vehicle = self.indian_vehicle_factory.create_random_vehicle(
            position=origin_position,
            destination=destination_position
        )
        
        # Set route
        indian_vehicle.route = path
        
        # Store vehicle data
        self.indian_vehicles[vid] = indian_vehicle
        self.routes[vid] = path
        self.start_nodes[vid] = orig
        self.end_nodes[vid] = dest
        
        # Register with traffic manager
        self.mixed_traffic_manager.register_vehicle(indian_vehicle)
        
        # Initialize behavior tracking
        self.vehicle_behaviors[vid] = {
            'vehicle_type': indian_vehicle.vehicle_type.name,
            'behavior_profile': indian_vehicle.behavior_profile.name,
            'lane_discipline_factor': indian_vehicle.behavior_params.lane_discipline_factor,
            'overtaking_aggressiveness': indian_vehicle.behavior_params.overtaking_aggressiveness
        }
    
    def _calculate_indian_spawn_interval(self) -> float:
        """Calculate spawn interval with Indian traffic patterns"""
        
        # Get time-of-day adjusted spawn rate
        adjusted_spawn_rate = self.time_manager.get_spawn_rate_adjustment(
            self.current_hour, self.spawn_rate
        )
        
        # Apply weather effects (bad weather reduces traffic)
        weather_effects = self.weather_manager.get_current_weather_effects(VehicleType.CAR)
        weather_spawn_factor = 0.5 + (weather_effects['visibility'] * 0.5)  # 0.5 to 1.0 range
        
        adjusted_spawn_rate *= weather_spawn_factor
        
        # Add some randomness typical of Indian traffic
        randomness_factor = random.uniform(0.7, 1.3)
        final_spawn_rate = max(0.01, adjusted_spawn_rate * randomness_factor)
        
        return random.expovariate(final_spawn_rate)

    def run(self):
        random.seed(42)
        self.env.process(self.vehicle_source())
        
        if self.use_indian_features:
            # Start dynamic condition updates
            self.env.process(self._dynamic_condition_updater())
            # Start mixed traffic simulation
            self.env.process(self._mixed_traffic_simulator())
        
        self.env.run(until=self.sim_seconds)
    
    def update_weather_conditions(self, weather_type: WeatherType, intensity: float = 1.0):
        """Update weather conditions affecting the simulation"""
        if not self.use_indian_features:
            return
        
        # Create new weather condition
        current_datetime = self.simulation_start_time + timedelta(seconds=self.env.now)
        new_weather = WeatherCondition(
            condition_type=weather_type,
            intensity=intensity,
            visibility=1.0,  # Will be calculated
            road_wetness=0.0,  # Will be calculated
            temperature=30.0,  # Will be set
            wind_speed=10.0,  # Will be set
            duration_minutes=60,  # Default duration
            start_time=current_datetime
        )
        
        # Update weather manager
        self.weather_manager.current_weather = new_weather
        self.current_weather = weather_type
        
        # Update road condition mapper
        self.road_condition_mapper.update_weather_conditions(weather_type.name.lower(), intensity)
    
    def update_time_of_day(self, hour: int):
        """Update time of day effects on traffic"""
        if not self.use_indian_features:
            return
        
        self.current_hour = hour
        self.road_condition_mapper.update_time_effects(hour)
    
    def add_temporary_obstacle(self, edge_id: Tuple[int, int], obstacle_type: str, 
                             severity: str = 'medium', duration_minutes: int = 30) -> str:
        """Add a temporary obstacle to the road network"""
        if not self.use_indian_features:
            return ""
        
        return self.road_condition_mapper.add_temporary_obstacle(
            edge_id, obstacle_type, severity=severity, duration_minutes=duration_minutes
        )
    
    def remove_temporary_obstacle(self, obstacle_id: str) -> bool:
        """Remove a temporary obstacle from the road network"""
        if not self.use_indian_features:
            return False
        
        return self.road_condition_mapper.remove_temporary_obstacle(obstacle_id)
    
    def create_emergency_scenario(self, emergency_type: EmergencyType, 
                                location: Optional[Point3D] = None,
                                severity: Optional[SeverityLevel] = None) -> str:
        """Create an emergency scenario in the simulation"""
        if not self.use_indian_features:
            return ""
        
        scenario = self.emergency_manager.create_emergency_scenario(
            emergency_type, location, severity=severity
        )
        
        # Mark all vehicles for potential rerouting check
        for vid in self.indian_vehicles.keys():
            self.vehicle_rerouting_needed[vid] = True
        
        return scenario.scenario_id
    
    def resolve_emergency_scenario(self, scenario_id: str) -> bool:
        """Manually resolve an emergency scenario"""
        if not self.use_indian_features:
            return False
        
        if scenario_id in self.emergency_manager.active_emergencies:
            scenario = self.emergency_manager.active_emergencies[scenario_id]
            
            # Mark as expired
            scenario.start_time = datetime.now() - scenario.estimated_duration - timedelta(minutes=1)
            
            # Update emergencies to remove expired ones
            current_datetime = self.simulation_start_time + timedelta(seconds=self.env.now)
            self.emergency_manager.update_emergencies(current_datetime)
            
            return True
        
        return False
    
    def get_active_emergencies(self) -> List[Dict[str, Any]]:
        """Get information about active emergency scenarios"""
        if not self.use_indian_features:
            return []
        
        emergencies = []
        for scenario in self.emergency_manager.active_emergencies.values():
            emergencies.append({
                'scenario_id': scenario.scenario_id,
                'type': scenario.scenario_type.name,
                'severity': scenario.severity.name,
                'location': {
                    'x': scenario.location.x,
                    'y': scenario.location.y,
                    'z': scenario.location.z
                },
                'description': scenario.description,
                'affected_edges': len(scenario.affected_edges),
                'vehicles_affected': len(scenario.vehicles_affected),
                'vehicles_rerouted': len(scenario.rerouted_vehicles),
                'estimated_clearance': scenario.get_estimated_clearance_time().isoformat(),
                'congestion_radius': scenario.congestion_radius,
                'accessibility': scenario.accessibility
            })
        
        return emergencies
    
    def _dynamic_condition_updater(self):
        """Process for updating dynamic road conditions during simulation"""
        while True:
            # Update every 30 simulation seconds
            yield self.env.timeout(30.0)
            
            current_sim_time = self.env.now
            
            # Update time of day (simulate time progression)
            if current_sim_time - self.last_time_update >= self.time_update_interval:
                # Advance time by 1 hour every 30 sim seconds for demo
                self.current_hour = (self.current_hour + 1) % 24
                self.update_time_of_day(self.current_hour)
                self.last_time_update = current_sim_time
            
            # Update weather conditions
            if current_sim_time - self.last_weather_update >= self.weather_update_interval:
                # Calculate current simulation time
                sim_time_elapsed = timedelta(seconds=current_sim_time)
                current_datetime = self.simulation_start_time + sim_time_elapsed
                
                # Update weather using weather manager
                new_weather = self.weather_manager.update_weather(current_datetime)
                self.current_weather = new_weather.condition_type
                
                # Update road condition mapper with new weather
                self.road_condition_mapper.update_weather_conditions(
                    new_weather.condition_type.name.lower(), new_weather.intensity
                )
                
                self.last_weather_update = current_sim_time
            
            # Weather-dependent obstacle generation
            weather_effects = self.weather_manager.get_current_weather_effects(VehicleType.CAR)
            obstacle_probability = 0.01 * weather_effects['accident_probability_multiplier']
            
            # Add temporary obstacles based on weather and traffic conditions
            if random.random() < obstacle_probability and len(self.G.edges) > 0:
                edge_list = list(self.G.edges())
                random_edge = random.choice(edge_list)
                
                # Weather-dependent obstacle types
                if self.current_weather == WeatherType.HEAVY_RAIN:
                    obstacle_types = ['flooding', 'accident', 'breakdown']
                elif self.current_weather == WeatherType.FOG:
                    obstacle_types = ['accident', 'breakdown']
                elif self.current_weather == WeatherType.DUST_STORM:
                    obstacle_types = ['accident', 'debris', 'breakdown']
                else:
                    obstacle_types = ['accident', 'breakdown', 'debris']
                
                obstacle_type = random.choice(obstacle_types)
                duration = random.randint(10, 60)
                
                # Longer durations for weather-related obstacles
                if obstacle_type == 'flooding' and self.current_weather == WeatherType.HEAVY_RAIN:
                    duration = random.randint(60, 180)
                
                self.add_temporary_obstacle(random_edge, obstacle_type, duration_minutes=duration)
            
            # Update emergency scenarios
            if current_sim_time - self.last_emergency_update >= self.emergency_update_interval:
                # Update existing emergencies
                current_datetime = self.simulation_start_time + timedelta(seconds=current_sim_time)
                expired_emergencies = self.emergency_manager.update_emergencies(current_datetime)
                
                # Create new random emergencies
                new_emergency = self.emergency_manager.create_random_emergency(self.current_weather)
                if new_emergency:
                    # Mark affected vehicles for potential rerouting
                    for vid in self.indian_vehicles.keys():
                        if vid not in self.vehicle_rerouting_needed:
                            self.vehicle_rerouting_needed[vid] = False
                
                self.last_emergency_update = current_sim_time
    
    def _mixed_traffic_simulator(self):
        """Process for simulating mixed traffic dynamics"""
        while True:
            # Update every 5 simulation seconds
            yield self.env.timeout(5.0)
            
            if len(self.indian_vehicles) > 0:
                # Simulate mixed vehicle dynamics
                dynamics_result = self.mixed_traffic_manager.simulate_mixed_vehicle_dynamics(5.0)
                
                # Apply behavior modifications to vehicles
                vehicle_behaviors = dynamics_result.get('vehicle_behaviors', {})
                for vid, indian_vehicle in self.indian_vehicles.items():
                    vehicle_id = indian_vehicle.vehicle_id
                    if vehicle_id in vehicle_behaviors:
                        behavior_mods = vehicle_behaviors[vehicle_id]
                        # Store behavior modifications for use in driving calculations
                        self.vehicle_behaviors[vid].update(behavior_mods)
    
    def get_simulation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive simulation statistics"""
        stats = {
            'total_vehicles': len(self.routes),
            'simulation_time': self.env.now,
            'max_vehicles': self.max_vehicles,
            'spawn_rate': self.spawn_rate
        }
        
        if self.use_indian_features:
            # Add Indian-specific statistics
            traffic_stats = self.mixed_traffic_manager.get_traffic_statistics()
            factory_stats = self.indian_vehicle_factory.get_vehicle_statistics()
            
            # Get current weather and time effects
            current_weather_condition = self.weather_manager.current_weather
            time_effects = self.time_manager.get_time_effects_summary(self.current_hour)
            weather_effects = self.weather_manager.get_current_weather_effects(VehicleType.CAR)
            
            stats.update({
                'indian_features_enabled': True,
                'current_weather': self.current_weather.name,
                'current_hour': self.current_hour,
                'weather_details': {
                    'type': current_weather_condition.condition_type.name,
                    'intensity': current_weather_condition.intensity,
                    'visibility': current_weather_condition.visibility,
                    'road_wetness': current_weather_condition.road_wetness,
                    'temperature': current_weather_condition.temperature,
                    'wind_speed': current_weather_condition.wind_speed
                },
                'time_effects': {
                    'is_peak_hour': time_effects['is_peak_hour'],
                    'traffic_density_multiplier': time_effects['traffic_density_multiplier'],
                    'speed_adjustment': time_effects['speed_adjustment'],
                    'aggressiveness_multiplier': time_effects['aggressiveness_multiplier'],
                    'period': time_effects['period']
                },
                'weather_effects': {
                    'speed_factor': weather_effects['speed_factor'],
                    'following_distance_factor': weather_effects['following_distance_factor'],
                    'accident_probability_multiplier': weather_effects['accident_probability_multiplier']
                },
                'vehicle_type_distribution': traffic_stats.get('vehicle_type_distribution', {}),
                'emergency_vehicles': traffic_stats.get('emergency_vehicles', 0),
                'active_interactions': traffic_stats.get('active_interactions', 0),
                'congestion_zones': traffic_stats.get('congestion_zones', 0),
                'total_interactions_processed': traffic_stats.get('total_interactions_processed', 0),
                'vehicles_created_by_factory': factory_stats.get('total_vehicles_created', 0),
                'emergency_statistics': self.emergency_manager.get_emergency_statistics(),
                'emergency_affected_vehicles': len(self.emergency_affected_vehicles),
                'vehicles_needing_rerouting': sum(1 for needed in self.vehicle_rerouting_needed.values() if needed)
            })
        else:
            stats['indian_features_enabled'] = False
        
        return stats