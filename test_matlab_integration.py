"""
Test script for MATLAB Integration functionality

This script tests all components of the MATLAB integration system
and demonstrates how to use them with real data.
"""

import os
import json
import numpy as np
import networkx as nx
from datetime import datetime
from typing import Dict, List, Any

# Import MATLAB integration components
from matlab_integration import (
    MATLABDataExporter,
    RoadRunnerImporter,
    SimulinkConnector,
    MATLABScriptGenerator,
    MATLABConfig,
    setup_matlab_integration,
    get_integration_status
)

def create_sample_data():
    """Create sample simulation data for testing"""
    print("Creating sample simulation data...")
    
    # Sample vehicle trajectories
    trajectories = {}
    for vehicle_id in range(1, 6):  # 5 vehicles
        trajectory = []
        for t in range(0, 100, 10):  # 10 time steps
            point = {
                'timestamp': t,
                'x': 10 * t + vehicle_id * 5,
                'y': 5 * t + np.sin(t * 0.1) * 10,
                'vx': 10 + np.random.normal(0, 1),
                'vy': 5 + np.random.normal(0, 0.5),
                'ax': np.random.normal(0, 0.2),
                'ay': np.random.normal(0, 0.1)
            }
            trajectory.append(point)
        trajectories[vehicle_id] = trajectory
    
    # Sample road network (simple grid)
    G = nx.Graph()
    
    # Add nodes (intersections)
    for i in range(4):
        for j in range(4):
            node_id = i * 4 + j
            G.add_node(node_id, x=i*100, y=j*100, osmid=node_id)
    
    # Add edges (roads)
    for i in range(4):
        for j in range(3):
            # Horizontal edges
            source = i * 4 + j
            target = i * 4 + j + 1
            G.add_edge(source, target, 
                      length=100, 
                      highway='primary',
                      lanes=2,
                      maxspeed=50,
                      osmid=f"way_{source}_{target}")
            
            # Vertical edges
            source = j * 4 + i
            target = (j + 1) * 4 + i
            G.add_edge(source, target,
                      length=100,
                      highway='primary', 
                      lanes=2,
                      maxspeed=50,
                      osmid=f"way_{source}_{target}")
    
    # Sample traffic metrics
    metrics = {
        'congestion': {
            'average_speeds': [15.2, 14.8, 13.5, 12.1, 11.8, 13.2, 14.5, 15.1],
            'densities': [25.3, 28.1, 32.4, 35.7, 38.2, 33.1, 29.8, 26.5],
            'flow_rates': [1200, 1150, 1080, 950, 890, 1020, 1180, 1220],
            'level_of_service': ['B', 'B', 'C', 'D', 'D', 'C', 'B', 'B'],
            'bottlenecks': [{'location': 'Node_5', 'severity': 0.7}]
        },
        'flow': {
            'total_vehicles': 45,
            'completed_trips': 38,
            'average_travel_time': 245.6,
            'throughput_history': [12, 15, 18, 22, 25, 23, 20, 17],
            'queue_lengths': [3, 5, 8, 12, 15, 11, 7, 4]
        },
        'safety': {
            'near_misses': 3,
            'conflicts': [
                {'type': 'rear_end', 'severity': 0.6, 'location': 'Node_8'},
                {'type': 'lane_change', 'severity': 0.4, 'location': 'Node_12'}
            ],
            'emergency_braking': 7,
            'critical_events': []
        },
        'environmental': {
            'fuel_consumption': 125.4,
            'emissions': {
                'co2': 45.2,
                'nox': 2.1,
                'pm': 0.8,
                'hc': 1.3
            },
            'noise_levels': [65.2, 67.1, 69.3, 71.5, 68.9, 66.7, 64.8, 63.2],
            'air_quality': {'aqi': 85, 'pm2_5': 35.2}
        }
    }
    
    return trajectories, G, metrics

def test_system_status():
    """Test system status and availability"""
    print("\n" + "="*50)
    print("TESTING SYSTEM STATUS")
    print("="*50)
    
    status = get_integration_status()
    
    print(f"MATLAB Available: {status['matlab_available']}")
    print(f"SciPy Available: {status['scipy_available']}")
    print(f"Version: {status['version']}")
    
    print("\nAvailable Components:")
    for component, available in status['components'].items():
        print(f"  {component}: {'✓' if available else '✗'}")
    
    if status['issues']:
        print("\nIssues found:")
        for issue in status['issues']:
            print(f"  - {issue}")
    
    return status

def test_data_export(trajectories, road_network, metrics):
    """Test MATLAB data export functionality"""
    print("\n" + "="*50)
    print("TESTING DATA EXPORT")
    print("="*50)
    
    try:
        # Initialize exporter
        config = MATLABConfig()
        exporter = MATLABDataExporter(config)
        
        print("Exporting vehicle trajectories...")
        trajectory_file = exporter.export_vehicle_trajectories(trajectories)
        print(f"  ✓ Exported to: {trajectory_file}")
        
        print("Exporting road network...")
        network_file = exporter.export_road_network(road_network)
        print(f"  ✓ Exported to: {network_file}")
        
        print("Exporting traffic metrics...")
        metrics_file = exporter.export_traffic_metrics(metrics)
        print(f"  ✓ Exported to: {metrics_file}")
        
        # Test workspace creation
        print("Creating MATLAB workspace...")
        simulation_results = {
            'trajectories': trajectories,
            'road_network': road_network,
            'metrics': metrics,
            'duration': 300,
            'vehicle_count': len(trajectories)
        }
        
        workspace_vars = exporter.create_matlab_workspace(simulation_results)
        print(f"  ✓ Created {len(workspace_vars)} workspace variables")
        
        return [trajectory_file, network_file, metrics_file]
        
    except Exception as e:
        print(f"  ✗ Export failed: {e}")
        return []

def test_script_generation(data_files):
    """Test MATLAB script generation"""
    print("\n" + "="*50)
    print("TESTING SCRIPT GENERATION")
    print("="*50)
    
    try:
        generator = MATLABScriptGenerator()
        
        # Test different analysis types
        analysis_types = ['comprehensive', 'congestion', 'safety', 'environmental']
        
        generated_scripts = []
        
        for analysis_type in analysis_types:
            print(f"Generating {analysis_type} analysis script...")
            script_file = generator.generate_traffic_analysis_script(data_files, analysis_type)
            generated_scripts.append(script_file)
            print(f"  ✓ Generated: {script_file}")
        
        # Test integration scripts
        print("Generating RoadRunner integration script...")
        rr_script = generator.generate_roadrunner_integration_script()
        generated_scripts.append(rr_script)
        print(f"  ✓ Generated: {rr_script}")
        
        print("Generating Simulink integration script...")
        sim_script = generator.generate_simulink_integration_script()
        generated_scripts.append(sim_script)
        print(f"  ✓ Generated: {sim_script}")
        
        # Test documentation generation
        print("Generating documentation...")
        user_guide = generator.generate_documentation()
        api_docs = generator.generate_api_documentation()
        print(f"  ✓ Generated user guide: {user_guide}")
        print(f"  ✓ Generated API docs: {api_docs}")
        
        return generated_scripts
        
    except Exception as e:
        print(f"  ✗ Script generation failed: {e}")
        return []

def test_roadrunner_import():
    """Test RoadRunner import functionality"""
    print("\n" + "="*50)
    print("TESTING ROADRUNNER IMPORT")
    print("="*50)
    
    try:
        # Create a sample RoadRunner scene file (JSON format for testing)
        sample_scene_data = {
            'road_network': {
                'nodes': [
                    {'id': 1, 'x': 0, 'y': 0, 'type': 'intersection'},
                    {'id': 2, 'x': 100, 'y': 0, 'type': 'intersection'},
                    {'id': 3, 'x': 100, 'y': 100, 'type': 'intersection'},
                    {'id': 4, 'x': 0, 'y': 100, 'type': 'intersection'}
                ],
                'edges': [
                    {'source': 1, 'target': 2, 'length': 100, 'lanes': 2, 'type': 'primary'},
                    {'source': 2, 'target': 3, 'length': 100, 'lanes': 2, 'type': 'primary'},
                    {'source': 3, 'target': 4, 'length': 100, 'lanes': 2, 'type': 'primary'},
                    {'source': 4, 'target': 1, 'length': 100, 'lanes': 2, 'type': 'primary'}
                ]
            },
            'vehicle_paths': [
                {
                    'vehicle_id': 1,
                    'vehicle_type': 'car',
                    'waypoints': [
                        {'x': 0, 'y': 0, 'timestamp': 0, 'speed': 15, 'heading': 0},
                        {'x': 50, 'y': 0, 'timestamp': 3.33, 'speed': 15, 'heading': 0},
                        {'x': 100, 'y': 0, 'timestamp': 6.67, 'speed': 15, 'heading': 0}
                    ]
                }
            ],
            'scenario_config': {
                'simulation_duration': 60.0,
                'time_step': 0.1,
                'weather': 'clear',
                'traffic_density': 'medium'
            },
            'metadata': {
                'coordinate_system': 'local',
                'version': '1.0'
            }
        }
        
        # Save sample scene file
        scene_file = 'test_scene.json'
        with open(scene_file, 'w') as f:
            json.dump(sample_scene_data, f, indent=2)
        
        print(f"Created sample scene file: {scene_file}")
        
        # Test import
        importer = RoadRunnerImporter()
        
        print("Importing scene file...")
        scene = importer.import_scene_file(scene_file)
        print(f"  ✓ Imported scene: {scene.scene_name}")
        
        print("Converting to OSMnx graph...")
        graph = importer.convert_to_osmnx_graph(scene)
        print(f"  ✓ Converted graph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
        
        print("Extracting vehicle paths...")
        vehicle_paths = importer.extract_vehicle_paths(scene)
        print(f"  ✓ Extracted {len(vehicle_paths)} vehicle paths")
        
        print("Validating scene compatibility...")
        is_valid, issues = importer.validate_scene_compatibility(scene)
        print(f"  ✓ Scene valid: {is_valid}")
        if issues:
            print(f"    Issues: {issues}")
        
        # Clean up
        os.remove(scene_file)
        
        return True
        
    except Exception as e:
        print(f"  ✗ RoadRunner import failed: {e}")
        return False

def test_simulink_connector():
    """Test Simulink connector (without actual connection)"""
    print("\n" + "="*50)
    print("TESTING SIMULINK CONNECTOR")
    print("="*50)
    
    try:
        connector = SimulinkConnector()
        
        print("Testing connector initialization...")
        print(f"  ✓ Connector initialized")
        
        print("Testing data preparation...")
        sample_data = {
            'vehicle_count': 25,
            'average_speed': 12.5,
            'congestion_level': 0.6,
            'simulation_time': 45.2
        }
        
        # Test data encoding/decoding
        if hasattr(connector, '_encode_binary_message'):
            encoded = connector._encode_binary_message(sample_data)
            decoded = connector._decode_binary_message(encoded)
            print(f"  ✓ Binary encoding/decoding works")
            print(f"    Original keys: {list(sample_data.keys())}")
            print(f"    Decoded keys: {list(decoded.keys())}")
        
        print("Testing connection statistics...")
        stats = connector.get_connection_statistics()
        print(f"  ✓ Statistics available: {list(stats.keys())}")
        
        print("Note: Actual Simulink connection requires running MATLAB/Simulink")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Simulink connector test failed: {e}")
        return False

def create_matlab_usage_guide(data_files, script_files):
    """Create a practical MATLAB usage guide"""
    guide_content = f"""% MATLAB Usage Guide for Indian Traffic Digital Twin
% Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

%% Quick Start Guide

% 1. LOAD EXPORTED DATA
% The following data files have been exported from your simulation:
"""
    
    for i, file_path in enumerate(data_files, 1):
        guide_content += f"""
% File {i}: {file_path}
data_{i} = load('{file_path}');
fprintf('Loaded {file_path}\\n');
"""
    
    guide_content += """

%% 2. BASIC DATA EXPLORATION

% Check what data is available
if exist('data_1', 'var')
    disp('Available fields in data_1:');
    disp(fieldnames(data_1));
end

% Display basic statistics
if exist('data_1', 'var') && isfield(data_1, 'vehicle_trajectories')
    traj = data_1.vehicle_trajectories;
    fprintf('Number of vehicles: %d\\n', length(traj.vehicle_ids));
    fprintf('Simulation metadata: %s\\n', traj.metadata.coordinate_system);
end

%% 3. VISUALIZATION EXAMPLES

% Plot vehicle trajectories
if exist('data_1', 'var') && isfield(data_1, 'vehicle_trajectories')
    figure('Name', 'Vehicle Trajectories');
    hold on;
    
    traj = data_1.vehicle_trajectories;
    colors = lines(length(traj.vehicle_ids));
    
    for i = 1:length(traj.vehicle_ids)
        if iscell(traj.positions)
            pos = traj.positions{i};
        else
            pos = traj.positions(i,:);
        end
        
        if size(pos, 1) > 1
            plot(pos(:,1), pos(:,2), 'Color', colors(i,:), 'LineWidth', 1.5);
        end
    end
    
    xlabel('X Coordinate (m)');
    ylabel('Y Coordinate (m)');
    title('Vehicle Movement Patterns');
    grid on;
    axis equal;
end

% Plot road network
if exist('data_2', 'var') && isfield(data_2, 'road_network')
    figure('Name', 'Road Network');
    
    network = data_2.road_network;
    
    % Plot edges
    hold on;
    for i = 1:length(network.edges.source_nodes)
        source_id = network.edges.source_nodes(i);
        target_id = network.edges.target_nodes(i);
        
        % Find node coordinates
        source_idx = find(network.nodes.ids == source_id);
        target_idx = find(network.nodes.ids == target_id);
        
        if ~isempty(source_idx) && ~isempty(target_idx)
            source_pos = network.nodes.coordinates(source_idx, :);
            target_pos = network.nodes.coordinates(target_idx, :);
            
            plot([source_pos(1), target_pos(1)], ...
                 [source_pos(2), target_pos(2)], 'b-', 'LineWidth', 2);
        end
    end
    
    % Plot nodes
    scatter(network.nodes.coordinates(:,1), ...
            network.nodes.coordinates(:,2), ...
            100, 'ro', 'filled');
    
    xlabel('X Coordinate (m)');
    ylabel('Y Coordinate (m)');
    title('Road Network Structure');
    grid on;
    axis equal;
end

% Plot traffic metrics
if exist('data_3', 'var') && isfield(data_3, 'traffic_metrics')
    metrics = data_3.traffic_metrics;
    
    if isfield(metrics, 'congestion_metrics')
        figure('Name', 'Traffic Metrics');
        
        congestion = metrics.congestion_metrics;
        
        subplot(2,2,1);
        plot(congestion.average_speeds);
        title('Average Speed Over Time');
        xlabel('Time Step');
        ylabel('Speed (m/s)');
        grid on;
        
        subplot(2,2,2);
        plot(congestion.densities);
        title('Traffic Density');
        xlabel('Time Step');
        ylabel('Density (vehicles/km)');
        grid on;
        
        subplot(2,2,3);
        plot(congestion.flow_rates);
        title('Flow Rate');
        xlabel('Time Step');
        ylabel('Flow (vehicles/hour)');
        grid on;
        
        subplot(2,2,4);
        if isfield(congestion, 'level_of_service')
            los_counts = countcats(categorical(congestion.level_of_service));
            bar(categorical({'A', 'B', 'C', 'D', 'E', 'F'}), los_counts);
            title('Level of Service Distribution');
            ylabel('Count');
            grid on;
        end
    end
end

%% 4. ANALYSIS FUNCTIONS

% Calculate basic statistics
function stats = calculate_trajectory_stats(trajectories)
    stats = struct();
    
    if iscell(trajectories.positions)
        num_vehicles = length(trajectories.positions);
        total_distance = 0;
        
        for i = 1:num_vehicles
            pos = trajectories.positions{i};
            if size(pos, 1) > 1
                distances = sqrt(sum(diff(pos).^2, 2));
                total_distance = total_distance + sum(distances);
            end
        end
        
        stats.num_vehicles = num_vehicles;
        stats.avg_distance = total_distance / num_vehicles;
    end
end

% Network analysis
function analyze_network(network)
    fprintf('\\nNetwork Analysis:\\n');
    fprintf('  Nodes: %d\\n', length(network.nodes.ids));
    fprintf('  Edges: %d\\n', length(network.edges.source_nodes));
    fprintf('  Total length: %.2f km\\n', sum(network.edges.lengths)/1000);
    fprintf('  Average edge length: %.2f m\\n', mean(network.edges.lengths));
end

%% 5. EXPORT RESULTS

% Save analysis results
results = struct();
results.analysis_date = datestr(now);
results.data_files = {"""
    
    for file_path in data_files:
        guide_content += f"'{file_path}', "
    
    guide_content += """};

% Add your analysis results here
% results.trajectory_stats = calculate_trajectory_stats(data_1.vehicle_trajectories);

% Save results
save('indian_traffic_analysis_results.mat', 'results');
fprintf('Analysis results saved to indian_traffic_analysis_results.mat\\n');

%% 6. NEXT STEPS

fprintf('\\n=== Next Steps ===\\n');
fprintf('1. Run the generated analysis scripts:\\n');
"""
    
    for script_file in script_files:
        if script_file.endswith('.m'):
            guide_content += f"fprintf('   run(''{script_file}'')\\n');\n"
    
    guide_content += """
fprintf('2. Customize the analysis for your specific needs\\n');
fprintf('3. Integrate with other MATLAB toolboxes as needed\\n');
fprintf('4. Set up real-time Simulink integration if required\\n');

fprintf('\\nFor more information, see the generated documentation files.\\n');
"""
    
    # Save the guide
    guide_file = 'matlab_usage_guide.m'
    with open(guide_file, 'w') as f:
        f.write(guide_content)
    
    return guide_file

def main():
    """Main test function"""
    print("MATLAB Integration Test Suite")
    print("=" * 60)
    
    # Test system status
    status = test_system_status()
    
    # Create sample data
    trajectories, road_network, metrics = create_sample_data()
    print(f"\n✓ Created sample data: {len(trajectories)} vehicles, {road_network.number_of_nodes()} nodes")
    
    # Test data export
    data_files = test_data_export(trajectories, road_network, metrics)
    
    # Test script generation
    script_files = test_script_generation(data_files)
    
    # Test RoadRunner import
    test_roadrunner_import()
    
    # Test Simulink connector
    test_simulink_connector()
    
    # Create MATLAB usage guide
    if data_files:
        guide_file = create_matlab_usage_guide(data_files, script_files)
        print(f"\n✓ Created MATLAB usage guide: {guide_file}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if data_files:
        print("✓ Data export: PASSED")
        print(f"  Exported files: {len(data_files)}")
        for file in data_files:
            print(f"    - {file}")
    else:
        print("✗ Data export: FAILED")
    
    if script_files:
        print("✓ Script generation: PASSED")
        print(f"  Generated scripts: {len(script_files)}")
    else:
        print("✗ Script generation: FAILED")
    
    print("\nTo use with MATLAB:")
    print("1. Open MATLAB")
    print("2. Navigate to this directory")
    print("3. Run: matlab_usage_guide")
    print("4. Or run any of the generated analysis scripts")
    
    if not status['scipy_available']:
        print("\nNote: Install scipy for .mat file support:")
        print("  pip install scipy")

if __name__ == "__main__":
    main()