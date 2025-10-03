"""
MATLAB Data Exporter Implementation

This module implements the MATLABExporterInterface for exporting simulation data
to MATLAB-compatible formats including .mat files and analysis scripts.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import networkx as nx
import numpy as np

try:
    import scipy.io as sio
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    print("Warning: scipy not available. MATLAB export will use JSON format.")

from .interfaces import MATLABExporterInterface, MATLABDataFormat
from .config import MATLABConfig, ExportConfig


class MATLABDataExporter(MATLABExporterInterface):
    """Implementation of MATLAB data export functionality"""
    
    def __init__(self, config: Optional[MATLABConfig] = None):
        """Initialize MATLAB data exporter with configuration"""
        self.config = config or MATLABConfig()
        self.export_config = self.config.export_config
        
        # Ensure output directory exists
        os.makedirs(self.export_config.output_directory, exist_ok=True)
        
        # Track exported files for script generation
        self.exported_files: List[str] = []
    
    def export_vehicle_trajectories(self, trajectories: Dict[int, List[Dict[str, Any]]]) -> str:
        """Export vehicle trajectory data to .mat file format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config.get_export_file_path("trajectories", timestamp)
        
        # Prepare trajectory data for MATLAB
        matlab_data = self._prepare_trajectory_data(trajectories)
        
        if SCIPY_AVAILABLE:
            # Export as .mat file - use v5 format for better compatibility
            sio.savemat(filename, matlab_data, 
                       format='5',
                       do_compression=self.export_config.compression)
        else:
            # Fallback to JSON format
            json_filename = filename.replace('.mat', '.json')
            with open(json_filename, 'w') as f:
                json.dump(self._convert_numpy_to_list(matlab_data), f, indent=2)
            filename = json_filename
        
        self.exported_files.append(filename)
        return filename
    
    def export_road_network(self, graph: nx.Graph) -> str:
        """Export road network data compatible with MATLAB"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config.get_export_file_path("road_network", timestamp)
        
        # Prepare road network data for MATLAB
        matlab_data = self._prepare_road_network_data(graph)
        
        if SCIPY_AVAILABLE:
            format_version = '5' if self.export_config.mat_file_version == "-v5" else '4'
            sio.savemat(filename, matlab_data,
                       format=format_version,
                       do_compression=self.export_config.compression)
        else:
            json_filename = filename.replace('.mat', '.json')
            with open(json_filename, 'w') as f:
                json.dump(self._convert_numpy_to_list(matlab_data), f, indent=2)
            filename = json_filename
        
        self.exported_files.append(filename)
        return filename
    
    def export_traffic_metrics(self, metrics: Dict[str, Any]) -> str:
        """Export traffic analysis metrics"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config.get_export_file_path("metrics", timestamp)
        
        # Prepare metrics data for MATLAB
        matlab_data = self._prepare_metrics_data(metrics)
        
        if SCIPY_AVAILABLE:
            format_version = '5' if self.export_config.mat_file_version == "-v5" else '4'
            sio.savemat(filename, matlab_data,
                       format=format_version,
                       do_compression=self.export_config.compression)
        else:
            json_filename = filename.replace('.mat', '.json')
            with open(json_filename, 'w') as f:
                json.dump(self._convert_numpy_to_list(matlab_data), f, indent=2)
            filename = json_filename
        
        self.exported_files.append(filename)
        return filename
    
    def generate_analysis_script(self, data_files: List[str], analysis_type: str) -> str:
        """Generate MATLAB analysis script for exported data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_filename = os.path.join(
            self.export_config.output_directory,
            f"{self.export_config.file_prefix}_analysis_{analysis_type}_{timestamp}.m"
        )
        
        script_content = self._generate_matlab_script_content(data_files, analysis_type)
        
        with open(script_filename, 'w') as f:
            f.write(script_content)
        
        return script_filename
    
    def create_matlab_workspace(self, simulation_results: Dict[str, Any]) -> Dict[str, MATLABDataFormat]:
        """Create MATLAB workspace variables from simulation results"""
        workspace_vars = {}
        
        # Vehicle trajectories
        if 'trajectories' in simulation_results:
            trajectories_data = self._prepare_trajectory_data(simulation_results['trajectories'])
            workspace_vars['vehicle_trajectories'] = MATLABDataFormat(
                variable_name='vehicle_trajectories',
                data=trajectories_data,
                data_type='struct',
                description='Vehicle trajectory data with positions, velocities, and timestamps'
            )
        
        # Road network
        if 'road_network' in simulation_results:
            network_data = self._prepare_road_network_data(simulation_results['road_network'])
            workspace_vars['road_network'] = MATLABDataFormat(
                variable_name='road_network',
                data=network_data,
                data_type='struct',
                description='Road network graph with nodes, edges, and attributes'
            )
        
        # Traffic metrics
        if 'metrics' in simulation_results:
            metrics_data = self._prepare_metrics_data(simulation_results['metrics'])
            workspace_vars['traffic_metrics'] = MATLABDataFormat(
                variable_name='traffic_metrics',
                data=metrics_data,
                data_type='struct',
                description='Traffic analysis metrics including congestion and flow rates'
            )
        
        # Simulation metadata
        workspace_vars['simulation_info'] = MATLABDataFormat(
            variable_name='simulation_info',
            data={
                'timestamp': datetime.now().isoformat(),
                'duration': simulation_results.get('duration', 0),
                'vehicle_count': simulation_results.get('vehicle_count', 0),
                'coordinate_system': self.export_config.coordinate_system
            },
            data_type='struct',
            description='Simulation metadata and configuration information'
        )
        
        return workspace_vars
    
    def _prepare_trajectory_data(self, trajectories: Dict[int, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Prepare trajectory data for MATLAB export"""
        matlab_data = {
            'vehicle_ids': [],
            'timestamps': [],
            'positions': [],
            'velocities': [] if self.export_config.include_velocity_data else None,
            'accelerations': [] if self.export_config.include_acceleration_data else None,
            'metadata': {
                'coordinate_system': self.export_config.coordinate_system,
                'sampling_rate': self.export_config.trajectory_sampling_rate,
                'num_vehicles': len(trajectories)
            }
        }
        
        for vehicle_id, trajectory in trajectories.items():
            if not trajectory:
                continue
            
            # Extract trajectory data
            times = [point.get('timestamp', 0) for point in trajectory]
            positions = [(point.get('x', 0), point.get('y', 0)) for point in trajectory]
            
            matlab_data['vehicle_ids'].append(vehicle_id)
            matlab_data['timestamps'].append(np.array(times))
            matlab_data['positions'].append(np.array(positions))
            
            if self.export_config.include_velocity_data:
                velocities = [(point.get('vx', 0), point.get('vy', 0)) for point in trajectory]
                matlab_data['velocities'].append(np.array(velocities))
            
            if self.export_config.include_acceleration_data:
                accelerations = [(point.get('ax', 0), point.get('ay', 0)) for point in trajectory]
                matlab_data['accelerations'].append(np.array(accelerations))
        
        # Convert lists to numpy arrays for MATLAB compatibility
        matlab_data['vehicle_ids'] = np.array(matlab_data['vehicle_ids'])
        
        # Remove None values
        matlab_data = {k: v for k, v in matlab_data.items() if v is not None}
        
        return matlab_data    

    def _prepare_road_network_data(self, graph: nx.Graph) -> Dict[str, Any]:
        """Prepare road network data for MATLAB export"""
        matlab_data = {
            'nodes': {
                'ids': [],
                'coordinates': [],
                'attributes': []
            },
            'edges': {
                'source_nodes': [],
                'target_nodes': [],
                'lengths': [],
                'geometries': [],
                'attributes': []
            },
            'metadata': {
                'num_nodes': graph.number_of_nodes(),
                'num_edges': graph.number_of_edges(),
                'coordinate_system': self.export_config.coordinate_system,
                'includes_lane_geometry': self.export_config.include_lane_geometry,
                'includes_traffic_signals': self.export_config.include_traffic_signals
            }
        }
        
        # Extract node data
        for node_id, node_data in graph.nodes(data=True):
            matlab_data['nodes']['ids'].append(node_id)
            matlab_data['nodes']['coordinates'].append([
                node_data.get('x', 0),
                node_data.get('y', 0)
            ])
            
            # Extract relevant node attributes
            node_attrs = {}
            if self.export_config.include_traffic_signals:
                node_attrs['traffic_signal'] = node_data.get('highway') == 'traffic_signals'
            
            matlab_data['nodes']['attributes'].append(node_attrs)
        
        # Extract edge data
        for source, target, edge_data in graph.edges(data=True):
            matlab_data['edges']['source_nodes'].append(source)
            matlab_data['edges']['target_nodes'].append(target)
            matlab_data['edges']['lengths'].append(edge_data.get('length', 0))
            
            # Extract geometry if available
            geometry = edge_data.get('geometry')
            if geometry and self.export_config.include_lane_geometry:
                if hasattr(geometry, 'coords'):
                    coords = list(geometry.coords)
                    matlab_data['edges']['geometries'].append(coords)
                else:
                    matlab_data['edges']['geometries'].append([])
            else:
                matlab_data['edges']['geometries'].append([])
            
            # Extract edge attributes
            edge_attrs = {
                'highway': edge_data.get('highway', 'unknown'),
                'lanes': edge_data.get('lanes', 1),
                'maxspeed': edge_data.get('maxspeed', 50)
            }
            
            if self.export_config.include_road_conditions:
                edge_attrs['road_quality'] = edge_data.get('road_quality', 'good')
                edge_attrs['surface'] = edge_data.get('surface', 'asphalt')
            
            matlab_data['edges']['attributes'].append(edge_attrs)
        
        # Convert to numpy arrays
        matlab_data['nodes']['ids'] = np.array(matlab_data['nodes']['ids'])
        matlab_data['nodes']['coordinates'] = np.array(matlab_data['nodes']['coordinates'])
        matlab_data['edges']['source_nodes'] = np.array(matlab_data['edges']['source_nodes'])
        matlab_data['edges']['target_nodes'] = np.array(matlab_data['edges']['target_nodes'])
        matlab_data['edges']['lengths'] = np.array(matlab_data['edges']['lengths'])
        
        return matlab_data
    
    def _prepare_metrics_data(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare traffic metrics data for MATLAB export"""
        matlab_data = {
            'congestion_metrics': {},
            'flow_metrics': {},
            'safety_metrics': {},
            'environmental_metrics': {},
            'metadata': {
                'aggregation_interval': self.export_config.metrics_aggregation_interval,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Congestion metrics
        if self.export_config.include_congestion_metrics and 'congestion' in metrics:
            congestion = metrics['congestion']
            matlab_data['congestion_metrics'] = {
                'average_speed': np.array(congestion.get('average_speeds', [])),
                'density': np.array(congestion.get('densities', [])),
                'flow_rate': np.array(congestion.get('flow_rates', [])),
                'level_of_service': congestion.get('level_of_service', []),
                'bottleneck_locations': congestion.get('bottlenecks', [])
            }
        
        # Flow metrics
        if 'flow' in metrics:
            flow = metrics['flow']
            matlab_data['flow_metrics'] = {
                'total_vehicles': flow.get('total_vehicles', 0),
                'completed_trips': flow.get('completed_trips', 0),
                'average_travel_time': flow.get('average_travel_time', 0),
                'throughput': np.array(flow.get('throughput_history', [])),
                'queue_lengths': np.array(flow.get('queue_lengths', []))
            }
        
        # Safety metrics
        if self.export_config.include_safety_metrics and 'safety' in metrics:
            safety = metrics['safety']
            matlab_data['safety_metrics'] = {
                'near_misses': safety.get('near_misses', 0),
                'conflicts': safety.get('conflicts', []),
                'emergency_braking_events': safety.get('emergency_braking', 0),
                'safety_critical_events': safety.get('critical_events', [])
            }
        
        # Environmental metrics
        if self.export_config.include_environmental_metrics and 'environmental' in metrics:
            env = metrics['environmental']
            matlab_data['environmental_metrics'] = {
                'fuel_consumption': env.get('fuel_consumption', 0),
                'emissions': env.get('emissions', {}),
                'noise_levels': np.array(env.get('noise_levels', [])),
                'air_quality_impact': env.get('air_quality', {})
            }
        
        return matlab_data
    
    def _generate_matlab_script_content(self, data_files: List[str], analysis_type: str) -> str:
        """Generate MATLAB script content for data analysis"""
        script_lines = [
            "% MATLAB Analysis Script for Indian Traffic Digital Twin",
            f"% Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"% Analysis Type: {analysis_type}",
            "%",
            "% This script loads and analyzes traffic simulation data",
            "",
            "clear; clc; close all;",
            "",
            "% Add paths if needed",
            "% addpath('path/to/your/functions');",
            "",
            "% Load data files"
        ]
        
        # Add data loading commands
        for i, file_path in enumerate(data_files):
            file_name = Path(file_path).stem
            if file_path.endswith('.mat'):
                script_lines.append(f"data_{i+1} = load('{file_path}');")
            elif file_path.endswith('.json'):
                script_lines.append(f"data_{i+1} = jsondecode(fileread('{file_path}'));")
        
        script_lines.extend([
            "",
            "% Analysis based on type"
        ])
        
        # Add analysis-specific code
        if analysis_type == "trajectory_analysis":
            script_lines.extend(self._get_trajectory_analysis_code())
        elif analysis_type == "congestion_analysis":
            script_lines.extend(self._get_congestion_analysis_code())
        elif analysis_type == "network_analysis":
            script_lines.extend(self._get_network_analysis_code())
        else:
            script_lines.extend([
                "% Custom analysis - add your code here",
                "fprintf('Data loaded successfully. Add your analysis code.\\n');"
            ])
        
        script_lines.extend([
            "",
            "% Save results",
            f"save('analysis_results_{analysis_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mat');",
            "",
            "fprintf('Analysis completed successfully.\\n');"
        ])
        
        return '\n'.join(script_lines)
    
    def _get_trajectory_analysis_code(self) -> List[str]:
        """Generate MATLAB code for trajectory analysis"""
        return [
            "% Trajectory Analysis",
            "if exist('data_1', 'var') && isfield(data_1, 'vehicle_trajectories')",
            "    trajectories = data_1.vehicle_trajectories;",
            "    ",
            "    % Plot vehicle trajectories",
            "    figure('Name', 'Vehicle Trajectories');",
            "    hold on;",
            "    for i = 1:length(trajectories.vehicle_ids)",
            "        positions = trajectories.positions{i};",
            "        plot(positions(:,1), positions(:,2), 'LineWidth', 1.5);",
            "    end",
            "    xlabel('X Coordinate (m)');",
            "    ylabel('Y Coordinate (m)');",
            "    title('Vehicle Trajectories');",
            "    grid on;",
            "    ",
            "    % Calculate trajectory statistics",
            "    total_distance = zeros(length(trajectories.vehicle_ids), 1);",
            "    for i = 1:length(trajectories.vehicle_ids)",
            "        positions = trajectories.positions{i};",
            "        if size(positions, 1) > 1",
            "            distances = sqrt(sum(diff(positions).^2, 2));",
            "            total_distance(i) = sum(distances);",
            "        end",
            "    end",
            "    ",
            "    fprintf('Average travel distance: %.2f m\\n', mean(total_distance));",
            "    fprintf('Max travel distance: %.2f m\\n', max(total_distance));",
            "end"
        ]
    
    def _get_congestion_analysis_code(self) -> List[str]:
        """Generate MATLAB code for congestion analysis"""
        return [
            "% Congestion Analysis",
            "if exist('data_1', 'var') && isfield(data_1, 'traffic_metrics')",
            "    metrics = data_1.traffic_metrics;",
            "    ",
            "    % Plot congestion metrics",
            "    if isfield(metrics, 'congestion_metrics')",
            "        congestion = metrics.congestion_metrics;",
            "        ",
            "        figure('Name', 'Congestion Analysis');",
            "        subplot(2,2,1);",
            "        plot(congestion.average_speed);",
            "        title('Average Speed Over Time');",
            "        xlabel('Time Step');",
            "        ylabel('Speed (m/s)');",
            "        ",
            "        subplot(2,2,2);",
            "        plot(congestion.density);",
            "        title('Traffic Density');",
            "        xlabel('Time Step');",
            "        ylabel('Density (vehicles/km)');",
            "        ",
            "        subplot(2,2,3);",
            "        plot(congestion.flow_rate);",
            "        title('Flow Rate');",
            "        xlabel('Time Step');",
            "        ylabel('Flow (vehicles/hour)');",
            "        ",
            "        % Calculate congestion statistics",
            "        avg_speed = mean(congestion.average_speed);",
            "        max_density = max(congestion.density);",
            "        avg_flow = mean(congestion.flow_rate);",
            "        ",
            "        fprintf('Average speed: %.2f m/s\\n', avg_speed);",
            "        fprintf('Maximum density: %.2f vehicles/km\\n', max_density);",
            "        fprintf('Average flow rate: %.2f vehicles/hour\\n', avg_flow);",
            "    end",
            "end"
        ]
    
    def _get_network_analysis_code(self) -> List[str]:
        """Generate MATLAB code for network analysis"""
        return [
            "% Network Analysis",
            "if exist('data_1', 'var') && isfield(data_1, 'road_network')",
            "    network = data_1.road_network;",
            "    ",
            "    % Plot road network",
            "    figure('Name', 'Road Network');",
            "    hold on;",
            "    ",
            "    % Plot edges",
            "    for i = 1:length(network.edges.source_nodes)",
            "        source_idx = find(network.nodes.ids == network.edges.source_nodes(i));",
            "        target_idx = find(network.nodes.ids == network.edges.target_nodes(i));",
            "        ",
            "        if ~isempty(source_idx) && ~isempty(target_idx)",
            "            source_pos = network.nodes.coordinates(source_idx, :);",
            "            target_pos = network.nodes.coordinates(target_idx, :);",
            "            plot([source_pos(1), target_pos(1)], [source_pos(2), target_pos(2)], 'b-');",
            "        end",
            "    end",
            "    ",
            "    % Plot nodes",
            "    scatter(network.nodes.coordinates(:,1), network.nodes.coordinates(:,2), 'ro');",
            "    ",
            "    xlabel('X Coordinate (m)');",
            "    ylabel('Y Coordinate (m)');",
            "    title('Road Network Structure');",
            "    grid on;",
            "    axis equal;",
            "    ",
            "    % Network statistics",
            "    num_nodes = network.metadata.num_nodes;",
            "    num_edges = network.metadata.num_edges;",
            "    avg_edge_length = mean(network.edges.lengths);",
            "    ",
            "    fprintf('Network nodes: %d\\n', num_nodes);",
            "    fprintf('Network edges: %d\\n', num_edges);",
            "    fprintf('Average edge length: %.2f m\\n', avg_edge_length);",
            "end"
        ]
    
    def _convert_numpy_to_list(self, data: Any) -> Any:
        """Convert numpy arrays to lists for JSON serialization"""
        if isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, dict):
            return {k: self._convert_numpy_to_list(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_numpy_to_list(item) for item in data]
        else:
            return data