"""
RoadRunner Scene Importer Implementation

This module implements the RoadRunnerImporterInterface for importing
RoadRunner scene files and converting them to OSMnx-compatible formats.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import networkx as nx
import numpy as np

try:
    import scipy.io as sio
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

from .interfaces import RoadRunnerImporterInterface, RoadRunnerScene
from .config import MATLABConfig, ImportConfig


class RoadRunnerImporter(RoadRunnerImporterInterface):
    """Implementation of RoadRunner scene file import functionality"""
    
    def __init__(self, config: Optional[MATLABConfig] = None):
        """Initialize RoadRunner importer with configuration"""
        self.config = config or MATLABConfig()
        self.import_config = self.config.import_config
        
        # Validation results
        self.last_validation_issues: List[str] = []
    
    def import_scene_file(self, filepath: str) -> RoadRunnerScene:
        """Import RoadRunner scene file"""
        file_path = Path(filepath)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Scene file not found: {filepath}")
        
        # Check file extension
        if file_path.suffix not in self.import_config.supported_file_extensions:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Backup original file if requested
        if self.import_config.backup_original_files:
            self._backup_file(file_path)
        
        # Parse based on file type
        if file_path.suffix == '.rrscene':
            scene_data = self._parse_rrscene_file(filepath)
        elif file_path.suffix == '.mat':
            scene_data = self._parse_mat_file(filepath)
        elif file_path.suffix == '.json':
            scene_data = self._parse_json_file(filepath)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        # Create RoadRunnerScene object
        scene = RoadRunnerScene(
            scene_name=file_path.stem,
            road_network=scene_data.get('road_network', {}),
            vehicle_paths=scene_data.get('vehicle_paths', []),
            scenario_config=scene_data.get('scenario_config', {}),
            metadata=scene_data.get('metadata', {})
        )
        
        # Validate if requested
        if self.import_config.validate_on_import:
            is_valid, issues = self.validate_scene_compatibility(scene)
            if not is_valid and self.import_config.report_import_warnings:
                print(f"Warning: Scene validation issues found: {issues}")
        
        return scene
    
    def convert_to_osmnx_graph(self, scene: RoadRunnerScene) -> nx.Graph:
        """Convert RoadRunner scene to OSMnx-compatible graph"""
        G = nx.Graph()
        
        road_network = scene.road_network
        
        # Add nodes from RoadRunner data
        if 'nodes' in road_network:
            nodes_data = road_network['nodes']
            for i, node_data in enumerate(nodes_data):
                node_id = node_data.get('id', i)
                
                # Convert coordinates if needed
                x, y = self._convert_coordinates(
                    node_data.get('x', 0),
                    node_data.get('y', 0)
                )
                
                # Add node with attributes
                G.add_node(node_id, 
                          x=x, y=y,
                          osmid=node_id,
                          **self._extract_node_attributes(node_data))
        
        # Add edges from RoadRunner data
        if 'edges' in road_network:
            edges_data = road_network['edges']
            for edge_data in edges_data:
                source = edge_data.get('source')
                target = edge_data.get('target')
                
                if source is not None and target is not None:
                    # Extract edge attributes
                    edge_attrs = self._extract_edge_attributes(edge_data)
                    
                    # Add geometry if available
                    if 'geometry' in edge_data and self.import_config.extract_lane_markings:
                        geometry = self._convert_geometry(edge_data['geometry'])
                        if geometry:
                            edge_attrs['geometry'] = geometry
                    
                    G.add_edge(source, target, **edge_attrs)
        
        # Validate network connectivity if requested
        if self.import_config.check_network_connectivity:
            if not nx.is_connected(G):
                print("Warning: Imported network is not fully connected")
        
        return G
    
    def extract_vehicle_paths(self, scene: RoadRunnerScene) -> List[Dict[str, Any]]:
        """Extract predefined vehicle paths from scene"""
        vehicle_paths = []
        
        for path_data in scene.vehicle_paths:
            # Process path waypoints
            waypoints = path_data.get('waypoints', [])
            processed_waypoints = []
            
            for waypoint in waypoints:
                x, y = self._convert_coordinates(
                    waypoint.get('x', 0),
                    waypoint.get('y', 0)
                )
                
                processed_waypoint = {
                    'x': x,
                    'y': y,
                    'timestamp': waypoint.get('timestamp', 0),
                    'speed': waypoint.get('speed', 0),
                    'heading': waypoint.get('heading', 0)
                }
                processed_waypoints.append(processed_waypoint)
            
            # Interpolate sparse paths if requested
            if (self.import_config.interpolate_sparse_paths and 
                len(processed_waypoints) > 1):
                processed_waypoints = self._interpolate_path(processed_waypoints)
            
            # Apply path smoothing if requested
            if self.import_config.path_smoothing and len(processed_waypoints) > 2:
                processed_waypoints = self._smooth_path(processed_waypoints)
            
            # Check minimum path length
            path_length = self._calculate_path_length(processed_waypoints)
            if path_length >= self.import_config.minimum_path_length:
                vehicle_path = {
                    'vehicle_id': path_data.get('vehicle_id'),
                    'vehicle_type': path_data.get('vehicle_type', 'car'),
                    'waypoints': processed_waypoints,
                    'path_length': path_length,
                    'metadata': path_data.get('metadata', {})
                }
                vehicle_paths.append(vehicle_path)
        
        return vehicle_paths
    
    def parse_scenario_configuration(self, scene: RoadRunnerScene) -> Dict[str, Any]:
        """Parse scenario configuration from RoadRunner scene"""
        config = scene.scenario_config.copy()
        
        # Extract simulation parameters
        simulation_config = {
            'duration': config.get('simulation_duration', 60.0),
            'time_step': config.get('time_step', 0.1),
            'weather_conditions': config.get('weather', {}),
            'traffic_density': config.get('traffic_density', 'medium'),
            'spawn_rate': config.get('spawn_rate', 1.0)
        }
        
        # Extract vehicle configuration
        vehicle_config = {
            'vehicle_types': config.get('vehicle_types', ['car']),
            'vehicle_mix': config.get('vehicle_mix', {'car': 1.0}),
            'behavior_parameters': config.get('behavior_parameters', {})
        }
        
        # Extract environment configuration
        environment_config = {
            'road_conditions': config.get('road_conditions', {}),
            'traffic_signals': config.get('traffic_signals', []),
            'construction_zones': config.get('construction_zones', []),
            'emergency_scenarios': config.get('emergency_scenarios', [])
        }
        
        return {
            'simulation': simulation_config,
            'vehicles': vehicle_config,
            'environment': environment_config,
            'metadata': scene.metadata
        }
    
    def validate_scene_compatibility(self, scene: RoadRunnerScene) -> Tuple[bool, List[str]]:
        """Validate scene compatibility and return any issues"""
        issues = []
        
        # Check road network structure
        if not scene.road_network:
            issues.append("No road network data found")
        else:
            # Check for required fields
            if 'nodes' not in scene.road_network:
                issues.append("Road network missing nodes data")
            if 'edges' not in scene.road_network:
                issues.append("Road network missing edges data")
            
            # Validate nodes
            nodes = scene.road_network.get('nodes', [])
            for i, node in enumerate(nodes):
                if 'x' not in node or 'y' not in node:
                    issues.append(f"Node {i} missing coordinate data")
            
            # Validate edges
            edges = scene.road_network.get('edges', [])
            node_ids = {node.get('id', i) for i, node in enumerate(nodes)}
            for i, edge in enumerate(edges):
                source = edge.get('source')
                target = edge.get('target')
                if source not in node_ids:
                    issues.append(f"Edge {i} references invalid source node: {source}")
                if target not in node_ids:
                    issues.append(f"Edge {i} references invalid target node: {target}")
        
        # Validate vehicle paths if present
        if self.import_config.validate_vehicle_paths:
            for i, path in enumerate(scene.vehicle_paths):
                waypoints = path.get('waypoints', [])
                if len(waypoints) < 2:
                    issues.append(f"Vehicle path {i} has insufficient waypoints")
                
                for j, waypoint in enumerate(waypoints):
                    if 'x' not in waypoint or 'y' not in waypoint:
                        issues.append(f"Vehicle path {i}, waypoint {j} missing coordinates")
        
        # Check coordinate system compatibility
        metadata = scene.metadata
        coord_system = metadata.get('coordinate_system')
        if coord_system and coord_system not in ['utm', 'latlon', 'local']:
            issues.append(f"Unsupported coordinate system: {coord_system}")
        
        self.last_validation_issues = issues
        return len(issues) == 0, issues    

    def _backup_file(self, file_path: Path) -> None:
        """Create backup of original file"""
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        backup_path.write_bytes(file_path.read_bytes())
    
    def _parse_rrscene_file(self, filepath: str) -> Dict[str, Any]:
        """Parse RoadRunner .rrscene file (XML format)"""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            scene_data = {
                'road_network': self._extract_road_network_from_xml(root),
                'vehicle_paths': self._extract_vehicle_paths_from_xml(root),
                'scenario_config': self._extract_scenario_config_from_xml(root),
                'metadata': {
                    'file_format': 'rrscene',
                    'coordinate_system': root.get('coordinateSystem', 'local'),
                    'version': root.get('version', '1.0')
                }
            }
            
            return scene_data
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid RoadRunner scene file format: {e}")
    
    def _parse_mat_file(self, filepath: str) -> Dict[str, Any]:
        """Parse MATLAB .mat file"""
        if not SCIPY_AVAILABLE:
            raise ImportError("scipy is required to import .mat files")
        
        try:
            mat_data = sio.loadmat(filepath)
            
            # Convert MATLAB structures to Python dictionaries
            scene_data = {
                'road_network': self._convert_matlab_struct(mat_data.get('roadNetwork', {})),
                'vehicle_paths': self._convert_matlab_struct(mat_data.get('vehiclePaths', [])),
                'scenario_config': self._convert_matlab_struct(mat_data.get('scenarioConfig', {})),
                'metadata': {
                    'file_format': 'mat',
                    'coordinate_system': 'local'
                }
            }
            
            return scene_data
            
        except Exception as e:
            raise ValueError(f"Error reading MATLAB file: {e}")
    
    def _parse_json_file(self, filepath: str) -> Dict[str, Any]:
        """Parse JSON scene file"""
        try:
            with open(filepath, 'r') as f:
                scene_data = json.load(f)
            
            # Ensure required structure
            if 'metadata' not in scene_data:
                scene_data['metadata'] = {}
            scene_data['metadata']['file_format'] = 'json'
            
            return scene_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
    
    def _extract_road_network_from_xml(self, root: ET.Element) -> Dict[str, Any]:
        """Extract road network data from XML"""
        road_network = {'nodes': [], 'edges': []}
        
        # Extract nodes
        for node_elem in root.findall('.//Node'):
            node_data = {
                'id': int(node_elem.get('id', 0)),
                'x': float(node_elem.get('x', 0)),
                'y': float(node_elem.get('y', 0)),
                'z': float(node_elem.get('z', 0)) if node_elem.get('z') else None
            }
            
            # Extract additional attributes
            for attr in node_elem.attrib:
                if attr not in ['id', 'x', 'y', 'z']:
                    node_data[attr] = node_elem.get(attr)
            
            road_network['nodes'].append(node_data)
        
        # Extract edges/roads
        for road_elem in root.findall('.//Road'):
            edge_data = {
                'source': int(road_elem.get('startNode', 0)),
                'target': int(road_elem.get('endNode', 0)),
                'length': float(road_elem.get('length', 0)),
                'lanes': int(road_elem.get('lanes', 1)),
                'highway': road_elem.get('type', 'unclassified')
            }
            
            # Extract geometry if available
            geometry_elem = road_elem.find('Geometry')
            if geometry_elem is not None:
                edge_data['geometry'] = self._parse_geometry_from_xml(geometry_elem)
            
            road_network['edges'].append(edge_data)
        
        return road_network
    
    def _extract_vehicle_paths_from_xml(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract vehicle paths from XML"""
        vehicle_paths = []
        
        for vehicle_elem in root.findall('.//Vehicle'):
            vehicle_data = {
                'vehicle_id': int(vehicle_elem.get('id', 0)),
                'vehicle_type': vehicle_elem.get('type', 'car'),
                'waypoints': [],
                'metadata': {}
            }
            
            # Extract waypoints
            for waypoint_elem in vehicle_elem.findall('.//Waypoint'):
                waypoint = {
                    'x': float(waypoint_elem.get('x', 0)),
                    'y': float(waypoint_elem.get('y', 0)),
                    'timestamp': float(waypoint_elem.get('time', 0)),
                    'speed': float(waypoint_elem.get('speed', 0)),
                    'heading': float(waypoint_elem.get('heading', 0))
                }
                vehicle_data['waypoints'].append(waypoint)
            
            vehicle_paths.append(vehicle_data)
        
        return vehicle_paths
    
    def _extract_scenario_config_from_xml(self, root: ET.Element) -> Dict[str, Any]:
        """Extract scenario configuration from XML"""
        config = {}
        
        scenario_elem = root.find('.//Scenario')
        if scenario_elem is not None:
            config['simulation_duration'] = float(scenario_elem.get('duration', 60.0))
            config['time_step'] = float(scenario_elem.get('timeStep', 0.1))
            config['weather'] = scenario_elem.get('weather', 'clear')
            config['traffic_density'] = scenario_elem.get('trafficDensity', 'medium')
        
        return config
    
    def _parse_geometry_from_xml(self, geometry_elem: ET.Element) -> List[Tuple[float, float]]:
        """Parse geometry coordinates from XML"""
        coordinates = []
        
        for point_elem in geometry_elem.findall('.//Point'):
            x = float(point_elem.get('x', 0))
            y = float(point_elem.get('y', 0))
            coordinates.append((x, y))
        
        return coordinates
    
    def _convert_matlab_struct(self, matlab_data: Any) -> Any:
        """Convert MATLAB structures to Python data types"""
        if isinstance(matlab_data, np.ndarray):
            if matlab_data.dtype.names:  # Structured array (MATLAB struct)
                result = {}
                for name in matlab_data.dtype.names:
                    result[name] = self._convert_matlab_struct(matlab_data[name][0, 0])
                return result
            else:
                return matlab_data.tolist()
        elif isinstance(matlab_data, (list, tuple)):
            return [self._convert_matlab_struct(item) for item in matlab_data]
        else:
            return matlab_data
    
    def _convert_coordinates(self, x: float, y: float) -> Tuple[float, float]:
        """Convert coordinates between coordinate systems if needed"""
        if self.import_config.coordinate_system_conversion:
            # Implement coordinate system conversion logic here
            # For now, return as-is
            pass
        
        return x, y
    
    def _convert_geometry(self, geometry_data: Any) -> Optional[Any]:
        """Convert geometry data to appropriate format"""
        if isinstance(geometry_data, list):
            # Assume list of coordinate pairs
            return geometry_data
        elif isinstance(geometry_data, dict):
            # Extract coordinates from dictionary
            return geometry_data.get('coordinates', [])
        else:
            return None
    
    def _extract_node_attributes(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant node attributes for OSMnx compatibility"""
        attributes = {}
        
        # Map RoadRunner attributes to OSM-style attributes
        if 'type' in node_data:
            attributes['highway'] = node_data['type']
        
        if 'elevation' in node_data or 'z' in node_data:
            attributes['elevation'] = node_data.get('elevation', node_data.get('z', 0))
        
        # Copy other attributes
        for key, value in node_data.items():
            if key not in ['id', 'x', 'y', 'z']:
                attributes[key] = value
        
        return attributes
    
    def _extract_edge_attributes(self, edge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant edge attributes for OSMnx compatibility"""
        attributes = {}
        
        # Required OSMnx attributes
        attributes['length'] = edge_data.get('length', 0)
        attributes['highway'] = edge_data.get('highway', edge_data.get('type', 'unclassified'))
        
        # Optional attributes
        if 'lanes' in edge_data:
            attributes['lanes'] = edge_data['lanes']
        
        if 'maxspeed' in edge_data:
            attributes['maxspeed'] = edge_data['maxspeed']
        elif 'speedLimit' in edge_data:
            attributes['maxspeed'] = edge_data['speedLimit']
        
        if 'surface' in edge_data:
            attributes['surface'] = edge_data['surface']
        
        # Generate osmid for compatibility
        attributes['osmid'] = f"rr_{edge_data.get('source', 0)}_{edge_data.get('target', 0)}"
        
        return attributes
    
    def _interpolate_path(self, waypoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Interpolate sparse vehicle paths"""
        if len(waypoints) < 2:
            return waypoints
        
        interpolated = [waypoints[0]]
        
        for i in range(1, len(waypoints)):
            prev_wp = waypoints[i-1]
            curr_wp = waypoints[i]
            
            # Calculate distance between waypoints
            dx = curr_wp['x'] - prev_wp['x']
            dy = curr_wp['y'] - prev_wp['y']
            distance = np.sqrt(dx**2 + dy**2)
            
            # Add intermediate points if distance is large
            if distance > 10.0:  # 10 meter threshold
                num_points = int(distance / 5.0)  # 5 meter intervals
                for j in range(1, num_points):
                    t = j / num_points
                    interp_wp = {
                        'x': prev_wp['x'] + t * dx,
                        'y': prev_wp['y'] + t * dy,
                        'timestamp': prev_wp['timestamp'] + t * (curr_wp['timestamp'] - prev_wp['timestamp']),
                        'speed': prev_wp['speed'] + t * (curr_wp['speed'] - prev_wp['speed']),
                        'heading': prev_wp['heading'] + t * (curr_wp['heading'] - prev_wp['heading'])
                    }
                    interpolated.append(interp_wp)
            
            interpolated.append(curr_wp)
        
        return interpolated
    
    def _smooth_path(self, waypoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply smoothing to vehicle paths"""
        if len(waypoints) < 3:
            return waypoints
        
        smoothed = [waypoints[0]]  # Keep first point
        
        # Simple moving average smoothing
        for i in range(1, len(waypoints) - 1):
            prev_wp = waypoints[i-1]
            curr_wp = waypoints[i]
            next_wp = waypoints[i+1]
            
            smoothed_wp = {
                'x': (prev_wp['x'] + curr_wp['x'] + next_wp['x']) / 3,
                'y': (prev_wp['y'] + curr_wp['y'] + next_wp['y']) / 3,
                'timestamp': curr_wp['timestamp'],
                'speed': (prev_wp['speed'] + curr_wp['speed'] + next_wp['speed']) / 3,
                'heading': curr_wp['heading']  # Keep original heading
            }
            smoothed.append(smoothed_wp)
        
        smoothed.append(waypoints[-1])  # Keep last point
        
        return smoothed
    
    def _calculate_path_length(self, waypoints: List[Dict[str, Any]]) -> float:
        """Calculate total path length"""
        if len(waypoints) < 2:
            return 0.0
        
        total_length = 0.0
        for i in range(1, len(waypoints)):
            prev_wp = waypoints[i-1]
            curr_wp = waypoints[i]
            
            dx = curr_wp['x'] - prev_wp['x']
            dy = curr_wp['y'] - prev_wp['y']
            total_length += np.sqrt(dx**2 + dy**2)
        
        return total_length