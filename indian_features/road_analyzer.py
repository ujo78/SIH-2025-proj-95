"""
Indian Road Analyzer Module

This module implements road condition analysis specific to Indian road networks,
including road quality assessment, pothole detection, and construction zone identification.
"""

import random
import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass

from .interfaces import RoadConditionInterface, Point3D
from .enums import (
    RoadQuality, SurfaceType, MaintenanceLevel, ConstructionStatus, 
    SeverityLevel
)
from .config import RoadConditionConfig


@dataclass
class PotholeLocation:
    """Represents a pothole location on a road segment"""
    position: Point3D
    severity: SeverityLevel
    diameter: float  # meters
    depth: float     # meters
    edge_id: Tuple[int, int]


@dataclass
class ConstructionZone:
    """Represents a construction zone affecting road segments"""
    edge_ids: List[Tuple[int, int]]
    construction_type: ConstructionStatus
    start_date: datetime
    estimated_end_date: datetime
    lanes_affected: int
    speed_limit_reduction: float  # factor (0.0 to 1.0)
    description: str


class IndianRoadAnalyzer(RoadConditionInterface):
    """
    Analyzes Indian road networks for quality assessment, pothole detection,
    and construction zone identification based on OSM data and metadata.
    """
    
    def __init__(self, config: Optional[RoadConditionConfig] = None):
        """Initialize the road analyzer with configuration"""
        self.config = config or RoadConditionConfig()
        self._road_quality_cache: Dict[Tuple[int, int], RoadQuality] = {}
        self._pothole_cache: Dict[Tuple[int, int], List[PotholeLocation]] = {}
        self._construction_zones: List[ConstructionZone] = []
    
    def analyze_road_quality(self, graph: nx.Graph) -> Dict[Tuple[int, int], RoadQuality]:
        """
        Analyze road quality for all edges in the graph based on OSM tags and metadata.
        
        Args:
            graph: NetworkX graph representing the road network
            
        Returns:
            Dictionary mapping edge IDs to RoadQuality enum values
        """
        road_qualities = {}
        
        for u, v, edge_data in graph.edges(data=True):
            edge_id = (u, v)
            
            # Check cache first
            if edge_id in self._road_quality_cache:
                road_qualities[edge_id] = self._road_quality_cache[edge_id]
                continue
            
            # Calculate quality score based on multiple factors
            quality_score = self._calculate_quality_score(edge_data)
            
            # Convert score to quality enum
            if quality_score >= 0.8:
                quality = RoadQuality.EXCELLENT
            elif quality_score >= 0.6:
                quality = RoadQuality.GOOD
            elif quality_score >= 0.4:
                quality = RoadQuality.POOR
            else:
                quality = RoadQuality.VERY_POOR
            
            road_qualities[edge_id] = quality
            self._road_quality_cache[edge_id] = quality
        
        return road_qualities
    
    def detect_potholes(self, edge_data: Dict[str, Any]) -> List[PotholeLocation]:
        """
        Detect potential pothole locations on a road segment using road age and surface type data.
        
        Args:
            edge_data: Dictionary containing edge attributes from OSM
            
        Returns:
            List of PotholeLocation objects representing detected potholes
        """
        edge_id = edge_data.get('edge_id', (0, 0))
        
        # Check cache first
        if edge_id in self._pothole_cache:
            return self._pothole_cache[edge_id]
        
        potholes = []
        
        # Determine surface type and maintenance level
        surface_type = self._get_surface_type(edge_data)
        maintenance_level = self._get_maintenance_level(edge_data)
        road_age = self._estimate_road_age(edge_data)
        
        # Calculate pothole probability based on conditions
        base_probability = self._calculate_pothole_probability(
            surface_type, maintenance_level, road_age
        )
        
        # Determine number of potholes based on road length and probability
        road_length = edge_data.get('length', 100.0)  # meters
        expected_potholes = (road_length / 100.0) * base_probability
        num_potholes = max(0, int(random.poisson(expected_potholes)))
        
        # Generate pothole locations
        for _ in range(num_potholes):
            position_ratio = random.uniform(0.1, 0.9)  # Avoid road ends
            pothole = self._create_pothole(
                edge_data, position_ratio, surface_type, maintenance_level
            )
            potholes.append(pothole)
        
        # Cache results
        self._pothole_cache[edge_id] = potholes
        return potholes
    
    def identify_construction_zones(self, graph: nx.Graph) -> List[ConstructionZone]:
        """
        Identify construction zones in the road network from OSM construction tags.
        
        Args:
            graph: NetworkX graph representing the road network
            
        Returns:
            List of ConstructionZone objects representing active construction
        """
        construction_edges = {}
        
        # Group edges by construction status
        for u, v, edge_data in graph.edges(data=True):
            construction_status = self._check_construction_status(edge_data)
            
            if construction_status != ConstructionStatus.NO_CONSTRUCTION:
                if construction_status not in construction_edges:
                    construction_edges[construction_status] = []
                construction_edges[construction_status].append(((u, v), edge_data))
        
        # Create construction zones from grouped edges
        construction_zones = []
        for status, edges in construction_edges.items():
            # Group adjacent edges into zones
            zones = self._group_adjacent_construction_edges(edges, graph)
            
            for zone_edges in zones:
                edge_ids = [edge_id for edge_id, _ in zone_edges]
                edge_data = zone_edges[0][1]  # Use first edge's data as representative
                
                construction_zone = self._create_construction_zone(
                    edge_ids, edge_data, status
                )
                construction_zones.append(construction_zone)
        
        self._construction_zones = construction_zones
        return construction_zones
    
    def update_dynamic_conditions(self, conditions: Dict[str, Any]) -> None:
        """
        Update dynamic road conditions based on external factors.
        
        Args:
            conditions: Dictionary containing condition updates
        """
        # Clear caches when conditions change
        if 'weather' in conditions or 'time' in conditions:
            self._road_quality_cache.clear()
            self._pothole_cache.clear()
        
        # Update construction zones if needed
        if 'construction_updates' in conditions:
            for update in conditions['construction_updates']:
                self._update_construction_zone(update)
    
    def _calculate_quality_score(self, edge_data: Dict[str, Any]) -> float:
        """Calculate overall quality score for a road segment"""
        surface_type = self._get_surface_type(edge_data)
        maintenance_level = self._get_maintenance_level(edge_data)
        
        # Base score from surface type
        surface_score = self.config.surface_type_weights.get(surface_type, 0.5)
        
        # Maintenance factor
        maintenance_score = self.config.maintenance_weights.get(maintenance_level, 0.5)
        
        # Highway type factor
        highway_type = edge_data.get('highway', '').lower()
        highway_factor = self._get_highway_quality_factor(highway_type)
        
        # Age factor
        age_factor = self._get_age_quality_factor(edge_data)
        
        # Combine factors (weighted average)
        quality_score = (
            surface_score * 0.3 +
            maintenance_score * 0.3 +
            highway_factor * 0.2 +
            age_factor * 0.2
        )
        
        return min(1.0, max(0.0, quality_score))
    
    def _get_surface_type(self, edge_data: Dict[str, Any]) -> SurfaceType:
        """Determine surface type from OSM data"""
        surface = edge_data.get('surface', '').lower()
        
        if surface in ['asphalt', 'paved']:
            return SurfaceType.ASPHALT
        elif surface in ['concrete']:
            return SurfaceType.CONCRETE
        elif surface in ['gravel', 'fine_gravel']:
            return SurfaceType.GRAVEL
        elif surface in ['dirt', 'earth', 'mud', 'sand']:
            return SurfaceType.DIRT
        elif surface in ['cobblestone', 'sett']:
            return SurfaceType.COBBLESTONE
        else:
            # Default based on highway type
            highway = edge_data.get('highway', '').lower()
            if highway in ['motorway', 'trunk', 'primary']:
                return SurfaceType.ASPHALT
            elif highway in ['secondary', 'tertiary']:
                return SurfaceType.ASPHALT
            else:
                return SurfaceType.GRAVEL  # Conservative default for Indian roads
    
    def _get_maintenance_level(self, edge_data: Dict[str, Any]) -> MaintenanceLevel:
        """Estimate maintenance level from OSM data and road characteristics"""
        # Check for explicit maintenance tags
        condition = edge_data.get('condition', '').lower()
        if condition in ['excellent', 'good']:
            return MaintenanceLevel.WELL_MAINTAINED
        elif condition in ['poor', 'bad']:
            return MaintenanceLevel.POORLY_MAINTAINED
        elif condition in ['very_bad', 'terrible']:
            return MaintenanceLevel.UNMAINTAINED
        
        # Infer from highway type
        highway = edge_data.get('highway', '').lower()
        if highway in ['motorway', 'trunk']:
            return MaintenanceLevel.WELL_MAINTAINED
        elif highway in ['primary', 'secondary']:
            return MaintenanceLevel.MODERATELY_MAINTAINED
        elif highway in ['tertiary', 'residential']:
            return MaintenanceLevel.MODERATELY_MAINTAINED
        else:
            return MaintenanceLevel.POORLY_MAINTAINED
    
    def _estimate_road_age(self, edge_data: Dict[str, Any]) -> int:
        """Estimate road age in years from available data"""
        # Try to get construction date or last modification
        start_date = edge_data.get('start_date')
        if start_date:
            try:
                year = int(start_date.split('-')[0])
                return max(0, datetime.now().year - year)
            except (ValueError, AttributeError):
                pass
        
        # Estimate based on highway type (Indian road development patterns)
        highway = edge_data.get('highway', '').lower()
        if highway in ['motorway', 'trunk']:
            return random.randint(5, 15)  # Newer highways
        elif highway in ['primary', 'secondary']:
            return random.randint(10, 25)  # Established roads
        else:
            return random.randint(15, 40)  # Older local roads
    
    def _get_highway_quality_factor(self, highway_type: str) -> float:
        """Get quality factor based on highway type"""
        highway_factors = {
            'motorway': 1.0,
            'trunk': 0.9,
            'primary': 0.8,
            'secondary': 0.7,
            'tertiary': 0.6,
            'residential': 0.5,
            'service': 0.4,
            'track': 0.2,
            'path': 0.1
        }
        return highway_factors.get(highway_type, 0.5)
    
    def _get_age_quality_factor(self, edge_data: Dict[str, Any]) -> float:
        """Get quality factor based on estimated road age"""
        age = self._estimate_road_age(edge_data)
        
        if age <= 5:
            return 1.0
        elif age <= 10:
            return 0.8
        elif age <= 20:
            return 0.6
        else:
            return 0.3
    
    def _calculate_pothole_probability(self, surface_type: SurfaceType, 
                                    maintenance_level: MaintenanceLevel, 
                                    road_age: int) -> float:
        """Calculate probability of potholes per 100m of road"""
        # Base probability from age
        age_factor = min(road_age / 20.0, 1.0)  # Normalize to 0-1 over 20 years
        
        # Surface type multiplier
        surface_multipliers = {
            SurfaceType.ASPHALT: 1.0,
            SurfaceType.CONCRETE: 0.5,
            SurfaceType.GRAVEL: 2.0,
            SurfaceType.DIRT: 4.0,
            SurfaceType.COBBLESTONE: 1.5
        }
        surface_factor = surface_multipliers.get(surface_type, 2.0)
        
        # Maintenance multiplier
        maintenance_multipliers = {
            MaintenanceLevel.WELL_MAINTAINED: 0.5,
            MaintenanceLevel.MODERATELY_MAINTAINED: 1.0,
            MaintenanceLevel.POORLY_MAINTAINED: 2.5,
            MaintenanceLevel.UNMAINTAINED: 4.0
        }
        maintenance_factor = maintenance_multipliers.get(maintenance_level, 2.0)
        
        # Combine factors
        probability = age_factor * surface_factor * maintenance_factor * 0.1
        return min(probability, 1.0)  # Cap at 100%
    
    def _create_pothole(self, edge_data: Dict[str, Any], position_ratio: float, 
                       surface_type: SurfaceType, maintenance_level: MaintenanceLevel) -> PotholeLocation:
        """Create a pothole at a specific position on the road segment"""
        # Determine severity based on surface and maintenance
        if maintenance_level == MaintenanceLevel.UNMAINTAINED:
            severity = random.choice([SeverityLevel.MEDIUM, SeverityLevel.HIGH, SeverityLevel.CRITICAL])
        elif maintenance_level == MaintenanceLevel.POORLY_MAINTAINED:
            severity = random.choice([SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.HIGH])
        else:
            severity = random.choice([SeverityLevel.LOW, SeverityLevel.MEDIUM])
        
        # Determine size based on severity and surface type
        base_diameter = {
            SeverityLevel.LOW: random.uniform(0.3, 0.8),
            SeverityLevel.MEDIUM: random.uniform(0.8, 1.5),
            SeverityLevel.HIGH: random.uniform(1.5, 2.5),
            SeverityLevel.CRITICAL: random.uniform(2.5, 4.0)
        }[severity]
        
        base_depth = {
            SeverityLevel.LOW: random.uniform(0.05, 0.15),
            SeverityLevel.MEDIUM: random.uniform(0.15, 0.30),
            SeverityLevel.HIGH: random.uniform(0.30, 0.50),
            SeverityLevel.CRITICAL: random.uniform(0.50, 1.0)
        }[severity]
        
        # Adjust for surface type
        if surface_type == SurfaceType.DIRT:
            base_diameter *= 1.5
            base_depth *= 2.0
        elif surface_type == SurfaceType.GRAVEL:
            base_diameter *= 1.2
            base_depth *= 1.5
        
        # Calculate position (simplified - would need actual geometry in real implementation)
        edge_id = edge_data.get('edge_id', (0, 0))
        position = Point3D(
            x=position_ratio * 100,  # Simplified positioning
            y=0,
            z=-base_depth
        )
        
        return PotholeLocation(
            position=position,
            severity=severity,
            diameter=base_diameter,
            depth=base_depth,
            edge_id=edge_id
        )
    
    def _check_construction_status(self, edge_data: Dict[str, Any]) -> ConstructionStatus:
        """Check construction status from OSM tags"""
        # Check for construction tags
        construction = edge_data.get('construction', '').lower()
        highway = edge_data.get('highway', '').lower()
        
        if 'construction' in highway or construction:
            if 'major' in construction or 'reconstruction' in construction:
                return ConstructionStatus.MAJOR_CONSTRUCTION
            elif 'minor' in construction or 'maintenance' in construction:
                return ConstructionStatus.MINOR_WORK
            else:
                return ConstructionStatus.MINOR_WORK
        
        # Check for temporary tags
        if edge_data.get('temporary', '').lower() == 'yes':
            return ConstructionStatus.MINOR_WORK
        
        # Check for access restrictions that might indicate construction
        access = edge_data.get('access', '').lower()
        if access in ['no', 'private', 'construction']:
            return ConstructionStatus.ROAD_CLOSURE
        
        return ConstructionStatus.NO_CONSTRUCTION
    
    def _create_construction_zone(self, edge_ids: List[Tuple[int, int]], 
                                edge_data: Dict[str, Any],
                                construction_status: ConstructionStatus) -> ConstructionZone:
        """Create a construction zone from edge data"""
        # Estimate construction duration based on type
        if construction_status == ConstructionStatus.MAJOR_CONSTRUCTION:
            duration_days = random.randint(180, 730)  # 6 months to 2 years
            lanes_affected = random.randint(1, 3)
            speed_reduction = 0.3  # 70% of normal speed
        elif construction_status == ConstructionStatus.MINOR_WORK:
            duration_days = random.randint(7, 90)  # 1 week to 3 months
            lanes_affected = random.randint(1, 2)
            speed_reduction = 0.5  # 50% of normal speed
        else:  # ROAD_CLOSURE
            duration_days = random.randint(1, 30)  # 1 day to 1 month
            lanes_affected = 99  # All lanes
            speed_reduction = 0.0  # Complete closure
        
        start_date = datetime.now() - timedelta(days=random.randint(0, 30))
        end_date = start_date + timedelta(days=duration_days)
        
        description = f"{construction_status.name.replace('_', ' ').title()} on {edge_data.get('name', 'unnamed road')}"
        
        return ConstructionZone(
            edge_ids=edge_ids,
            construction_type=construction_status,
            start_date=start_date,
            estimated_end_date=end_date,
            lanes_affected=lanes_affected,
            speed_limit_reduction=speed_reduction,
            description=description
        )
    
    def _group_adjacent_construction_edges(self, edges: List[Tuple[Tuple[int, int], Dict[str, Any]]], 
                                         graph: nx.Graph) -> List[List[Tuple[Tuple[int, int], Dict[str, Any]]]]:
        """Group adjacent construction edges into zones"""
        if not edges:
            return []
        
        zones = []
        processed = set()
        
        for i, (edge_id, edge_data) in enumerate(edges):
            if edge_id in processed:
                continue
            
            # Start a new zone
            zone = [(edge_id, edge_data)]
            processed.add(edge_id)
            
            # Find adjacent edges
            queue = [edge_id]
            while queue:
                current_edge = queue.pop(0)
                u, v = current_edge
                
                # Check neighbors
                for neighbor in [u, v]:
                    for next_edge_id, next_edge_data in edges:
                        if next_edge_id in processed:
                            continue
                        
                        next_u, next_v = next_edge_id
                        if neighbor in [next_u, next_v]:
                            zone.append((next_edge_id, next_edge_data))
                            processed.add(next_edge_id)
                            queue.append(next_edge_id)
            
            zones.append(zone)
        
        return zones
    
    def _update_construction_zone(self, update: Dict[str, Any]) -> None:
        """Update an existing construction zone"""
        zone_id = update.get('zone_id')
        if zone_id is not None and zone_id < len(self._construction_zones):
            zone = self._construction_zones[zone_id]
            
            if 'end_date' in update:
                zone.estimated_end_date = update['end_date']
            if 'lanes_affected' in update:
                zone.lanes_affected = update['lanes_affected']
            if 'speed_reduction' in update:
                zone.speed_limit_reduction = update['speed_reduction']


@dataclass
class RoadConditionState:
    """Represents the current state of road conditions"""
    base_quality: RoadQuality
    weather_impact: float  # 0.0 to 1.0 (1.0 = no impact)
    time_impact: float     # 0.0 to 1.0 (1.0 = no impact)
    temporary_obstacles: List[Dict[str, Any]]
    construction_zones: List[ConstructionZone]
    last_updated: datetime


@dataclass
class TemporaryObstacle:
    """Represents a temporary obstacle on the road"""
    position: Point3D
    obstacle_type: str  # 'accident', 'breakdown', 'debris', 'flooding'
    severity: SeverityLevel
    lanes_blocked: int
    estimated_duration: timedelta
    created_at: datetime
    edge_id: Tuple[int, int]


class RoadConditionMapper:
    """
    Manages dynamic road conditions including weather effects, temporary obstacles,
    and construction zone updates for the Indian traffic simulation.
    """
    
    def __init__(self, road_analyzer: IndianRoadAnalyzer, config: Optional[RoadConditionConfig] = None):
        """Initialize the road condition mapper"""
        self.road_analyzer = road_analyzer
        self.config = config or RoadConditionConfig()
        
        # State storage
        self._road_states: Dict[Tuple[int, int], RoadConditionState] = {}
        self._temporary_obstacles: Dict[str, TemporaryObstacle] = {}
        self._active_construction_zones: List[ConstructionZone] = []
        
        # Weather and time tracking
        self._current_weather = None
        self._current_time = datetime.now()
        
        # Update intervals
        self._last_weather_update = datetime.now()
        self._last_time_update = datetime.now()
    
    def initialize_road_states(self, graph: nx.Graph) -> None:
        """Initialize road condition states for all edges in the graph"""
        # Get base road qualities from analyzer
        base_qualities = self.road_analyzer.analyze_road_quality(graph)
        
        # Initialize states for all edges
        current_time = datetime.now()
        for edge_id, quality in base_qualities.items():
            self._road_states[edge_id] = RoadConditionState(
                base_quality=quality,
                weather_impact=1.0,
                time_impact=1.0,
                temporary_obstacles=[],
                construction_zones=[],
                last_updated=current_time
            )
        
        # Initialize construction zones
        construction_zones = self.road_analyzer.identify_construction_zones(graph)
        self._active_construction_zones = construction_zones
        
        # Apply construction zones to affected edges
        for zone in construction_zones:
            for edge_id in zone.edge_ids:
                if edge_id in self._road_states:
                    self._road_states[edge_id].construction_zones.append(zone)
    
    def update_weather_conditions(self, weather_type: str, intensity: float = 1.0) -> None:
        """
        Update weather conditions affecting all roads.
        
        Args:
            weather_type: Type of weather ('clear', 'rain', 'fog', 'dust_storm')
            intensity: Weather intensity from 0.0 to 1.0
        """
        from .enums import WeatherType
        
        # Map string to enum
        weather_map = {
            'clear': WeatherType.CLEAR,
            'light_rain': WeatherType.LIGHT_RAIN,
            'heavy_rain': WeatherType.HEAVY_RAIN,
            'fog': WeatherType.FOG,
            'dust_storm': WeatherType.DUST_STORM
        }
        
        weather_enum = weather_map.get(weather_type.lower(), WeatherType.CLEAR)
        self._current_weather = weather_enum
        
        # Calculate weather impact factor
        weather_impacts = {
            WeatherType.CLEAR: 1.0,
            WeatherType.LIGHT_RAIN: 0.9,
            WeatherType.HEAVY_RAIN: 0.6,
            WeatherType.FOG: 0.7,
            WeatherType.DUST_STORM: 0.5
        }
        
        base_impact = weather_impacts.get(weather_enum, 1.0)
        weather_impact = base_impact * (1.0 - intensity * 0.3)  # Intensity reduces impact further
        
        # Update all road states
        current_time = datetime.now()
        for edge_id, state in self._road_states.items():
            state.weather_impact = weather_impact
            state.last_updated = current_time
        
        self._last_weather_update = current_time
    
    def update_time_effects(self, current_hour: int) -> None:
        """
        Update time-of-day effects on road conditions.
        
        Args:
            current_hour: Current hour (0-23)
        """
        # Calculate time impact based on traffic patterns
        # Peak hours have more wear and congestion effects
        peak_hours = [7, 8, 9, 17, 18, 19, 20]  # Morning and evening peaks
        
        if current_hour in peak_hours:
            time_impact = 0.8  # Reduced conditions during peak hours
        elif current_hour in [22, 23, 0, 1, 2, 3, 4, 5]:  # Night hours
            time_impact = 1.1  # Slightly better conditions at night (less traffic)
        else:
            time_impact = 1.0  # Normal conditions
        
        # Update all road states
        current_time = datetime.now()
        for edge_id, state in self._road_states.items():
            state.time_impact = min(1.0, time_impact)  # Cap at 1.0
            state.last_updated = current_time
        
        self._current_time = current_time
        self._last_time_update = current_time
    
    def add_temporary_obstacle(self, edge_id: Tuple[int, int], obstacle_type: str, 
                             position_ratio: float = 0.5, severity: str = 'medium',
                             duration_minutes: int = 30) -> str:
        """
        Add a temporary obstacle to a road segment.
        
        Args:
            edge_id: Edge identifier (u, v)
            obstacle_type: Type of obstacle ('accident', 'breakdown', 'debris', 'flooding')
            position_ratio: Position along the edge (0.0 to 1.0)
            severity: Severity level ('low', 'medium', 'high', 'critical')
            duration_minutes: Expected duration in minutes
            
        Returns:
            Obstacle ID for tracking and removal
        """
        # Generate unique obstacle ID
        obstacle_id = f"{edge_id[0]}_{edge_id[1]}_{len(self._temporary_obstacles)}_{int(datetime.now().timestamp())}"
        
        # Map severity string to enum
        severity_map = {
            'low': SeverityLevel.LOW,
            'medium': SeverityLevel.MEDIUM,
            'high': SeverityLevel.HIGH,
            'critical': SeverityLevel.CRITICAL
        }
        severity_enum = severity_map.get(severity.lower(), SeverityLevel.MEDIUM)
        
        # Determine lanes blocked based on obstacle type and severity
        lanes_blocked = self._calculate_lanes_blocked(obstacle_type, severity_enum)
        
        # Create obstacle
        obstacle = TemporaryObstacle(
            position=Point3D(x=position_ratio * 100, y=0, z=0),  # Simplified positioning
            obstacle_type=obstacle_type,
            severity=severity_enum,
            lanes_blocked=lanes_blocked,
            estimated_duration=timedelta(minutes=duration_minutes),
            created_at=datetime.now(),
            edge_id=edge_id
        )
        
        # Store obstacle
        self._temporary_obstacles[obstacle_id] = obstacle
        
        # Update road state
        if edge_id in self._road_states:
            obstacle_dict = {
                'id': obstacle_id,
                'type': obstacle_type,
                'severity': severity,
                'lanes_blocked': lanes_blocked,
                'position_ratio': position_ratio
            }
            self._road_states[edge_id].temporary_obstacles.append(obstacle_dict)
            self._road_states[edge_id].last_updated = datetime.now()
        
        return obstacle_id
    
    def remove_temporary_obstacle(self, obstacle_id: str) -> bool:
        """
        Remove a temporary obstacle.
        
        Args:
            obstacle_id: ID of the obstacle to remove
            
        Returns:
            True if obstacle was found and removed, False otherwise
        """
        if obstacle_id not in self._temporary_obstacles:
            return False
        
        obstacle = self._temporary_obstacles[obstacle_id]
        edge_id = obstacle.edge_id
        
        # Remove from storage
        del self._temporary_obstacles[obstacle_id]
        
        # Update road state
        if edge_id in self._road_states:
            state = self._road_states[edge_id]
            state.temporary_obstacles = [
                obs for obs in state.temporary_obstacles 
                if obs.get('id') != obstacle_id
            ]
            state.last_updated = datetime.now()
        
        return True
    
    def update_construction_zone(self, zone_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update an existing construction zone.
        
        Args:
            zone_id: Index of the construction zone to update
            updates: Dictionary containing updates (end_date, lanes_affected, speed_reduction)
            
        Returns:
            True if zone was found and updated, False otherwise
        """
        if zone_id < 0 or zone_id >= len(self._active_construction_zones):
            return False
        
        zone = self._active_construction_zones[zone_id]
        
        # Apply updates
        if 'end_date' in updates:
            zone.estimated_end_date = updates['end_date']
        if 'lanes_affected' in updates:
            zone.lanes_affected = updates['lanes_affected']
        if 'speed_reduction' in updates:
            zone.speed_limit_reduction = updates['speed_reduction']
        if 'description' in updates:
            zone.description = updates['description']
        
        # Update affected road states
        current_time = datetime.now()
        for edge_id in zone.edge_ids:
            if edge_id in self._road_states:
                self._road_states[edge_id].last_updated = current_time
        
        return True
    
    def add_construction_zone(self, edge_ids: List[Tuple[int, int]], 
                            construction_type: str, duration_days: int,
                            lanes_affected: int = 1, speed_reduction: float = 0.5,
                            description: str = "") -> int:
        """
        Add a new construction zone.
        
        Args:
            edge_ids: List of edge IDs affected by construction
            construction_type: Type of construction ('minor', 'major', 'closure')
            duration_days: Expected duration in days
            lanes_affected: Number of lanes affected
            speed_reduction: Speed reduction factor (0.0 to 1.0)
            description: Description of the construction work
            
        Returns:
            Zone ID for tracking and updates
        """
        from .enums import ConstructionStatus
        
        # Map construction type to enum
        type_map = {
            'minor': ConstructionStatus.MINOR_WORK,
            'major': ConstructionStatus.MAJOR_CONSTRUCTION,
            'closure': ConstructionStatus.ROAD_CLOSURE
        }
        construction_enum = type_map.get(construction_type.lower(), ConstructionStatus.MINOR_WORK)
        
        # Create construction zone
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)
        
        zone = ConstructionZone(
            edge_ids=edge_ids,
            construction_type=construction_enum,
            start_date=start_date,
            estimated_end_date=end_date,
            lanes_affected=lanes_affected,
            speed_limit_reduction=speed_reduction,
            description=description or f"{construction_type.title()} construction work"
        )
        
        # Add to active zones
        self._active_construction_zones.append(zone)
        zone_id = len(self._active_construction_zones) - 1
        
        # Update affected road states
        current_time = datetime.now()
        for edge_id in edge_ids:
            if edge_id in self._road_states:
                self._road_states[edge_id].construction_zones.append(zone)
                self._road_states[edge_id].last_updated = current_time
        
        return zone_id
    
    def remove_construction_zone(self, zone_id: int) -> bool:
        """
        Remove a construction zone.
        
        Args:
            zone_id: ID of the construction zone to remove
            
        Returns:
            True if zone was found and removed, False otherwise
        """
        if zone_id < 0 or zone_id >= len(self._active_construction_zones):
            return False
        
        zone = self._active_construction_zones[zone_id]
        
        # Update affected road states
        current_time = datetime.now()
        for edge_id in zone.edge_ids:
            if edge_id in self._road_states:
                state = self._road_states[edge_id]
                state.construction_zones = [
                    z for z in state.construction_zones if z != zone
                ]
                state.last_updated = current_time
        
        # Remove from active zones (mark as None to preserve indices)
        self._active_construction_zones[zone_id] = None
        
        return True
    
    def get_road_condition_state(self, edge_id: Tuple[int, int]) -> Optional[RoadConditionState]:
        """
        Get the current condition state for a road segment.
        
        Args:
            edge_id: Edge identifier (u, v)
            
        Returns:
            RoadConditionState object or None if edge not found
        """
        return self._road_states.get(edge_id)
    
    def get_effective_road_quality(self, edge_id: Tuple[int, int]) -> Optional[RoadQuality]:
        """
        Get the effective road quality considering all dynamic factors.
        
        Args:
            edge_id: Edge identifier (u, v)
            
        Returns:
            Effective RoadQuality or None if edge not found
        """
        state = self._road_states.get(edge_id)
        if not state:
            return None
        
        # Start with base quality score
        base_scores = {
            RoadQuality.EXCELLENT: 1.0,
            RoadQuality.GOOD: 0.75,
            RoadQuality.POOR: 0.5,
            RoadQuality.VERY_POOR: 0.25
        }
        
        effective_score = base_scores.get(state.base_quality, 0.5)
        
        # Apply weather impact
        effective_score *= state.weather_impact
        
        # Apply time impact
        effective_score *= state.time_impact
        
        # Apply temporary obstacle impact
        if state.temporary_obstacles:
            obstacle_impact = 1.0
            for obstacle in state.temporary_obstacles:
                severity = obstacle.get('severity', 'medium')
                if severity == 'critical':
                    obstacle_impact *= 0.3
                elif severity == 'high':
                    obstacle_impact *= 0.5
                elif severity == 'medium':
                    obstacle_impact *= 0.7
                else:  # low
                    obstacle_impact *= 0.9
            effective_score *= obstacle_impact
        
        # Apply construction zone impact
        if state.construction_zones:
            construction_impact = 1.0
            for zone in state.construction_zones:
                if zone.construction_type == ConstructionStatus.ROAD_CLOSURE:
                    construction_impact *= 0.1  # Nearly impassable
                elif zone.construction_type == ConstructionStatus.MAJOR_CONSTRUCTION:
                    construction_impact *= 0.4
                else:  # MINOR_WORK
                    construction_impact *= 0.7
            effective_score *= construction_impact
        
        # Convert back to quality enum
        if effective_score >= 0.8:
            return RoadQuality.EXCELLENT
        elif effective_score >= 0.6:
            return RoadQuality.GOOD
        elif effective_score >= 0.4:
            return RoadQuality.POOR
        else:
            return RoadQuality.VERY_POOR
    
    def get_speed_adjustment_factor(self, edge_id: Tuple[int, int]) -> float:
        """
        Get speed adjustment factor for a road segment based on current conditions.
        
        Args:
            edge_id: Edge identifier (u, v)
            
        Returns:
            Speed adjustment factor (0.0 to 1.0, where 1.0 = no adjustment)
        """
        state = self._road_states.get(edge_id)
        if not state:
            return 1.0
        
        # Base speed factor from road quality
        quality_factors = {
            RoadQuality.EXCELLENT: 1.0,
            RoadQuality.GOOD: 0.95,
            RoadQuality.POOR: 0.8,
            RoadQuality.VERY_POOR: 0.6
        }
        
        speed_factor = quality_factors.get(state.base_quality, 0.8)
        
        # Apply weather impact
        speed_factor *= state.weather_impact
        
        # Apply temporary obstacle impact
        if state.temporary_obstacles:
            for obstacle in state.temporary_obstacles:
                lanes_blocked = obstacle.get('lanes_blocked', 1)
                if lanes_blocked >= 2:
                    speed_factor *= 0.3  # Severe slowdown
                else:
                    speed_factor *= 0.6  # Moderate slowdown
        
        # Apply construction zone impact
        if state.construction_zones:
            for zone in state.construction_zones:
                speed_factor *= zone.speed_limit_reduction
        
        return max(0.1, min(1.0, speed_factor))  # Clamp between 0.1 and 1.0
    
    def cleanup_expired_obstacles(self) -> List[str]:
        """
        Remove expired temporary obstacles.
        
        Returns:
            List of removed obstacle IDs
        """
        current_time = datetime.now()
        expired_ids = []
        
        for obstacle_id, obstacle in list(self._temporary_obstacles.items()):
            if current_time > obstacle.created_at + obstacle.estimated_duration:
                expired_ids.append(obstacle_id)
                self.remove_temporary_obstacle(obstacle_id)
        
        return expired_ids
    
    def cleanup_completed_construction(self) -> List[int]:
        """
        Remove completed construction zones.
        
        Returns:
            List of removed zone IDs
        """
        current_time = datetime.now()
        completed_ids = []
        
        for i, zone in enumerate(self._active_construction_zones):
            if zone and current_time > zone.estimated_end_date:
                completed_ids.append(i)
                self.remove_construction_zone(i)
        
        return completed_ids
    
    def get_all_active_obstacles(self) -> Dict[str, TemporaryObstacle]:
        """Get all currently active temporary obstacles."""
        return self._temporary_obstacles.copy()
    
    def get_all_active_construction_zones(self) -> List[ConstructionZone]:
        """Get all currently active construction zones."""
        return [zone for zone in self._active_construction_zones if zone is not None]
    
    def _calculate_lanes_blocked(self, obstacle_type: str, severity: SeverityLevel) -> int:
        """Calculate number of lanes blocked based on obstacle type and severity."""
        base_lanes = {
            'accident': 2,
            'breakdown': 1,
            'debris': 1,
            'flooding': 3
        }
        
        lanes = base_lanes.get(obstacle_type, 1)
        
        # Adjust based on severity
        if severity == SeverityLevel.CRITICAL:
            lanes = min(4, lanes + 2)
        elif severity == SeverityLevel.HIGH:
            lanes = min(3, lanes + 1)
        elif severity == SeverityLevel.LOW:
            lanes = max(1, lanes - 1)
        
        return lanes