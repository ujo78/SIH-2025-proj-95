"""
TrafficFlowVisualizer Implementation

This module implements the TrafficVisualizerInterface for visualizing traffic flow
and congestion in 3D scenes, including color-coding for traffic density,
congestion hotspots, and emergency scenario alerts.
"""

import math
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

try:
    from panda3d.core import (
        NodePath, CardMaker, GeomNode, Geom, GeomVertexFormat,
        GeomVertexData, GeomVertexWriter, GeomTriangles, GeomLines,
        GeomPoints, RenderState, ColorBlendAttrib, TransparencyAttrib,
        Material, Vec3, Vec4, Point3, Texture, TextureStage,
        BillboardEffect, DepthTestAttrib, DepthWriteAttrib,
        DirectionalLight, PointLight
    )
    from direct.interval.IntervalGlobal import (
        Func, Wait, LerpColorInterval, LerpScaleInterval, LerpPosInterval, 
        Sequence, Parallel
    )
    PANDA3D_AVAILABLE = True
except ImportError:
    PANDA3D_AVAILABLE = False
    # Mock classes for development without Panda3D
    class NodePath:
        def __init__(self, *args): pass
        def setPos(self, *args): pass
        def setHpr(self, *args): pass
        def setScale(self, *args): pass
        def setColor(self, *args): pass
        def setTexture(self, *args): pass
        def reparentTo(self, *args): pass
        def removeNode(self): pass
        def show(self): pass
        def hide(self): pass
    
    Vec3 = Vec4 = Point3 = lambda *args: None
    Sequence = Parallel = LerpColorInterval = LerpScaleInterval = lambda *args: None

import networkx as nx

try:
    # Try relative imports first (when used as package)
    from .interfaces import TrafficVisualizerInterface
    from .config import VisualizationConfig, UIConfig
except ImportError:
    # Fall back to absolute imports (when run directly)
    from enhanced_visualization.interfaces import TrafficVisualizerInterface
    from enhanced_visualization.config import VisualizationConfig, UIConfig
from indian_features.enums import EmergencyType
from indian_features.interfaces import Point3D


@dataclass
class TrafficDensityLevel:
    """Represents traffic density level with visual properties"""
    level: str  # "free_flow", "light", "moderate", "heavy", "congested"
    density: float  # 0.0 to 1.0
    color: Tuple[float, float, float, float]
    animation_speed: float = 1.0
    pulse_intensity: float = 0.0


@dataclass
class CongestionHotspot:
    """Represents a traffic congestion hotspot"""
    hotspot_id: str
    center: Point3D
    radius: float
    intensity: float  # 0.0 to 1.0
    affected_edges: List[Tuple[int, int]]
    visual_node: Optional[NodePath] = None
    animation: Optional[Any] = None


@dataclass
class EmergencyAlert:
    """Represents an emergency scenario alert"""
    alert_id: str
    emergency_type: EmergencyType
    location: Point3D
    affected_area: List[Point3D]  # Polygon points
    severity: float  # 0.0 to 1.0
    visual_elements: List[NodePath] = field(default_factory=list)
    animations: List[Any] = field(default_factory=list)


@dataclass
class RouteVisualization:
    """Represents route visualization data"""
    route_id: str
    route_type: str  # "original", "alternative", "emergency"
    waypoints: List[Point3D]
    color: Tuple[float, float, float, float]
    width: float
    visual_node: Optional[NodePath] = None
    animation: Optional[Any] = None


class TrafficFlowVisualizer(TrafficVisualizerInterface):
    """
    Visualizes traffic flow and congestion in 3D scenes.
    
    This class provides color-coding for traffic density, highlights congestion
    hotspots, displays emergency alerts, and shows route alternatives with
    animated flow patterns.
    """
    
    def __init__(self, config: VisualizationConfig, render_root: Optional[NodePath] = None):
        """
        Initialize the traffic flow visualizer.
        
        Args:
            config: Visualization configuration
            render_root: Root node for rendering (optional, for testing)
        """
        self.config = config
        self.ui_config = config.ui_config
        
        # Initialize Panda3D components if available
        if PANDA3D_AVAILABLE:
            self.render = render_root
            self.panda3d_enabled = render_root is not None
        else:
            self.render = None
            self.panda3d_enabled = False
        
        # Road network data
        self.road_network: Optional[nx.Graph] = None
        self.edge_geometries: Dict[Tuple[int, int], List[Point3D]] = {}
        
        # Scene nodes
        self.traffic_overlay_node = None
        self.hotspots_node = None
        self.alerts_node = None
        self.routes_node = None
        self.flow_animation_node = None
        
        # Traffic visualization data
        self.edge_densities: Dict[Tuple[int, int], float] = {}
        self.density_visuals: Dict[Tuple[int, int], NodePath] = {}
        self.congestion_hotspots: Dict[str, CongestionHotspot] = {}
        self.emergency_alerts: Dict[str, EmergencyAlert] = {}
        self.route_visualizations: Dict[str, RouteVisualization] = {}
        
        # Traffic density levels
        self.density_levels = self._create_density_levels()
        
        # Animation management
        self.active_animations: Dict[str, Any] = {}
        self.flow_particles: Dict[Tuple[int, int], List[NodePath]] = {}
        
        # Performance settings
        self.max_flow_particles = 1000
        self.update_frequency = 10.0  # Hz
        self.animation_speed_multiplier = 1.0
        
        # Initialize the system
        self._initialize_scene_nodes()
        self._create_materials_and_textures()
    
    def initialize_traffic_overlay(self, road_network: nx.Graph) -> None:
        """
        Initialize traffic flow visualization overlay.
        
        Args:
            road_network: NetworkX graph representing the road network
        """
        self.road_network = road_network
        
        # Always extract edge geometries, regardless of Panda3D availability
        self._extract_edge_geometries()
        
        if not self.panda3d_enabled:
            print(f"Initializing traffic overlay for {len(road_network.edges)} edges (mock)")
            return
        
        # Create initial density visualizations
        self._create_initial_density_visuals()
        
        print(f"Initialized traffic overlay for {len(road_network.edges)} road segments")
    
    def update_traffic_density(self, edge_densities: Dict[Tuple[int, int], float]) -> None:
        """
        Update traffic density visualization on road segments.
        
        Args:
            edge_densities: Dictionary mapping edges to density values (0.0 to 1.0)
        """
        # Always update the density data
        self.edge_densities.update(edge_densities)
        
        if not self.panda3d_enabled:
            print(f"Updating traffic density for {len(edge_densities)} edges (mock)")
            return
        
        for edge, density in edge_densities.items():
            self._update_edge_density_visual(edge, density)
        
        # Update flow animations
        self._update_flow_animations()
        
        print(f"Updated traffic density for {len(edge_densities)} edges")
    
    def show_congestion_hotspots(self, hotspots: List[Dict[str, Any]]) -> None:
        """
        Highlight congestion hotspots in the visualization.
        
        Args:
            hotspots: List of hotspot data dictionaries
        """
        # Clear existing hotspots
        self._clear_congestion_hotspots()
        
        # Always create hotspot data structures
        for hotspot_data in hotspots:
            self._create_congestion_hotspot(hotspot_data)
        
        if not self.panda3d_enabled:
            print(f"Showing {len(hotspots)} congestion hotspots (mock)")
            return
        
        print(f"Displaying {len(hotspots)} congestion hotspots")
    
    def display_emergency_alerts(self, emergencies: List[Dict[str, Any]]) -> None:
        """
        Display emergency scenario alerts and affected areas.
        
        Args:
            emergencies: List of emergency scenario data
        """
        # Clear existing alerts
        self._clear_emergency_alerts()
        
        # Always create alert data structures
        for emergency_data in emergencies:
            self._create_emergency_alert(emergency_data)
        
        if not self.panda3d_enabled:
            print(f"Displaying {len(emergencies)} emergency alerts (mock)")
            return
        
        print(f"Displaying {len(emergencies)} emergency alerts")
    
    def show_route_alternatives(self, original_route: List[int], alternatives: List[List[int]]) -> None:
        """
        Visualize original and alternative routes.
        
        Args:
            original_route: List of node IDs for the original route
            alternatives: List of alternative routes (each a list of node IDs)
        """
        # Clear existing route visualizations
        self._clear_route_visualizations()
        
        # Always create route data structures
        if original_route:
            self._create_route_visualization("original", original_route, "original")
        
        # Create alternative route visualizations
        for i, alt_route in enumerate(alternatives):
            self._create_route_visualization(f"alternative_{i}", alt_route, "alternative")
        
        if not self.panda3d_enabled or not self.road_network:
            print(f"Showing original route and {len(alternatives)} alternatives (mock)")
            return
        
        print(f"Displaying original route and {len(alternatives)} alternative routes")
    
    def create_traffic_flow_animation(self, flow_data: Dict[str, Any]) -> None:
        """
        Create animated visualization of traffic flow patterns.
        
        Args:
            flow_data: Dictionary containing flow animation parameters
        """
        # Always create flow particles data structures
        self._create_flow_particles(flow_data)
        
        if not self.panda3d_enabled:
            print("Creating traffic flow animation (mock)")
            return
        
        # Start flow animation
        self._start_flow_animation()
        
        print("Created traffic flow animation")
    
    def add_performance_indicators(self, metrics: Dict[str, float]) -> None:
        """
        Add real-time performance indicators to the display.
        
        Args:
            metrics: Dictionary of performance metrics
        """
        if not self.panda3d_enabled:
            print(f"Adding performance indicators: {metrics} (mock)")
            return
        
        # Create or update performance indicator displays
        self._update_performance_indicators(metrics)
        
        print(f"Updated performance indicators: {list(metrics.keys())}")
    
    def update_from_mixed_traffic_manager(self, traffic_data: Dict[str, Any]) -> None:
        """
        Update visualization using data from MixedTrafficManager.
        
        Args:
            traffic_data: Traffic simulation data from MixedTrafficManager
        """
        if not traffic_data:
            return
        
        # Extract congestion zones from traffic manager data
        congestion_zones = traffic_data.get('congestion_zones', [])
        if congestion_zones:
            hotspots_data = []
            for zone in congestion_zones:
                hotspot_data = {
                    'id': f"congestion_{len(hotspots_data)}",
                    'x': zone.center_point.x,
                    'y': zone.center_point.y,
                    'z': zone.center_point.z,
                    'radius': zone.radius,
                    'intensity': zone.severity,
                    'affected_edges': []  # Would be populated from zone data
                }
                hotspots_data.append(hotspot_data)
            
            self.show_congestion_hotspots(hotspots_data)
        
        # Extract vehicle interactions for visualization
        interactions = traffic_data.get('interactions', [])
        if interactions:
            # Convert interactions to density data
            edge_densities = {}
            for interaction in interactions:
                # Simplified: increase density for edges with interactions
                # In full implementation, would use proper spatial mapping
                edge_key = (0, 1)  # Placeholder - would map interaction location to edge
                current_density = edge_densities.get(edge_key, 0.0)
                edge_densities[edge_key] = min(1.0, current_density + 0.1)
            
            if edge_densities:
                self.update_traffic_density(edge_densities)
        
        # Update performance indicators
        statistics = traffic_data.get('statistics', {})
        if statistics:
            performance_metrics = {
                'total_vehicles': statistics.get('total_vehicles', 0),
                'congestion_level': len(congestion_zones) / 10.0,  # Normalized
                'interaction_rate': len(interactions) / max(1, statistics.get('total_vehicles', 1))
            }
            self.add_performance_indicators(performance_metrics)
        
        print(f"Updated visualization from traffic manager: {len(congestion_zones)} zones, {len(interactions)} interactions")
    
    def _initialize_scene_nodes(self) -> None:
        """Initialize scene node hierarchy."""
        if not self.panda3d_enabled or not self.render:
            return
        
        self.traffic_overlay_node = self.render.attachNewNode("traffic_overlay")
        self.hotspots_node = self.render.attachNewNode("congestion_hotspots")
        self.alerts_node = self.render.attachNewNode("emergency_alerts")
        self.routes_node = self.render.attachNewNode("route_visualizations")
        self.flow_animation_node = self.render.attachNewNode("flow_animations")
        
        # Set render states for transparency
        self.traffic_overlay_node.setTransparency(TransparencyAttrib.MAlpha)
        self.hotspots_node.setTransparency(TransparencyAttrib.MAlpha)
        self.alerts_node.setTransparency(TransparencyAttrib.MAlpha)
    
    def _create_materials_and_textures(self) -> None:
        """Create materials and textures for visualization."""
        if not self.panda3d_enabled:
            return
        
        # Create materials for different density levels
        self.density_materials = {}
        for level_name, level in self.density_levels.items():
            material = Material()
            material.setAmbient(Vec4(*level.color))
            material.setDiffuse(Vec4(*level.color))
            material.setEmission(Vec4(*level.color) * 0.3)
            self.density_materials[level_name] = material
    
    def _create_density_levels(self) -> Dict[str, TrafficDensityLevel]:
        """Create traffic density level definitions."""
        colors = self.ui_config.traffic_density_colors
        
        return {
            "free_flow": TrafficDensityLevel(
                level="free_flow",
                density=0.0,
                color=(*colors["free_flow"], 0.6),
                animation_speed=2.0,
                pulse_intensity=0.0
            ),
            "light_traffic": TrafficDensityLevel(
                level="light_traffic",
                density=0.25,
                color=(*colors["light_traffic"], 0.7),
                animation_speed=1.5,
                pulse_intensity=0.1
            ),
            "moderate_traffic": TrafficDensityLevel(
                level="moderate_traffic",
                density=0.5,
                color=(*colors["moderate_traffic"], 0.8),
                animation_speed=1.0,
                pulse_intensity=0.3
            ),
            "heavy_traffic": TrafficDensityLevel(
                level="heavy_traffic",
                density=0.75,
                color=(*colors["heavy_traffic"], 0.9),
                animation_speed=0.5,
                pulse_intensity=0.6
            ),
            "congested": TrafficDensityLevel(
                level="congested",
                density=1.0,
                color=(*colors["congested"], 1.0),
                animation_speed=0.2,
                pulse_intensity=1.0
            )
        }
    
    def _extract_edge_geometries(self) -> None:
        """Extract geometric data from road network edges."""
        if not self.road_network:
            return
        
        for u, v, data in self.road_network.edges(data=True):
            # Extract geometry from edge data
            geometry = []
            
            if 'geometry' in data:
                # Use LineString geometry if available
                geom = data['geometry']
                if hasattr(geom, 'coords'):
                    for coord in geom.coords:
                        geometry.append(Point3D(coord[0], coord[1], 0.0))
            else:
                # Use node positions as fallback
                u_data = self.road_network.nodes[u]
                v_data = self.road_network.nodes[v]
                
                u_pos = Point3D(u_data.get('x', 0), u_data.get('y', 0), 0)
                v_pos = Point3D(v_data.get('x', 0), v_data.get('y', 0), 0)
                
                geometry = [u_pos, v_pos]
            
            self.edge_geometries[(u, v)] = geometry
    
    def _create_initial_density_visuals(self) -> None:
        """Create initial density visualization for all edges."""
        if not self.panda3d_enabled:
            return
        
        for edge in self.road_network.edges():
            self._create_edge_density_visual(edge, 0.0)  # Start with zero density
    
    def _create_edge_density_visual(self, edge: Tuple[int, int], density: float) -> None:
        """Create density visualization for a single edge."""
        if not self.panda3d_enabled or edge not in self.edge_geometries:
            return
        
        geometry = self.edge_geometries[edge]
        if len(geometry) < 2:
            return
        
        # Create road segment visualization
        segment_node = self._create_road_segment_geometry(edge, geometry, density)
        
        if segment_node:
            segment_node.reparentTo(self.traffic_overlay_node)
            self.density_visuals[edge] = segment_node
    
    def _create_road_segment_geometry(self, edge: Tuple[int, int], geometry: List[Point3D], density: float) -> Optional[NodePath]:
        """Create 3D geometry for a road segment with density visualization."""
        if not self.panda3d_enabled:
            return None
        
        # Create road segment with proper geometry
        segment_node = NodePath(f"density_segment_{edge[0]}_{edge[1]}")
        
        # Create line geometry for the road segment
        if len(geometry) >= 2:
            # Create vertex data first
            vertex_data = GeomVertexData("road_segment", GeomVertexFormat.getV3(), Geom.UHStatic)
            vertex_data.setNumRows(len(geometry))
            vertex_writer = GeomVertexWriter(vertex_data, "vertex")
            
            # Add vertices along the road segment
            for point in geometry:
                vertex_writer.addData3f(point.x, point.y, point.z + 0.1)  # Slightly above road
            
            # Create geometry with vertex data
            geom = Geom(vertex_data)
            
            # Create line primitive
            lines = GeomLines(Geom.UHStatic)
            for i in range(len(geometry) - 1):
                lines.addVertex(i)
                lines.addVertex(i + 1)
            lines.closePrimitive()
            
            geom.addPrimitive(lines)
            geom_node = GeomNode(f"road_geom_{edge[0]}_{edge[1]}")
            geom_node.addGeom(geom)
            
            segment_node.attachNewNode(geom_node)
        
        # Set color based on density
        density_level = self._get_density_level(density)
        color = self.density_levels[density_level].color
        segment_node.setColor(*color)
        
        # Set line width based on road importance (simplified)
        segment_node.setRenderModeWireframe()
        segment_node.setTwoSided(True)
        
        return segment_node
    
    def _get_density_level(self, density: float) -> str:
        """Get density level name for a given density value."""
        if density < 0.2:
            return "free_flow"
        elif density < 0.4:
            return "light_traffic"
        elif density < 0.6:
            return "moderate_traffic"
        elif density < 0.8:
            return "heavy_traffic"
        else:
            return "congested"
    
    def _update_edge_density_visual(self, edge: Tuple[int, int], density: float) -> None:
        """Update density visualization for an edge."""
        if edge not in self.density_visuals:
            self._create_edge_density_visual(edge, density)
            return
        
        visual_node = self.density_visuals[edge]
        if not self.panda3d_enabled:
            return
        
        # Update color based on new density
        density_level = self._get_density_level(density)
        color = self.density_levels[density_level].color
        visual_node.setColor(*color)
        
        # Add pulsing animation for high congestion
        pulse_intensity = self.density_levels[density_level].pulse_intensity
        if pulse_intensity > 0:
            self._add_pulse_animation(visual_node, pulse_intensity)
    
    def _add_pulse_animation(self, node: NodePath, intensity: float) -> None:
        """Add pulsing animation to a node."""
        if not self.panda3d_enabled:
            return
        
        # Create pulsing scale animation
        scale_up = LerpScaleInterval(node, 0.5, Vec3(1.2, 1.2, 1.2))
        scale_down = LerpScaleInterval(node, 0.5, Vec3(1.0, 1.0, 1.0))
        pulse_sequence = Sequence(scale_up, scale_down)
        pulse_sequence.loop()
    
    def _create_congestion_hotspot(self, hotspot_data: Dict[str, Any]) -> None:
        """Create visualization for a congestion hotspot."""
        hotspot_id = hotspot_data.get("id", f"hotspot_{len(self.congestion_hotspots)}")
        center = Point3D(
            hotspot_data.get("x", 0),
            hotspot_data.get("y", 0),
            hotspot_data.get("z", 0)
        )
        radius = hotspot_data.get("radius", 50.0)
        intensity = hotspot_data.get("intensity", 1.0)
        
        # Create hotspot visual (only if Panda3D is available)
        hotspot_node = None
        animation = None
        
        if self.panda3d_enabled:
            hotspot_node = self._create_hotspot_visual(center, radius, intensity)
            
            if hotspot_node:
                hotspot_node.reparentTo(self.hotspots_node)
                
                # Create pulsing animation
                animation = self._create_hotspot_animation(hotspot_node, intensity)
        
        # Always create the data structure
        hotspot = CongestionHotspot(
            hotspot_id=hotspot_id,
            center=center,
            radius=radius,
            intensity=intensity,
            affected_edges=hotspot_data.get("affected_edges", []),
            visual_node=hotspot_node,
            animation=animation
        )
        
        self.congestion_hotspots[hotspot_id] = hotspot
    
    def _create_hotspot_visual(self, center: Point3D, radius: float, intensity: float) -> Optional[NodePath]:
        """Create visual representation of a congestion hotspot."""
        if not self.panda3d_enabled:
            return None
        
        # Create a circular indicator
        hotspot_node = NodePath("congestion_hotspot")
        hotspot_node.setPos(center.x, center.y, center.z + 1.0)  # Above ground
        hotspot_node.setScale(radius, radius, 1.0)
        
        # Color based on intensity (red for high congestion)
        red_intensity = min(1.0, intensity)
        hotspot_node.setColor(red_intensity, 1.0 - red_intensity, 0.0, 0.7)
        
        return hotspot_node
    
    def _create_hotspot_animation(self, node: NodePath, intensity: float) -> Optional[Any]:
        """Create animation for congestion hotspot."""
        if not self.panda3d_enabled:
            return None
        
        # Create pulsing animation with speed based on intensity
        duration = max(0.5, 2.0 - intensity)  # Faster pulse for higher intensity
        
        scale_up = LerpScaleInterval(node, duration / 2, Vec3(1.3, 1.3, 1.0))
        scale_down = LerpScaleInterval(node, duration / 2, Vec3(1.0, 1.0, 1.0))
        
        pulse_sequence = Sequence(scale_up, scale_down)
        pulse_sequence.loop()
        
        return pulse_sequence
    
    def _create_emergency_alert(self, emergency_data: Dict[str, Any]) -> None:
        """Create visualization for an emergency alert."""
        alert_id = emergency_data.get("id", f"alert_{len(self.emergency_alerts)}")
        emergency_type = emergency_data.get("type", EmergencyType.ACCIDENT)
        location = Point3D(
            emergency_data.get("x", 0),
            emergency_data.get("y", 0),
            emergency_data.get("z", 0)
        )
        severity = emergency_data.get("severity", 1.0)
        
        # Create alert visuals (only if Panda3D is available)
        visual_elements = []
        animations = []
        
        if self.panda3d_enabled:
            visual_elements = self._create_emergency_visuals(emergency_type, location, severity)
            animations = self._create_emergency_animations(visual_elements, emergency_type, severity)
        
        # Always create the data structure
        alert = EmergencyAlert(
            alert_id=alert_id,
            emergency_type=emergency_type,
            location=location,
            affected_area=emergency_data.get("affected_area", []),
            severity=severity,
            visual_elements=visual_elements,
            animations=animations
        )
        
        self.emergency_alerts[alert_id] = alert
    
    def _create_emergency_visuals(self, emergency_type: EmergencyType, location: Point3D, severity: float) -> List[NodePath]:
        """Create visual elements for emergency alert."""
        if not self.panda3d_enabled:
            return []
        
        visual_elements = []
        
        # Get color for emergency type
        emergency_colors = self.ui_config.emergency_colors
        if hasattr(emergency_type, 'name'):
            color_key = emergency_type.name.lower()
        elif hasattr(emergency_type, 'value') and isinstance(emergency_type.value, str):
            color_key = emergency_type.value.lower()
        else:
            color_key = str(emergency_type).lower()
        
        color = emergency_colors.get(color_key, (1.0, 0.0, 0.0))  # Default to red
        
        # Create main alert indicator
        alert_node = NodePath(f"emergency_{emergency_type}")
        alert_node.setPos(location.x, location.y, location.z + 5.0)  # Above scene
        alert_node.setScale(10.0 * severity, 10.0 * severity, 1.0)
        alert_node.setColor(*color, 0.8)
        alert_node.reparentTo(self.alerts_node)
        
        visual_elements.append(alert_node)
        
        # Create warning perimeter
        perimeter_node = NodePath(f"emergency_perimeter_{emergency_type}")
        perimeter_node.setPos(location.x, location.y, location.z + 0.5)
        perimeter_node.setScale(20.0 * severity, 20.0 * severity, 1.0)
        perimeter_node.setColor(*color, 0.3)
        perimeter_node.reparentTo(self.alerts_node)
        
        visual_elements.append(perimeter_node)
        
        return visual_elements
    
    def _create_emergency_animations(self, visual_elements: List[NodePath], emergency_type: EmergencyType, severity: float) -> List[Any]:
        """Create animations for emergency alert."""
        if not PANDA3D_AVAILABLE or not visual_elements:
            return []
        
        animations = []
        
        # Create flashing animation for main alert
        if len(visual_elements) > 0:
            main_alert = visual_elements[0]
            flash_on = LerpColorInterval(main_alert, 0.3, Vec4(1.0, 1.0, 1.0, 1.0))
            flash_off = LerpColorInterval(main_alert, 0.3, Vec4(0.5, 0.5, 0.5, 0.5))
            flash_sequence = Sequence(flash_on, flash_off)
            flash_sequence.loop()
            animations.append(flash_sequence)
        
        # Create expanding animation for perimeter
        if len(visual_elements) > 1:
            perimeter = visual_elements[1]
            expand = LerpScaleInterval(perimeter, 2.0, Vec3(1.5, 1.5, 1.0))
            contract = LerpScaleInterval(perimeter, 2.0, Vec3(1.0, 1.0, 1.0))
            expand_sequence = Sequence(expand, contract)
            expand_sequence.loop()
            animations.append(expand_sequence)
        
        return animations
    
    def _create_route_visualization(self, route_id: str, route_nodes: List[int], route_type: str) -> None:
        """Create visualization for a route."""
        # Convert node IDs to waypoints (always do this)
        waypoints = []
        if self.road_network:
            for node_id in route_nodes:
                if node_id in self.road_network.nodes:
                    node_data = self.road_network.nodes[node_id]
                    waypoint = Point3D(
                        node_data.get('x', 0),
                        node_data.get('y', 0),
                        node_data.get('z', 0)
                    )
                    waypoints.append(waypoint)
        else:
            # Create mock waypoints for testing
            for i, node_id in enumerate(route_nodes):
                waypoints.append(Point3D(i * 10, 0, 0))
        
        if len(waypoints) < 2:
            return
        
        # Set color and width based on route type
        if route_type == "original":
            color = (0.0, 0.0, 1.0, 0.8)  # Blue
            width = 3.0
        elif route_type == "alternative":
            color = (0.0, 1.0, 0.0, 0.6)  # Green
            width = 2.0
        else:  # emergency
            color = (1.0, 0.0, 0.0, 0.8)  # Red
            width = 4.0
        
        # Create route visual (only if Panda3D is available)
        route_node = None
        animation = None
        
        if self.panda3d_enabled:
            route_node = self._create_route_geometry(waypoints, color, width)
            
            if route_node:
                route_node.reparentTo(self.routes_node)
                
                # Create route animation
                animation = self._create_route_animation(route_node, waypoints)
        
        # Always create the data structure
        route_viz = RouteVisualization(
            route_id=route_id,
            route_type=route_type,
            waypoints=waypoints,
            color=color,
            width=width,
            visual_node=route_node,
            animation=animation
        )
        
        self.route_visualizations[route_id] = route_viz
    
    def _create_route_geometry(self, waypoints: List[Point3D], color: Tuple[float, float, float, float], width: float) -> Optional[NodePath]:
        """Create 3D geometry for a route."""
        if not PANDA3D_AVAILABLE or len(waypoints) < 2:
            return None
        
        # Create route line with proper geometry
        route_node = NodePath("route_line")
        
        # Create vertex data first
        vertex_data = GeomVertexData("route", GeomVertexFormat.getV3(), Geom.UHStatic)
        vertex_data.setNumRows(len(waypoints))
        vertex_writer = GeomVertexWriter(vertex_data, "vertex")
        
        # Add vertices along the route
        for waypoint in waypoints:
            vertex_writer.addData3f(waypoint.x, waypoint.y, waypoint.z + 1.0)  # Above road level
        
        # Create geometry with vertex data
        geom = Geom(vertex_data)
        
        # Create line strip primitive
        lines = GeomLines(Geom.UHStatic)
        for i in range(len(waypoints) - 1):
            lines.addVertex(i)
            lines.addVertex(i + 1)
        lines.closePrimitive()
        
        geom.addPrimitive(lines)
        geom_node = GeomNode("route_geom")
        geom_node.addGeom(geom)
        
        route_geom_node = route_node.attachNewNode(geom_node)
        
        # Set visual properties
        route_node.setColor(*color)
        route_node.setRenderModeWireframe()
        route_node.setTwoSided(True)
        
        # Set line thickness (simplified approach)
        route_node.setScale(width, width, 1.0)
        
        return route_node
    
    def _create_route_animation(self, route_node: NodePath, waypoints: List[Point3D]) -> Optional[Any]:
        """Create animation for route visualization."""
        if not PANDA3D_AVAILABLE or len(waypoints) < 2:
            return None
        
        # Create flowing animation along the route using color waves
        # This creates a pulsing effect that travels along the route
        
        # Create color animation that pulses along the route
        original_color = route_node.getColor()
        highlight_color = Vec4(original_color.x * 1.5, original_color.y * 1.5, original_color.z * 1.5, 1.0)
        
        # Create pulsing sequence
        pulse_up = LerpColorInterval(route_node, 0.5, highlight_color)
        pulse_down = LerpColorInterval(route_node, 0.5, original_color)
        
        # Create flowing effect by varying the pulse timing
        flow_sequence = Sequence(
            pulse_up,
            pulse_down,
            Wait(0.2)  # Brief pause between pulses
        )
        flow_sequence.loop()
        
        return flow_sequence
    
    def _create_flow_particles(self, flow_data: Dict[str, Any]) -> None:
        """Create flow particles for traffic animation."""
        # Create particles for edges with high traffic flow
        for edge, density in self.edge_densities.items():
            if density > 0.3:  # Only show particles for moderate+ traffic
                self._create_edge_flow_particles(edge, density)
    
    def _create_edge_flow_particles(self, edge: Tuple[int, int], density: float) -> None:
        """Create flow particles for a single edge."""
        if edge not in self.edge_geometries:
            return
        
        geometry = self.edge_geometries[edge]
        if len(geometry) < 2:
            return
        
        # Create particles along the edge
        num_particles = max(1, int(density * 10))  # More particles for higher density
        particles = []
        
        if self.panda3d_enabled:
            for i in range(num_particles):
                particle_node = NodePath(f"flow_particle_{edge[0]}_{edge[1]}_{i}")
                particle_node.setScale(0.5, 0.5, 0.5)
                particle_node.setColor(1.0, 1.0, 0.0, 0.8)  # Yellow particles
                particle_node.reparentTo(self.flow_animation_node)
                particles.append(particle_node)
        else:
            # Create mock particles for testing
            for i in range(num_particles):
                particles.append(f"mock_particle_{edge[0]}_{edge[1]}_{i}")
        
        self.flow_particles[edge] = particles
    
    def _start_flow_animation(self) -> None:
        """Start flow particle animations."""
        if not self.panda3d_enabled:
            return
        
        # Animate particles along edges based on traffic flow
        for edge, particles in self.flow_particles.items():
            if edge not in self.edge_geometries:
                continue
            
            geometry = self.edge_geometries[edge]
            if len(geometry) < 2:
                continue
            
            density = self.edge_densities.get(edge, 0.0)
            
            for i, particle in enumerate(particles):
                # Create movement animation along the edge
                start_pos = geometry[0]
                end_pos = geometry[-1]
                
                # Stagger particle start times
                delay = i * 0.2
                
                # Speed based on traffic density (higher density = slower movement)
                speed_multiplier = max(0.2, 1.0 - density * 0.8)
                duration = 3.0 / speed_multiplier
                
                # Create movement sequence
                move_interval = LerpPosInterval(
                    particle, 
                    duration,
                    Point3(end_pos.x, end_pos.y, end_pos.z + 0.5),
                    startPos=Point3(start_pos.x, start_pos.y, start_pos.z + 0.5)
                )
                
                # Reset position and repeat
                reset_func = Func(particle.setPos, start_pos.x, start_pos.y, start_pos.z + 0.5)
                
                # Create looping sequence
                particle_sequence = Sequence(
                    Wait(delay),
                    move_interval,
                    reset_func
                )
                particle_sequence.loop()
                
                # Store animation for cleanup
                animation_id = f"flow_{edge[0]}_{edge[1]}_{i}"
                self.active_animations[animation_id] = particle_sequence
    
    def _animate_edge_particles(self, particles: List[NodePath], geometry: List[Point3D]) -> None:
        """Animate particles along an edge geometry."""
        if not PANDA3D_AVAILABLE or not particles or len(geometry) < 2:
            return
        
        # Create staggered animations for particles
        for i, particle in enumerate(particles):
            delay = i * 0.5  # Stagger particle start times
            
            # Create movement animation along geometry
            start_pos = Point3(geometry[0].x, geometry[0].y, geometry[0].z + 1.0)
            end_pos = Point3(geometry[-1].x, geometry[-1].y, geometry[-1].z + 1.0)
            
            move_interval = LerpPosInterval(particle, 3.0, end_pos, startPos=start_pos)
            
            # Create looping sequence with delay
            sequence = Sequence(
                Wait(delay),
                move_interval,
                Func(particle.setPos, start_pos)  # Reset position
            )
            sequence.loop()
    
    def _update_flow_animations(self) -> None:
        """Update flow animations based on current traffic density."""
        if not self.panda3d_enabled:
            return
        
        # Adjust animation speeds based on traffic density
        for edge, density in self.edge_densities.items():
            if edge in self.flow_particles:
                particles = self.flow_particles[edge]
                
                # Adjust particle speed based on density
                # Higher density = slower movement (congestion)
                speed_multiplier = max(0.2, 1.0 - density * 0.8)
                
                # Update particle colors based on density
                density_level = self._get_density_level(density)
                color = self.density_levels[density_level].color
                
                for particle in particles:
                    particle.setColor(*color)
                    
                    # Adjust particle visibility based on density
                    if density < 0.1:
                        particle.hide()
                    else:
                        particle.show()
                
                # Update animation speeds by restarting with new parameters
                for i, particle in enumerate(particles):
                    animation_id = f"flow_{edge[0]}_{edge[1]}_{i}"
                    if animation_id in self.active_animations:
                        # Stop current animation
                        self.active_animations[animation_id].finish()
                        
                        # Create new animation with updated speed
                        if edge in self.edge_geometries:
                            geometry = self.edge_geometries[edge]
                            if len(geometry) >= 2:
                                start_pos = geometry[0]
                                end_pos = geometry[-1]
                                
                                duration = 3.0 / speed_multiplier
                                delay = i * 0.2
                                
                                move_interval = LerpPosInterval(
                                    particle,
                                    duration,
                                    Point3(end_pos.x, end_pos.y, end_pos.z + 0.5),
                                    startPos=Point3(start_pos.x, start_pos.y, start_pos.z + 0.5)
                                )
                                
                                reset_func = Func(particle.setPos, start_pos.x, start_pos.y, start_pos.z + 0.5)
                                
                                particle_sequence = Sequence(
                                    Wait(delay),
                                    move_interval,
                                    reset_func
                                )
                                particle_sequence.loop()
                                
                                self.active_animations[animation_id] = particle_sequence
    
    def _update_performance_indicators(self, metrics: Dict[str, float]) -> None:
        """Update performance indicator displays."""
        if not self.panda3d_enabled:
            print(f"Performance indicators updated: {metrics}")
            return
        
        # Create or update performance indicator displays
        # This creates text nodes showing key performance metrics
        
        # Clear existing indicators
        if hasattr(self, 'performance_indicators'):
            for indicator in self.performance_indicators:
                indicator.removeNode()
        
        self.performance_indicators = []
        
        # Create text displays for key metrics
        y_offset = 0.8
        for metric_name, value in metrics.items():
            # Create text node for this metric
            text_node = NodePath(f"perf_indicator_{metric_name}")
            text_node.reparentTo(self.render)
            
            # Position in screen space (would need proper text rendering in full implementation)
            text_node.setPos(-0.9, 0, y_offset)
            text_node.setScale(0.05)
            
            # Color code based on metric type and value
            if 'fps' in metric_name.lower():
                # FPS: Green > 30, Yellow 20-30, Red < 20
                if value >= 30:
                    text_node.setColor(0, 1, 0, 1)  # Green
                elif value >= 20:
                    text_node.setColor(1, 1, 0, 1)  # Yellow
                else:
                    text_node.setColor(1, 0, 0, 1)  # Red
            elif 'congestion' in metric_name.lower():
                # Congestion: Green < 0.3, Yellow 0.3-0.7, Red > 0.7
                if value < 0.3:
                    text_node.setColor(0, 1, 0, 1)  # Green
                elif value < 0.7:
                    text_node.setColor(1, 1, 0, 1)  # Yellow
                else:
                    text_node.setColor(1, 0, 0, 1)  # Red
            else:
                text_node.setColor(1, 1, 1, 1)  # White default
            
            self.performance_indicators.append(text_node)
            y_offset -= 0.1
        
        print(f"Updated performance indicators: {list(metrics.keys())}")
    
    def _clear_congestion_hotspots(self) -> None:
        """Clear existing congestion hotspot visuals."""
        for hotspot in self.congestion_hotspots.values():
            if hotspot.animation:
                hotspot.animation.finish()
            if hotspot.visual_node and self.panda3d_enabled:
                hotspot.visual_node.removeNode()
        
        self.congestion_hotspots.clear()
    
    def _clear_emergency_alerts(self) -> None:
        """Clear existing emergency alert visuals."""
        for alert in self.emergency_alerts.values():
            for animation in alert.animations:
                if animation:
                    animation.finish()
            for element in alert.visual_elements:
                if element and self.panda3d_enabled:
                    element.removeNode()
        
        self.emergency_alerts.clear()
    
    def _clear_route_visualizations(self) -> None:
        """Clear existing route visualizations."""
        for route_viz in self.route_visualizations.values():
            if route_viz.animation:
                route_viz.animation.finish()
            if route_viz.visual_node and self.panda3d_enabled:
                route_viz.visual_node.removeNode()
        
        self.route_visualizations.clear()
    
    def create_real_time_congestion_indicators(self, edge_speeds: Dict[Tuple[int, int], float]) -> None:
        """
        Create real-time congestion indicators based on edge speeds.
        
        Args:
            edge_speeds: Dictionary mapping edges to current average speeds (km/h)
        """
        # Convert speeds to density levels for visualization
        edge_densities = {}
        
        for edge, speed in edge_speeds.items():
            # Convert speed to congestion level (inverse relationship)
            # Assume free flow speed is 50 km/h
            free_flow_speed = 50.0
            
            if speed <= 0:
                density = 1.0  # Complete congestion
            elif speed >= free_flow_speed:
                density = 0.0  # Free flow
            else:
                # Linear relationship: lower speed = higher density
                density = 1.0 - (speed / free_flow_speed)
            
            edge_densities[edge] = min(1.0, max(0.0, density))
        
        # Update traffic density visualization
        self.update_traffic_density(edge_densities)
        
        # Create pulsing indicators for highly congested areas
        high_congestion_edges = {edge: density for edge, density in edge_densities.items() if density > 0.7}
        
        if high_congestion_edges and self.panda3d_enabled:
            self._create_congestion_pulse_indicators(high_congestion_edges)
        
        if not self.panda3d_enabled:
            print(f"Creating congestion indicators for {len(edge_speeds)} edges (mock)")
        else:
            print(f"Created real-time congestion indicators for {len(edge_densities)} edges")
    
    def _create_congestion_pulse_indicators(self, congested_edges: Dict[Tuple[int, int], float]) -> None:
        """Create pulsing indicators for highly congested edges."""
        if not self.panda3d_enabled:
            return
        
        for edge, density in congested_edges.items():
            if edge not in self.edge_geometries:
                continue
            
            geometry = self.edge_geometries[edge]
            if len(geometry) < 2:
                continue
            
            # Create pulsing indicator at the center of the edge
            center_idx = len(geometry) // 2
            center_pos = geometry[center_idx]
            
            # Create warning indicator
            warning_node = NodePath(f"congestion_warning_{edge[0]}_{edge[1]}")
            warning_node.setPos(center_pos.x, center_pos.y, center_pos.z + 2.0)
            warning_node.setScale(5.0 * density, 5.0 * density, 1.0)
            warning_node.setColor(1.0, 0.0, 0.0, 0.8)  # Red warning
            warning_node.reparentTo(self.hotspots_node)
            
            # Create pulsing animation
            pulse_up = LerpScaleInterval(warning_node, 0.5, Vec3(1.5, 1.5, 1.0))
            pulse_down = LerpScaleInterval(warning_node, 0.5, Vec3(1.0, 1.0, 1.0))
            pulse_sequence = Sequence(pulse_up, pulse_down)
            pulse_sequence.loop()
            
            # Store for cleanup
            animation_id = f"congestion_pulse_{edge[0]}_{edge[1]}"
            self.active_animations[animation_id] = pulse_sequence