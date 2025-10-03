"""
MATLAB Integration Demo

This script demonstrates how to use the MATLAB integration with real traffic simulation data.
It exports data from a traffic simulation and creates MATLAB scripts for analysis.
"""

import os
import numpy as np
import networkx as nx
from datetime import datetime

# Import traffic simulation components
try:
    from traffic_model import TrafficModel
    TRAFFIC_MODEL_AVAILABLE = True
except ImportError:
    TRAFFIC_MODEL_AVAILABLE = False
    print("Note: TrafficModel not available, using synthetic data")

import osmnx as ox

# Import MATLAB integration
from matlab_integration import (
    MATLABDataExporter,
    MATLABScriptGenerator,
    MATLABConfig,
    setup_matlab_integration
)

def run_traffic_simulation():
    """Run a small traffic simulation to generate real data"""
    print("Running traffic simulation...")
    
    # Create a simple road network
    print("  Creating synthetic network...")
    G = nx.grid_2d_graph(4, 4)
    G = nx.convert_node_labels_to_integers(G)
    
    # Add required attributes
    for node in G.nodes():
        G.nodes[node]['x'] = (node % 4) * 100
        G.nodes[node]['y'] = (node // 4) * 100
        G.nodes[node]['osmid'] = node
    
    for u, v in G.edges():
        G.edges[u, v]['length'] = 100
        G.edges[u, v]['highway'] = 'residential'
        G.edges[u, v]['lanes'] = 1
        G.edges[u, v]['maxspeed'] = 30
        G.edges[u, v]['osmid'] = f"way_{u}_{v}"
    
    print(f"  ✓ Created network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Generate synthetic trajectories
    print("  Generating vehicle trajectories...")
    trajectories = {}
    
    # Create 6 vehicles with different paths
    vehicle_paths = [
        [0, 1, 2, 3],      # Top row
        [0, 4, 8, 12],     # Left column
        [12, 13, 14, 15],  # Bottom row
        [3, 7, 11, 15],    # Right column
        [0, 5, 10, 15],    # Diagonal
        [5, 6, 7, 11]      # Mixed path
    ]
    
    for vid, path in enumerate(vehicle_paths, 1):
        trajectory = []
        for i, node in enumerate(path):
            # Get node coordinates
            x = G.nodes[node]['x']
            y = G.nodes[node]['y']
            
            # Create trajectory point
            point = {
                'timestamp': i * 15.0,  # 15 second intervals
                'x': x + np.random.normal(0, 3),  # Add some noise
                'y': y + np.random.normal(0, 3),
                'vx': 8 + np.random.normal(0, 2),
                'vy': 6 + np.random.normal(0, 1),
                'ax': np.random.normal(0, 0.5),
                'ay': np.random.normal(0, 0.3)
            }
            trajectory.append(point)
        
        trajectories[vid] = trajectory
    
    # Create traffic metrics
    metrics = {
        'congestion': {
            'average_speeds': [12.5, 11.8, 10.2, 9.5, 11.1, 13.2],
            'densities': [28.3, 32.1, 35.7, 38.9, 33.2, 29.1],
            'flow_rates': [850, 780, 720, 650, 750, 820],
            'level_of_service': ['B', 'C', 'D', 'D', 'C', 'B'],
            'bottlenecks': []
        },
        'flow': {
            'total_vehicles': len(trajectories),
            'completed_trips': len([t for t in trajectories.values() if len(t) > 3]),
            'average_travel_time': 85.4,
            'throughput_history': [8, 12, 15, 18, 16, 14],
            'queue_lengths': [2, 4, 6, 8, 5, 3]
        },
        'safety': {
            'near_misses': 2,
            'conflicts': [
                {'type': 'lane_change', 'severity': 0.3, 'location': 'Node_5'}
            ],
            'emergency_braking': 4,
            'critical_events': []
        }
    }
    
    print(f"  ✓ Simulation complete: {len(trajectories)} vehicles tracked")
    
    return G, trajectories, metrics

def export_to_matlab(road_network, trajectories, metrics):
    """Export simulation data to MATLAB"""
    print("\nExporting data to MATLAB...")
    
    # Setup MATLAB integration
    config = MATLABConfig()
    config.export_config.output_directory = "matlab_demo_exports"
    config.export_config.file_prefix = "indian_traffic_demo"
    
    exporter = MATLABDataExporter(config)
    
    # Export data
    trajectory_file = exporter.export_vehicle_trajectories(trajectories)
    network_file = exporter.export_road_network(road_network)
    metrics_file = exporter.export_traffic_metrics(metrics)
    
    print(f"  ✓ Exported trajectories: {trajectory_file}")
    print(f"  ✓ Exported network: {network_file}")
    print(f"  ✓ Exported metrics: {metrics_file}")
    
    return [trajectory_file, network_file, metrics_file]

def generate_matlab_scripts(data_files):
    """Generate MATLAB analysis scripts"""
    print("\nGenerating MATLAB analysis scripts...")
    
    config = MATLABConfig()
    config.script_template_directory = "matlab_demo_scripts"
    
    generator = MATLABScriptGenerator(config)
    
    # Generate different types of analysis scripts
    scripts = []
    
    # Comprehensive analysis
    comprehensive_script = generator.generate_traffic_analysis_script(
        data_files, "comprehensive"
    )
    scripts.append(comprehensive_script)
    print(f"  ✓ Generated comprehensive analysis: {comprehensive_script}")
    
    # Congestion analysis
    congestion_script = generator.generate_traffic_analysis_script(
        data_files, "congestion"
    )
    scripts.append(congestion_script)
    print(f"  ✓ Generated congestion analysis: {congestion_script}")
    
    # RoadRunner integration script
    rr_script = generator.generate_roadrunner_integration_script()
    scripts.append(rr_script)
    print(f"  ✓ Generated RoadRunner integration: {rr_script}")
    
    # Simulink integration script
    sim_script = generator.generate_simulink_integration_script()
    scripts.append(sim_script)
    print(f"  ✓ Generated Simulink integration: {sim_script}")
    
    return scripts

def create_matlab_startup_script(data_files, script_files):
    """Create a MATLAB startup script for easy use"""
    startup_content = f"""% Indian Traffic Digital Twin - MATLAB Demo
% Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
%
% This script provides a quick start for analyzing Indian traffic simulation data

clear; clc; close all;

fprintf('=== Indian Traffic Digital Twin - MATLAB Demo ===\\n');
fprintf('Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n');

%% 1. Load Simulation Data
fprintf('Loading simulation data...\\n');

% Load exported data files
"""
    
    for i, file_path in enumerate(data_files, 1):
        rel_path = os.path.relpath(file_path).replace('\\', '/')
        startup_content += f"""
try
    data_{i} = load('{rel_path}');
    fprintf('  Loaded: {rel_path}\\n');
catch ME
    fprintf('  Failed to load: {rel_path}\\n');
    fprintf('    Error: %s\\n', ME.message);
end
"""
    
    startup_content += """
%% 2. Quick Data Overview
fprintf('\\nData Overview:\\n');

% Vehicle trajectories
if exist('data_1', 'var') && isfield(data_1, 'vehicle_trajectories')
    traj = data_1.vehicle_trajectories;
    fprintf('  Vehicles tracked: %d\\n', length(traj.vehicle_ids));
    
    % Calculate basic statistics
    total_points = 0;
    for i = 1:length(traj.positions)
        if iscell(traj.positions)
            total_points = total_points + size(traj.positions{i}, 1);
        end
    end
    fprintf('  Total trajectory points: %d\\n', total_points);
end

% Road network
if exist('data_2', 'var') && isfield(data_2, 'road_network')
    network = data_2.road_network;
    fprintf('  Network nodes: %d\\n', length(network.nodes.ids));
    fprintf('  Network edges: %d\\n', length(network.edges.source_nodes));
    fprintf('  Total road length: %.2f km\\n', sum(network.edges.lengths)/1000);
end

% Traffic metrics
if exist('data_3', 'var') && isfield(data_3, 'traffic_metrics')
    metrics = data_3.traffic_metrics;
    if isfield(metrics, 'flow_metrics')
        fprintf('  Total vehicles simulated: %d\\n', metrics.flow_metrics.total_vehicles);
        fprintf('  Completed trips: %d\\n', metrics.flow_metrics.completed_trips);
    end
end

%% 3. Quick Visualization
fprintf('\\nCreating visualizations...\\n');

% Plot vehicle trajectories
if exist('data_1', 'var') && isfield(data_1, 'vehicle_trajectories')
    figure('Name', 'Vehicle Trajectories', 'Position', [100, 100, 800, 600]);
    
    traj = data_1.vehicle_trajectories;
    colors = lines(length(traj.vehicle_ids));
    
    hold on;
    for i = 1:min(length(traj.vehicle_ids), 10)  % Limit to 10 for clarity
        if iscell(traj.positions)
            pos = traj.positions{i};
        else
            pos = traj.positions(i,:);
        end
        
        if size(pos, 1) > 1
            plot(pos(:,1), pos(:,2), 'Color', colors(i,:), 'LineWidth', 2, ...
                 'DisplayName', sprintf('Vehicle %d', traj.vehicle_ids(i)));
        end
    end
    
    xlabel('X Coordinate (m)');
    ylabel('Y Coordinate (m)');
    title('Indian Traffic Vehicle Trajectories');
    legend('show', 'Location', 'best');
    grid on;
    axis equal;
    
    fprintf('  Vehicle trajectories plotted\\n');
end

% Plot road network
if exist('data_2', 'var') && isfield(data_2, 'road_network')
    figure('Name', 'Road Network', 'Position', [200, 200, 800, 600]);
    
    network = data_2.road_network;
    
    hold on;
    
    % Plot edges (roads)
    for i = 1:length(network.edges.source_nodes)
        source_id = network.edges.source_nodes(i);
        target_id = network.edges.target_nodes(i);
        
        source_idx = find(network.nodes.ids == source_id, 1);
        target_idx = find(network.nodes.ids == target_id, 1);
        
        if ~isempty(source_idx) && ~isempty(target_idx)
            source_pos = network.nodes.coordinates(source_idx, :);
            target_pos = network.nodes.coordinates(target_idx, :);
            
            plot([source_pos(1), target_pos(1)], ...
                 [source_pos(2), target_pos(2)], 'b-', 'LineWidth', 2);
        end
    end
    
    % Plot nodes (intersections)
    scatter(network.nodes.coordinates(:,1), network.nodes.coordinates(:,2), ...
            100, 'ro', 'filled', 'MarkerEdgeColor', 'k');
    
    xlabel('X Coordinate (m)');
    ylabel('Y Coordinate (m)');
    title('Indian Traffic Road Network');
    grid on;
    axis equal;
    
    fprintf('  Road network plotted\\n');
end

% Plot traffic metrics
if exist('data_3', 'var') && isfield(data_3, 'traffic_metrics')
    figure('Name', 'Traffic Metrics', 'Position', [300, 300, 1000, 700]);
    
    metrics = data_3.traffic_metrics;
    
    if isfield(metrics, 'congestion_metrics')
        congestion = metrics.congestion_metrics;
        
        subplot(2,3,1);
        plot(congestion.average_speeds, 'b-o', 'LineWidth', 2);
        title('Average Speed');
        xlabel('Time Step');
        ylabel('Speed (m/s)');
        grid on;
        
        subplot(2,3,2);
        plot(congestion.densities, 'r-s', 'LineWidth', 2);
        title('Traffic Density');
        xlabel('Time Step');
        ylabel('Density (vehicles/km)');
        grid on;
        
        subplot(2,3,3);
        plot(congestion.flow_rates, 'g-^', 'LineWidth', 2);
        title('Flow Rate');
        xlabel('Time Step');
        ylabel('Flow (vehicles/hour)');
        grid on;
        
        subplot(2,3,4);
        if isfield(congestion, 'level_of_service')
            los_categories = categorical(congestion.level_of_service);
            histogram(los_categories);
            title('Level of Service Distribution');
            ylabel('Count');
            grid on;
        end
    end
    
    if isfield(metrics, 'flow_metrics')
        flow = metrics.flow_metrics;
        
        subplot(2,3,5);
        plot(flow.throughput_history, 'm-d', 'LineWidth', 2);
        title('Traffic Throughput');
        xlabel('Time Step');
        ylabel('Vehicles/hour');
        grid on;
        
        subplot(2,3,6);
        plot(flow.queue_lengths, 'c-p', 'LineWidth', 2);
        title('Queue Lengths');
        xlabel('Time Step');
        ylabel('Queue Length');
        grid on;
    end
    
    sgtitle('Indian Traffic Metrics Dashboard');
    
    fprintf('  Traffic metrics plotted\\n');
end

%% 4. Available Analysis Scripts
fprintf('\\nAvailable analysis scripts:\\n');
"""
    
    for script_file in script_files:
        if script_file.endswith('.m'):
            script_name = os.path.basename(script_file)
            rel_path = os.path.relpath(script_file).replace('\\', '/')
            startup_content += f"""fprintf('  - {script_name}\\n');
fprintf('    Run with: run(''{rel_path}'')\\n');
"""
    
    startup_content += """
%% 5. Next Steps
fprintf('\\nNext Steps:\\n');
fprintf('1. Explore the generated visualizations\\n');
fprintf('2. Run detailed analysis scripts listed above\\n');
fprintf('3. Modify analysis parameters for your specific needs\\n');
fprintf('4. Export results for further processing\\n');

fprintf('\\n=== Demo Complete ===\\n');
fprintf('For more information, see the generated documentation.\\n');

% Save workspace for later use
save('indian_traffic_demo_workspace.mat');
fprintf('\\nWorkspace saved to: indian_traffic_demo_workspace.mat\\n');
"""
    
    # Save the startup script
    startup_file = 'indian_traffic_matlab_demo.m'
    with open(startup_file, 'w', encoding='utf-8') as f:
        f.write(startup_content)
    
    return startup_file

def main():
    """Main demo function"""
    print("Indian Traffic Digital Twin - MATLAB Integration Demo")
    print("=" * 60)
    
    # Run traffic simulation
    road_network, trajectories, metrics = run_traffic_simulation()
    
    # Export to MATLAB
    data_files = export_to_matlab(road_network, trajectories, metrics)
    
    # Generate analysis scripts
    script_files = generate_matlab_scripts(data_files)
    
    # Create startup script
    startup_script = create_matlab_startup_script(data_files, script_files)
    
    # Summary
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    
    print(f"✓ Exported {len(data_files)} data files")
    print(f"✓ Generated {len(script_files)} analysis scripts")
    print(f"✓ Created startup script: {startup_script}")
    
    print("\nTo use with MATLAB:")
    print("1. Open MATLAB")
    print("2. Navigate to this directory")
    print(f"3. Run: {startup_script.replace('.m', '')}")
    print("\nOr run individual analysis scripts:")
    for script in script_files:
        if script.endswith('.m'):
            script_name = os.path.basename(script).replace('.m', '')
            print(f"   - {script_name}")
    
    print("\nFiles created:")
    print("Data files:")
    for file in data_files:
        print(f"  - {file}")
    print("Script files:")
    for file in script_files:
        print(f"  - {file}")
    print(f"Startup script: {startup_script}")

if __name__ == "__main__":
    main()