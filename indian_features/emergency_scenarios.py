"""
Emergency Scenarios Module

This module implements emergency scenario handling for Indian traffic simulation,
including accidents, flooding, road closures, and dynamic rerouting capabilities.
"""

import random
import math
import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from .enums import EmergencyType, SeverityLevel, VehicleType, WeatherType
from .interfaces import Point3D
from .mixed_traffic_manager import MixedTrafficManager


@dataclass
class EmergencyScenario:
    """Represents an emergency scenario affecting traffic"""
    scenario_id: str
    scenario_type: EmergencyType
    location: Point3D
    affected_edges: List[Tuple[int, int]]
    severity: SeverityLevel
    start_time: datetime
    estimated_duration: timedelta
    description: str
    
    # Impact parameters
    lanes_blocked: int = 0
    speed_reduction_factor: float = 1.0  # 1.0 = no reduction, 0.0 = complete stop
    accessibility: float = 1.0  # 1.0 = fully accessible, 0.0 = completely blocked
    
    # Propagation parameters
    congestion_radius: float = 500.0  # meters
    congestion_severity: float = 0.5  # 0.0 to 1.0
    
    # Status tracking
    is_active: bool = True
    vehicles_affected: Set[str] = field(default_factory=set)
    rerouted_vehicles: Set[str] = field(default_factory=set)
    
    def __post_init__(self):
        """Calculate derived parameters based on scenario type and severity"""
        self._calculate_impact_parameters()
    
    def _calculate_impact_parameters(self):
        """Calculate impact parameters based on emergency type and severity"""
        
        # Base parameters by emergency type
        type_parameters = {
            EmergencyType.ACCIDENT: {
                'base_lanes_blocked': 1,
                'base_speed_reduction': 0.3,
                'base_accessibility': 0.7,
                'base_congestion_radius': 300.0,
                'base_congestion_severity': 0.6
            },
            EmergencyType.FLOODING: {
                'base_lanes_blocked': 2,
                'base_speed_reduction': 0.1,
                'base_accessibility': 0.2,
                'base_congestion_radius': 800.0,
                'base_congestion_severity': 0.8
            },
            EmergencyType.ROAD_CLOSURE: {
                'base_lanes_blocked': 99,  # All lanes
                'base_speed_reduction': 0.0,
                'base_accessibility': 0.0,
                'base_congestion_radius': 600.0,
                'base_congestion_severity': 0.9
            },
            EmergencyType.CONSTRUCTION: {
                'base_lanes_blocked': 1,
                'base_speed_reduction': 0.5,
                'base_accessibility': 0.8,
                'base_congestion_radius': 200.0,
                'base_congestion_severity': 0.4
            },
            EmergencyType.VEHICLE_BREAKDOWN: {
                'base_lanes_blocked': 1,
                'base_speed_reduction': 0.6,
                'base_accessibility': 0.9,
                'base_congestion_radius': 150.0,
                'base_congestion_severity': 0.3
            }
        }
        
        params = type_parameters.get(self.scenario_type, type_parameters[EmergencyType.ACCIDENT])
        
        # Severity multipliers
        severity_multipliers = {
            SeverityLevel.LOW: 0.5,
            SeverityLevel.MEDIUM: 1.0,
            SeverityLevel.HIGH: 1.5,
            SeverityLevel.CRITICAL: 2.0
        }
        
        multiplier = severity_multipliers.get(self.severity, 1.0)
        
        # Calculate final parameters
        self.lanes_blocked = max(1, int(params['base_lanes_blocked'] * multiplier))
        self.speed_reduction_factor = max(0.0, params['base_speed_reduction'] / multiplier)
        self.accessibility = max(0.0, params['base_accessibility'] / multiplier)
        self.congestion_radius = params['base_congestion_radius'] * multiplier
        self.congestion_severity = min(1.0, params['base_congestion_severity'] * multiplier)
    
    def is_edge_affected(self, edge_id: Tuple[int, int]) -> bool:
        """Check if an edge is directly affected by this emergency"""
        return edge_id in self.affected_edges
    
    def is_in_congestion_area(self, position: Point3D) -> bool:
        """Check if a position is within the congestion area"""
        distance = math.sqrt(
            (position.x - self.location.x)**2 + 
            (position.y - self.location.y)**2
        )
        return distance <= self.congestion_radius
    
    def get_congestion_impact(self, position: Point3D) -> float:
        """Get congestion impact factor based on distance from emergency"""
        if not self.is_in_congestion_area(position):
            return 0.0
        
        distance = math.sqrt(
            (position.x - self.location.x)**2 + 
            (position.y - self.location.y)**2
        )
        
        # Linear decay with distance
        impact_factor = 1.0 - (distance / self.congestion_radius)
        return self.congestion_severity * impact_factor
    
    def should_trigger_rerouting(self) -> bool:
        """Determine if this emergency should trigger rerouting"""
        return (self.accessibility < 0.5 or 
                self.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL])
    
    def get_estimated_clearance_time(self) -> datetime:
        """Get estimated time when emergency will be cleared"""
        return self.start_time + self.estimated_duration
    
    def is_expired(self, current_time: datetime) -> bool:
        """Check if emergency scenario has expired"""
        return current_time > self.get_estimated_clearance_time()


class EmergencyManager:
    """Manages emergency scenarios and their effects on traffic simulation"""
    
    def __init__(self, graph: nx.Graph, mixed_traffic_manager: MixedTrafficManager):
        """Initialize emergency manager"""
        self.graph = graph
        self.mixed_traffic_manager = mixed_traffic_manager
        
        # Active emergencies
        self.active_emergencies: Dict[str, EmergencyScenario] = {}
        self.emergency_counter = 0
        
        # Rerouting system
        self.blocked_edges: Set[Tuple[int, int]] = set()
        self.alternative_routes_cache: Dict[Tuple[int, int], List[List[int]]] = {}
        
        # Emergency response parameters
        self.emergency_probabilities = {
            EmergencyType.ACCIDENT: 0.001,  # Per simulation step
            EmergencyType.VEHICLE_BREAKDOWN: 0.0005,
            EmergencyType.FLOODING: 0.0001,
            EmergencyType.ROAD_CLOSURE: 0.00005,
            EmergencyType.CONSTRUCTION: 0.00002
        }
        
        # Weather-dependent probability multipliers
        self.weather_emergency_multipliers = {
            WeatherType.CLEAR: 1.0,
            WeatherType.LIGHT_RAIN: 1.5,
            WeatherType.HEAVY_RAIN: 3.0,
            WeatherType.FOG: 2.0,
            WeatherType.DUST_STORM: 2.5
        }
        
        # Statistics
        self.total_emergencies_created = 0
        self.total_vehicles_rerouted = 0
        self.emergency_history: List[EmergencyScenario] = []
    
    def create_emergency_scenario(self, emergency_type: EmergencyType, 
                                location: Optional[Point3D] = None,
                                affected_edges: Optional[List[Tuple[int, int]]] = None,
                                severity: Optional[SeverityLevel] = None) -> EmergencyScenario:
        """Create a new emergency scenario"""
        
        # Generate unique ID
        self.emergency_counter += 1
        scenario_id = f"EMERGENCY_{emergency_type.name}_{self.emergency_counter:04d}"
        
        # Determine location if not provided
        if location is None:
            location = self._select_random_location()
        
        # Determine affected edges if not provided
        if affected_edges is None:
            affected_edges = self._find_nearby_edges(location, radius=100.0)
        
        # Determine severity if not provided
        if severity is None:
            severity = self._determine_random_severity(emergency_type)
        
        # Estimate duration based on type and severity
        duration = self._estimate_emergency_duration(emergency_type, severity)
        
        # Generate description
        description = self._generate_emergency_description(emergency_type, severity, location)
        
        # Create scenario
        scenario = EmergencyScenario(
            scenario_id=scenario_id,
            scenario_type=emergency_type,
            location=location,
            affected_edges=affected_edges,
            severity=severity,
            start_time=datetime.now(),
            estimated_duration=duration,
            description=description
        )
        
        # Add to active emergencies
        self.active_emergencies[scenario_id] = scenario
        self.total_emergencies_created += 1
        
        # Update blocked edges
        if scenario.accessibility < 0.5:
            self.blocked_edges.update(affected_edges)
        
        return scenario
    
    def create_random_emergency(self, current_weather: WeatherType = WeatherType.CLEAR) -> Optional[EmergencyScenario]:
        """Create a random emergency based on probabilities and weather"""
        
        # Calculate weather-adjusted probabilities
        weather_multiplier = self.weather_emergency_multipliers.get(current_weather, 1.0)
        
        # Check if any emergency should occur
        total_probability = sum(self.emergency_probabilities.values()) * weather_multiplier
        
        if random.random() > total_probability:
            return None
        
        # Select emergency type based on weighted probabilities
        emergency_types = list(self.emergency_probabilities.keys())
        probabilities = [self.emergency_probabilities[et] * weather_multiplier for et in emergency_types]
        
        # Normalize probabilities
        total_prob = sum(probabilities)
        probabilities = [p / total_prob for p in probabilities]
        
        # Select emergency type
        rand_val = random.random()
        cumulative_prob = 0.0
        selected_type = emergency_types[0]
        
        for emergency_type, prob in zip(emergency_types, probabilities):
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                selected_type = emergency_type
                break
        
        # Weather-specific emergency types
        if current_weather == WeatherType.HEAVY_RAIN:
            if random.random() < 0.3:  # 30% chance of flooding in heavy rain
                selected_type = EmergencyType.FLOODING
        
        return self.create_emergency_scenario(selected_type)
    
    def update_emergencies(self, current_time: datetime) -> List[str]:
        """Update emergency scenarios and remove expired ones"""
        expired_emergencies = []
        
        for scenario_id, scenario in list(self.active_emergencies.items()):
            if scenario.is_expired(current_time):
                expired_emergencies.append(scenario_id)
                
                # Remove from active emergencies
                del self.active_emergencies[scenario_id]
                
                # Remove blocked edges
                for edge in scenario.affected_edges:
                    self.blocked_edges.discard(edge)
                
                # Add to history
                scenario.is_active = False
                self.emergency_history.append(scenario)
        
        return expired_emergencies
    
    def find_alternative_routes(self, origin: int, destination: int, 
                              blocked_edges: Optional[Set[Tuple[int, int]]] = None) -> List[List[int]]:
        """Find alternative routes avoiding blocked edges"""
        
        if blocked_edges is None:
            blocked_edges = self.blocked_edges
        
        # Check cache first
        cache_key = (origin, destination)
        if cache_key in self.alternative_routes_cache and not blocked_edges:
            return self.alternative_routes_cache[cache_key]
        
        # Create temporary graph without blocked edges
        temp_graph = self.graph.copy()
        for u, v in blocked_edges:
            if temp_graph.has_edge(u, v):
                temp_graph.remove_edge(u, v)
        
        alternative_routes = []
        
        try:
            # Find shortest path
            shortest_path = nx.shortest_path(temp_graph, origin, destination, weight='travel_time')
            alternative_routes.append(shortest_path)
            
            # Find additional alternative paths using different algorithms
            try:
                # Try to find k shortest paths (simplified approach)
                for _ in range(2):  # Find up to 2 additional routes
                    # Remove some edges from the shortest path to force alternatives
                    modified_graph = temp_graph.copy()
                    if len(shortest_path) > 2:
                        # Remove middle edge
                        mid_idx = len(shortest_path) // 2
                        u, v = shortest_path[mid_idx], shortest_path[mid_idx + 1]
                        if modified_graph.has_edge(u, v):
                            modified_graph.remove_edge(u, v)
                    
                    alt_path = nx.shortest_path(modified_graph, origin, destination, weight='travel_time')
                    if alt_path != shortest_path and alt_path not in alternative_routes:
                        alternative_routes.append(alt_path)
                        
            except nx.NetworkXNoPath:
                pass  # No additional paths found
                
        except nx.NetworkXNoPath:
            # No path available, return empty list
            pass
        
        # Cache result if no blocked edges (static routes)
        if not blocked_edges:
            self.alternative_routes_cache[cache_key] = alternative_routes
        
        return alternative_routes
    
    def reroute_vehicle(self, vehicle_id: str, current_position: int, 
                       destination: int) -> Optional[List[int]]:
        """Reroute a vehicle around emergency scenarios"""
        
        # Find alternative routes
        alternative_routes = self.find_alternative_routes(current_position, destination)
        
        if not alternative_routes:
            return None
        
        # Select best alternative route (shortest travel time)
        best_route = None
        best_travel_time = float('inf')
        
        for route in alternative_routes:
            travel_time = self._calculate_route_travel_time(route)
            if travel_time < best_travel_time:
                best_travel_time = travel_time
                best_route = route
        
        if best_route:
            # Track rerouting
            self.total_vehicles_rerouted += 1
            
            # Mark vehicle as rerouted in relevant emergencies
            for scenario in self.active_emergencies.values():
                if vehicle_id in scenario.vehicles_affected:
                    scenario.rerouted_vehicles.add(vehicle_id)
        
        return best_route
    
    def get_emergency_impact_on_edge(self, edge_id: Tuple[int, int]) -> Dict[str, float]:
        """Get combined emergency impact on a specific edge"""
        
        impact = {
            'speed_reduction_factor': 1.0,
            'accessibility': 1.0,
            'congestion_factor': 0.0,
            'is_blocked': False
        }
        
        for scenario in self.active_emergencies.values():
            if scenario.is_edge_affected(edge_id):
                # Direct impact
                impact['speed_reduction_factor'] = min(
                    impact['speed_reduction_factor'], 
                    scenario.speed_reduction_factor
                )
                impact['accessibility'] = min(
                    impact['accessibility'], 
                    scenario.accessibility
                )
                
                if scenario.accessibility < 0.1:
                    impact['is_blocked'] = True
            
            else:
                # Check for congestion impact
                u, v = edge_id
                if self.graph.has_node(u) and self.graph.has_node(v):
                    # Use edge midpoint for congestion calculation
                    u_data = self.graph.nodes[u]
                    v_data = self.graph.nodes[v]
                    
                    edge_midpoint = Point3D(
                        x=(u_data.get('x', 0) + v_data.get('x', 0)) / 2,
                        y=(u_data.get('y', 0) + v_data.get('y', 0)) / 2,
                        z=0
                    )
                    
                    congestion_impact = scenario.get_congestion_impact(edge_midpoint)
                    impact['congestion_factor'] = max(
                        impact['congestion_factor'], 
                        congestion_impact
                    )
        
        return impact
    
    def get_affected_vehicles(self, vehicle_positions: Dict[str, Point3D]) -> Dict[str, List[str]]:
        """Get vehicles affected by each emergency scenario"""
        
        affected_vehicles = {}
        
        for scenario_id, scenario in self.active_emergencies.items():
            affected_vehicles[scenario_id] = []
            
            for vehicle_id, position in vehicle_positions.items():
                if scenario.is_in_congestion_area(position):
                    affected_vehicles[scenario_id].append(vehicle_id)
                    scenario.vehicles_affected.add(vehicle_id)
        
        return affected_vehicles
    
    def get_emergency_statistics(self) -> Dict[str, Any]:
        """Get emergency management statistics"""
        
        active_by_type = {}
        for scenario in self.active_emergencies.values():
            emergency_type = scenario.scenario_type.name
            active_by_type[emergency_type] = active_by_type.get(emergency_type, 0) + 1
        
        return {
            'active_emergencies': len(self.active_emergencies),
            'active_by_type': active_by_type,
            'total_emergencies_created': self.total_emergencies_created,
            'total_vehicles_rerouted': self.total_vehicles_rerouted,
            'blocked_edges': len(self.blocked_edges),
            'emergency_history_count': len(self.emergency_history)
        }
    
    def _select_random_location(self) -> Point3D:
        """Select a random location on the road network"""
        if not self.graph.nodes:
            return Point3D(0, 0, 0)
        
        # Select random node
        node_id = random.choice(list(self.graph.nodes()))
        node_data = self.graph.nodes[node_id]
        
        return Point3D(
            x=node_data.get('x', 0),
            y=node_data.get('y', 0),
            z=0
        )
    
    def _find_nearby_edges(self, location: Point3D, radius: float) -> List[Tuple[int, int]]:
        """Find edges near a location"""
        nearby_edges = []
        
        for u, v in self.graph.edges():
            u_data = self.graph.nodes[u]
            v_data = self.graph.nodes[v]
            
            # Calculate distance to edge (simplified - use midpoint)
            edge_midpoint_x = (u_data.get('x', 0) + v_data.get('x', 0)) / 2
            edge_midpoint_y = (u_data.get('y', 0) + v_data.get('y', 0)) / 2
            
            distance = math.sqrt(
                (location.x - edge_midpoint_x)**2 + 
                (location.y - edge_midpoint_y)**2
            )
            
            if distance <= radius:
                nearby_edges.append((u, v))
        
        return nearby_edges[:5]  # Limit to 5 edges
    
    def _determine_random_severity(self, emergency_type: EmergencyType) -> SeverityLevel:
        """Determine random severity based on emergency type"""
        
        severity_probabilities = {
            EmergencyType.ACCIDENT: {
                SeverityLevel.LOW: 0.4,
                SeverityLevel.MEDIUM: 0.4,
                SeverityLevel.HIGH: 0.15,
                SeverityLevel.CRITICAL: 0.05
            },
            EmergencyType.FLOODING: {
                SeverityLevel.LOW: 0.2,
                SeverityLevel.MEDIUM: 0.3,
                SeverityLevel.HIGH: 0.3,
                SeverityLevel.CRITICAL: 0.2
            },
            EmergencyType.ROAD_CLOSURE: {
                SeverityLevel.MEDIUM: 0.5,
                SeverityLevel.HIGH: 0.3,
                SeverityLevel.CRITICAL: 0.2
            },
            EmergencyType.CONSTRUCTION: {
                SeverityLevel.LOW: 0.6,
                SeverityLevel.MEDIUM: 0.3,
                SeverityLevel.HIGH: 0.1
            },
            EmergencyType.VEHICLE_BREAKDOWN: {
                SeverityLevel.LOW: 0.7,
                SeverityLevel.MEDIUM: 0.25,
                SeverityLevel.HIGH: 0.05
            }
        }
        
        probs = severity_probabilities.get(emergency_type, {SeverityLevel.MEDIUM: 1.0})
        
        rand_val = random.random()
        cumulative_prob = 0.0
        
        for severity, prob in probs.items():
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                return severity
        
        return SeverityLevel.MEDIUM
    
    def _estimate_emergency_duration(self, emergency_type: EmergencyType, 
                                   severity: SeverityLevel) -> timedelta:
        """Estimate emergency duration based on type and severity"""
        
        base_durations = {
            EmergencyType.ACCIDENT: 30,  # minutes
            EmergencyType.FLOODING: 180,
            EmergencyType.ROAD_CLOSURE: 120,
            EmergencyType.CONSTRUCTION: 480,  # 8 hours
            EmergencyType.VEHICLE_BREAKDOWN: 20
        }
        
        severity_multipliers = {
            SeverityLevel.LOW: 0.5,
            SeverityLevel.MEDIUM: 1.0,
            SeverityLevel.HIGH: 2.0,
            SeverityLevel.CRITICAL: 3.0
        }
        
        base_minutes = base_durations.get(emergency_type, 60)
        multiplier = severity_multipliers.get(severity, 1.0)
        
        # Add randomness
        final_minutes = base_minutes * multiplier * random.uniform(0.7, 1.5)
        
        return timedelta(minutes=int(final_minutes))
    
    def _generate_emergency_description(self, emergency_type: EmergencyType, 
                                      severity: SeverityLevel, location: Point3D) -> str:
        """Generate human-readable emergency description"""
        
        severity_adjectives = {
            SeverityLevel.LOW: "minor",
            SeverityLevel.MEDIUM: "moderate",
            SeverityLevel.HIGH: "major",
            SeverityLevel.CRITICAL: "severe"
        }
        
        type_descriptions = {
            EmergencyType.ACCIDENT: "traffic accident",
            EmergencyType.FLOODING: "road flooding",
            EmergencyType.ROAD_CLOSURE: "road closure",
            EmergencyType.CONSTRUCTION: "construction work",
            EmergencyType.VEHICLE_BREAKDOWN: "vehicle breakdown"
        }
        
        severity_adj = severity_adjectives.get(severity, "moderate")
        type_desc = type_descriptions.get(emergency_type, "incident")
        
        return f"{severity_adj.title()} {type_desc} at location ({location.x:.1f}, {location.y:.1f})"
    
    def _calculate_route_travel_time(self, route: List[int]) -> float:
        """Calculate total travel time for a route"""
        total_time = 0.0
        
        for u, v in zip(route[:-1], route[1:]):
            if self.graph.has_edge(u, v):
                edge_data = self.graph[u][v]
                if isinstance(edge_data, dict):
                    # MultiGraph - get first edge
                    edge_data = edge_data.get(0, {})
                travel_time = edge_data.get('travel_time', 10.0)
                total_time += travel_time
        
        return total_time