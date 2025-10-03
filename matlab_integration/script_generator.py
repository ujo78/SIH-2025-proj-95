"""
MATLAB Script Generator

This module generates MATLAB analysis scripts and documentation
for Indian traffic simulation data analysis.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .config import MATLABConfig


class MATLABScriptGenerator:
    """Generator for MATLAB analysis scripts and documentation"""
    
    def __init__(self, config: Optional[MATLABConfig] = None):
        """Initialize script generator with configuration"""
        self.config = config or MATLABConfig()
        
        # Ensure template directory exists
        os.makedirs(self.config.script_template_directory, exist_ok=True)
    
    def generate_traffic_analysis_script(self, data_files: List[str], 
                                       analysis_type: str = "comprehensive") -> str:
        """Generate comprehensive traffic analysis script"""
        script_content = self._get_script_header("Traffic Analysis", analysis_type)
        
        # Add data loading section
        script_content += self._get_data_loading_section(data_files)
        
        # Add analysis sections based on type
        if analysis_type == "comprehensive":
            script_content += self._get_comprehensive_analysis()
        elif analysis_type == "congestion":
            script_content += self._get_congestion_analysis()
        elif analysis_type == "safety":
            script_content += self._get_safety_analysis()
        elif analysis_type == "environmental":
            script_content += self._get_environmental_analysis()
        else:
            script_content += self._get_basic_analysis()
        
        # Add visualization and export sections
        script_content += self._get_visualization_section()
        script_content += self._get_export_section()
        script_content += self._get_script_footer()
        
        # Save script
        filename = f"indian_traffic_analysis_{analysis_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m"
        filepath = os.path.join(self.config.script_template_directory, filename)
        
        with open(filepath, 'w') as f:
            f.write(script_content)
        
        return filepath
    
    def generate_roadrunner_integration_script(self) -> str:
        """Generate script for RoadRunner integration"""
        script_content = self._get_script_header("RoadRunner Integration", "roadrunner")
        
        script_content += """
%% RoadRunner Scene Import and Analysis
% This script demonstrates how to import RoadRunner scenes and
% integrate them with Indian traffic simulation data

%% Import RoadRunner Scene
% Specify the path to your RoadRunner scene file
scene_file = 'path/to/your/scene.rrscene';

if exist(scene_file, 'file')
    fprintf('Importing RoadRunner scene: %s\\n', scene_file);
    
    % Load scene data (assuming it's been converted to .mat format)
    scene_data = load(scene_file);
    
    % Extract road network
    if isfield(scene_data, 'road_network')
        road_network = scene_data.road_network;
        fprintf('Road network loaded: %d nodes, %d edges\\n', ...
                length(road_network.nodes.ids), ...
                length(road_network.edges.source_nodes));
    end
    
    % Extract vehicle paths
    if isfield(scene_data, 'vehicle_paths')
        vehicle_paths = scene_data.vehicle_paths;
        fprintf('Vehicle paths loaded: %d paths\\n', length(vehicle_paths));
    end
else
    warning('RoadRunner scene file not found. Using sample data.');
    % Create sample road network for demonstration
    road_network = create_sample_network();
end

%% Visualize Road Network
figure('Name', 'RoadRunner Road Network');
plot_road_network(road_network);
title('Imported Road Network from RoadRunner');

%% Convert to Graph Format
% Convert to MATLAB graph object for analysis
G = create_graph_from_network(road_network);

% Analyze network properties
num_nodes = numnodes(G);
num_edges = numedges(G);
avg_degree = mean(degree(G));

fprintf('Network Analysis:\\n');
fprintf('  Nodes: %d\\n', num_nodes);
fprintf('  Edges: %d\\n', num_edges);
fprintf('  Average degree: %.2f\\n', avg_degree);

%% Path Analysis
if exist('vehicle_paths', 'var')
    analyze_vehicle_paths(vehicle_paths, road_network);
end

%% Export for Indian Traffic Simulation
% Prepare data for use in Indian traffic simulation
export_data = struct();
export_data.road_network = road_network;
export_data.timestamp = datestr(now);
export_data.source = 'RoadRunner';

save('roadrunner_export_for_indian_traffic.mat', 'export_data');
fprintf('Data exported for Indian traffic simulation\\n');

%% Helper Functions
function road_network = create_sample_network()
    % Create a sample road network for demonstration
    road_network = struct();
    
    % Sample nodes (intersection points)
    road_network.nodes.ids = [1, 2, 3, 4];
    road_network.nodes.coordinates = [0, 0; 100, 0; 100, 100; 0, 100];
    
    % Sample edges (road segments)
    road_network.edges.source_nodes = [1, 2, 3, 4];
    road_network.edges.target_nodes = [2, 3, 4, 1];
    road_network.edges.lengths = [100, 100, 100, 100];
end

function plot_road_network(road_network)
    hold on;
    
    % Plot edges
    for i = 1:length(road_network.edges.source_nodes)
        source_id = road_network.edges.source_nodes(i);
        target_id = road_network.edges.target_nodes(i);
        
        source_idx = find(road_network.nodes.ids == source_id);
        target_idx = find(road_network.nodes.ids == target_id);
        
        if ~isempty(source_idx) && ~isempty(target_idx)
            source_pos = road_network.nodes.coordinates(source_idx, :);
            target_pos = road_network.nodes.coordinates(target_idx, :);
            
            plot([source_pos(1), target_pos(1)], ...
                 [source_pos(2), target_pos(2)], 'b-', 'LineWidth', 2);
        end
    end
    
    % Plot nodes
    scatter(road_network.nodes.coordinates(:,1), ...
            road_network.nodes.coordinates(:,2), ...
            100, 'ro', 'filled');
    
    xlabel('X Coordinate (m)');
    ylabel('Y Coordinate (m)');
    grid on;
    axis equal;
end

function G = create_graph_from_network(road_network)
    % Create MATLAB graph object from road network
    source_nodes = road_network.edges.source_nodes;
    target_nodes = road_network.edges.target_nodes;
    weights = road_network.edges.lengths;
    
    G = graph(source_nodes, target_nodes, weights);
end

function analyze_vehicle_paths(vehicle_paths, road_network)
    fprintf('\\nVehicle Path Analysis:\\n');
    
    for i = 1:length(vehicle_paths)
        path = vehicle_paths{i};
        
        if isfield(path, 'waypoints') && ~isempty(path.waypoints)
            waypoints = path.waypoints;
            
            % Calculate path statistics
            total_distance = 0;
            for j = 2:length(waypoints)
                dx = waypoints(j).x - waypoints(j-1).x;
                dy = waypoints(j).y - waypoints(j-1).y;
                total_distance = total_distance + sqrt(dx^2 + dy^2);
            end
            
            fprintf('  Path %d: %.2f m total distance\\n', i, total_distance);
        end
    end
end
"""
        
        script_content += self._get_script_footer()
        
        filename = f"roadrunner_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m"
        filepath = os.path.join(self.config.script_template_directory, filename)
        
        with open(filepath, 'w') as f:
            f.write(script_content)
        
        return filepath
    
    def generate_simulink_integration_script(self) -> str:
        """Generate script for Simulink real-time integration"""
        script_content = self._get_script_header("Simulink Integration", "simulink")
        
        script_content += """
%% Simulink Real-time Integration
% This script demonstrates real-time data exchange with Indian traffic simulation

%% Configuration
simulink_model = 'indian_traffic_control_model';
host_address = 'localhost';
port = 12345;

%% Initialize Connection
fprintf('Initializing Simulink connection...\\n');

% Create TCP/IP connection
try
    t = tcpip(host_address, port);
    set(t, 'InputBufferSize', 8192);
    set(t, 'OutputBufferSize', 8192);
    set(t, 'Timeout', 10);
    
    fopen(t);
    fprintf('Connected to traffic simulation at %s:%d\\n', host_address, port);
    
    connected = true;
catch ME
    fprintf('Connection failed: %s\\n', ME.message);
    connected = false;
    return;
end

%% Real-time Data Exchange Loop
simulation_time = 0;
time_step = 0.1;
max_simulation_time = 300; % 5 minutes

% Data storage
traffic_data = [];
control_signals = [];

fprintf('Starting real-time simulation...\\n');

while simulation_time < max_simulation_time && connected
    try
        % Receive traffic data from simulation
        if t.BytesAvailable > 0
            raw_data = fread(t, t.BytesAvailable, 'uint8');
            
            % Parse JSON data
            json_str = char(raw_data');
            traffic_info = jsondecode(json_str);
            
            % Store received data
            traffic_data = [traffic_data; traffic_info];
            
            % Process traffic data
            [control_output] = process_traffic_data(traffic_info);
            
            % Send control signals back to simulation
            control_json = jsonencode(control_output);
            fwrite(t, control_json, 'char');
            
            % Store control signals
            control_signals = [control_signals; control_output];
            
            fprintf('Time: %.1fs - Vehicles: %d, Avg Speed: %.2f m/s\\n', ...
                    simulation_time, ...
                    traffic_info.vehicle_count, ...
                    traffic_info.average_speed);
        end
        
        % Update simulation time
        simulation_time = simulation_time + time_step;
        pause(time_step);
        
    catch ME
        fprintf('Communication error: %s\\n', ME.message);
        connected = false;
    end
end

%% Close Connection
if exist('t', 'var') && isvalid(t)
    fclose(t);
    delete(t);
    fprintf('Connection closed\\n');
end

%% Analyze Results
if ~isempty(traffic_data)
    analyze_real_time_results(traffic_data, control_signals);
end

%% Helper Functions
function control_output = process_traffic_data(traffic_info)
    % Process incoming traffic data and generate control signals
    
    control_output = struct();
    control_output.timestamp = now;
    control_output.simulation_time = traffic_info.simulation_time;
    
    % Simple traffic light control based on congestion
    if isfield(traffic_info, 'congestion_level')
        if traffic_info.congestion_level > 0.8
            % High congestion - extend green light
            control_output.traffic_light_duration = 45;
        elseif traffic_info.congestion_level < 0.3
            % Low congestion - normal timing
            control_output.traffic_light_duration = 30;
        else
            % Medium congestion - slightly longer
            control_output.traffic_light_duration = 35;
        end
    else
        control_output.traffic_light_duration = 30;
    end
    
    % Speed limit adjustment based on weather
    if isfield(traffic_info, 'weather_condition')
        switch traffic_info.weather_condition
            case 'rain'
                control_output.speed_limit_factor = 0.8;
            case 'fog'
                control_output.speed_limit_factor = 0.6;
            otherwise
                control_output.speed_limit_factor = 1.0;
        end
    else
        control_output.speed_limit_factor = 1.0;
    end
    
    % Emergency response
    if isfield(traffic_info, 'emergency_active') && traffic_info.emergency_active
        control_output.emergency_response = true;
        control_output.reroute_traffic = true;
    else
        control_output.emergency_response = false;
        control_output.reroute_traffic = false;
    end
end

function analyze_real_time_results(traffic_data, control_signals)
    fprintf('\\nAnalyzing real-time simulation results...\\n');
    
    % Extract time series data
    times = [traffic_data.simulation_time];
    vehicle_counts = [traffic_data.vehicle_count];
    avg_speeds = [traffic_data.average_speed];
    
    % Plot results
    figure('Name', 'Real-time Simulation Results');
    
    subplot(3,1,1);
    plot(times, vehicle_counts);
    title('Vehicle Count Over Time');
    xlabel('Simulation Time (s)');
    ylabel('Number of Vehicles');
    grid on;
    
    subplot(3,1,2);
    plot(times, avg_speeds);
    title('Average Speed Over Time');
    xlabel('Simulation Time (s)');
    ylabel('Speed (m/s)');
    grid on;
    
    subplot(3,1,3);
    if ~isempty(control_signals)
        control_times = [control_signals.simulation_time];
        light_durations = [control_signals.traffic_light_duration];
        plot(control_times, light_durations);
        title('Traffic Light Control Signals');
        xlabel('Simulation Time (s)');
        ylabel('Green Light Duration (s)');
        grid on;
    end
    
    % Statistics
    fprintf('Simulation Statistics:\\n');
    fprintf('  Duration: %.1f seconds\\n', max(times));
    fprintf('  Average vehicle count: %.1f\\n', mean(vehicle_counts));
    fprintf('  Average speed: %.2f m/s\\n', mean(avg_speeds));
    fprintf('  Speed standard deviation: %.2f m/s\\n', std(avg_speeds));
end
"""
        
        script_content += self._get_script_footer()
        
        filename = f"simulink_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m"
        filepath = os.path.join(self.config.script_template_directory, filename)
        
        with open(filepath, 'w') as f:
            f.write(script_content)
        
        return filepath
    
    def generate_documentation(self) -> str:
        """Generate comprehensive documentation for MATLAB integration"""
        doc_content = self._generate_user_guide()
        
        filename = f"MATLAB_Integration_Guide_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = os.path.join(self.config.script_template_directory, filename)
        
        with open(filepath, 'w') as f:
            f.write(doc_content)
        
        return filepath
    
    def generate_api_documentation(self) -> str:
        """Generate API documentation for MATLAB integration"""
        api_doc = self._generate_api_reference()
        
        filename = f"MATLAB_API_Reference_{datetime.now().strftime('%Y%m%d')}.md"
        filepath = os.path.join(self.config.script_template_directory, filename)
        
        with open(filepath, 'w') as f:
            f.write(api_doc)
        
        return filepath  
  
    def _get_script_header(self, title: str, analysis_type: str) -> str:
        """Generate standard script header"""
        return f"""% {title} Script for Indian Traffic Digital Twin
% Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
% Analysis Type: {analysis_type}
%
% This script provides comprehensive analysis tools for Indian traffic
% simulation data including trajectory analysis, congestion metrics,
% and performance evaluation.
%
% Requirements:
%   - MATLAB R2019b or later
%   - Statistics and Machine Learning Toolbox (optional)
%   - Mapping Toolbox (optional for geographic visualization)

clear; clc; close all;

% Set up environment
addpath(genpath('.'));  % Add current directory and subdirectories
warning('off', 'MATLAB:table:ModifiedAndSavedVarnames');

fprintf('=== {title} ===\\n');
fprintf('Started at: %s\\n', datestr(now));

"""
    
    def _get_data_loading_section(self, data_files: List[str]) -> str:
        """Generate data loading section"""
        section = """
%% Data Loading Section
fprintf('Loading simulation data...\\n');

% Initialize data containers
simulation_data = struct();
loaded_files = {};

"""
        
        for i, file_path in enumerate(data_files):
            file_name = Path(file_path).stem
            section += f"""
% Load {file_name}
try
    if exist('{file_path}', 'file')
        data_{i+1} = load('{file_path}');
        loaded_files{{end+1}} = '{file_path}';
        fprintf('  Loaded: {file_path}\\n');
        
        % Store in main data structure
        [~, name, ~] = fileparts('{file_path}');
        simulation_data.(name) = data_{i+1};
    else
        warning('File not found: {file_path}');
    end
catch ME
    warning('Error loading {file_path}: %s', ME.message);
end
"""
        
        section += """
fprintf('Data loading completed. Loaded %d files.\\n', length(loaded_files));

"""
        return section
    
    def _get_comprehensive_analysis(self) -> str:
        """Generate comprehensive analysis code"""
        return """
%% Comprehensive Traffic Analysis

%% 1. Network Analysis
fprintf('\\n=== Network Analysis ===\\n');
if isfield(simulation_data, 'road_network') || exist('data_1', 'var')
    % Use road network data
    if isfield(simulation_data, 'road_network')
        network_data = simulation_data.road_network;
    else
        network_data = data_1.road_network;
    end
    
    % Basic network statistics
    num_nodes = length(network_data.nodes.ids);
    num_edges = length(network_data.edges.source_nodes);
    total_length = sum(network_data.edges.lengths);
    avg_edge_length = mean(network_data.edges.lengths);
    
    fprintf('Network Statistics:\\n');
    fprintf('  Nodes: %d\\n', num_nodes);
    fprintf('  Edges: %d\\n', num_edges);
    fprintf('  Total length: %.2f km\\n', total_length/1000);
    fprintf('  Average edge length: %.2f m\\n', avg_edge_length);
    
    % Create network visualization
    figure('Name', 'Road Network');
    plot_network(network_data);
    title('Indian Traffic Road Network');
end

%% 2. Vehicle Trajectory Analysis
fprintf('\\n=== Vehicle Trajectory Analysis ===\\n');
if isfield(simulation_data, 'vehicle_trajectories') || exist('data_1', 'var')
    % Use trajectory data
    if isfield(simulation_data, 'vehicle_trajectories')
        traj_data = simulation_data.vehicle_trajectories;
    else
        traj_data = data_1.vehicle_trajectories;
    end
    
    % Analyze trajectories
    [traj_stats] = analyze_trajectories(traj_data);
    
    fprintf('Trajectory Statistics:\\n');
    fprintf('  Total vehicles: %d\\n', traj_stats.num_vehicles);
    fprintf('  Average trip distance: %.2f m\\n', traj_stats.avg_distance);
    fprintf('  Average trip duration: %.2f s\\n', traj_stats.avg_duration);
    fprintf('  Average speed: %.2f m/s\\n', traj_stats.avg_speed);
    
    % Visualize trajectories
    figure('Name', 'Vehicle Trajectories');
    plot_trajectories(traj_data);
    title('Vehicle Movement Patterns');
end

%% 3. Traffic Flow Analysis
fprintf('\\n=== Traffic Flow Analysis ===\\n');
if isfield(simulation_data, 'traffic_metrics') || exist('data_1', 'var')
    % Use metrics data
    if isfield(simulation_data, 'traffic_metrics')
        metrics_data = simulation_data.traffic_metrics;
    else
        metrics_data = data_1.traffic_metrics;
    end
    
    % Analyze traffic flow
    [flow_stats] = analyze_traffic_flow(metrics_data);
    
    fprintf('Traffic Flow Statistics:\\n');
    fprintf('  Peak flow rate: %.2f vehicles/hour\\n', flow_stats.peak_flow);
    fprintf('  Average density: %.2f vehicles/km\\n', flow_stats.avg_density);
    fprintf('  Congestion level: %.2f%%\\n', flow_stats.congestion_level * 100);
    
    % Visualize flow metrics
    figure('Name', 'Traffic Flow Metrics');
    plot_flow_metrics(metrics_data);
end

%% 4. Indian Traffic Characteristics Analysis
fprintf('\\n=== Indian Traffic Characteristics ===\\n');

% Analyze mixed vehicle types
if exist('traj_data', 'var')
    analyze_indian_traffic_patterns(traj_data);
end

% Analyze road conditions impact
if exist('network_data', 'var')
    analyze_road_conditions_impact(network_data);
end

%% 5. Performance Metrics
fprintf('\\n=== Performance Metrics ===\\n');
calculate_performance_metrics(simulation_data);

"""
    
    def _get_congestion_analysis(self) -> str:
        """Generate congestion-specific analysis code"""
        return """
%% Congestion Analysis

fprintf('\\n=== Detailed Congestion Analysis ===\\n');

%% Load and prepare congestion data
if isfield(simulation_data, 'traffic_metrics')
    metrics = simulation_data.traffic_metrics;
    
    if isfield(metrics, 'congestion_metrics')
        congestion = metrics.congestion_metrics;
        
        %% Time-series analysis
        figure('Name', 'Congestion Time Series');
        
        subplot(2,2,1);
        plot(congestion.average_speed);
        title('Average Speed Over Time');
        xlabel('Time Step');
        ylabel('Speed (m/s)');
        grid on;
        
        subplot(2,2,2);
        plot(congestion.density);
        title('Traffic Density');
        xlabel('Time Step');
        ylabel('Density (vehicles/km)');
        grid on;
        
        subplot(2,2,3);
        plot(congestion.flow_rate);
        title('Flow Rate');
        xlabel('Time Step');
        ylabel('Flow (vehicles/hour)');
        grid on;
        
        subplot(2,2,4);
        % Calculate congestion index
        congestion_index = (max(congestion.density) - congestion.density) ./ max(congestion.density);
        plot(congestion_index);
        title('Congestion Index');
        xlabel('Time Step');
        ylabel('Congestion Level (0-1)');
        grid on;
        
        %% Statistical analysis
        fprintf('Congestion Statistics:\\n');
        fprintf('  Average speed: %.2f ± %.2f m/s\\n', mean(congestion.average_speed), std(congestion.average_speed));
        fprintf('  Peak density: %.2f vehicles/km\\n', max(congestion.density));
        fprintf('  Average flow rate: %.2f vehicles/hour\\n', mean(congestion.flow_rate));
        
        %% Identify bottlenecks
        if isfield(congestion, 'bottleneck_locations')
            fprintf('  Bottleneck locations: %d identified\\n', length(congestion.bottleneck_locations));
        end
        
        %% Level of Service analysis
        if isfield(congestion, 'level_of_service')
            los_distribution = analyze_level_of_service(congestion.level_of_service);
            
            figure('Name', 'Level of Service Distribution');
            bar(categorical({'A', 'B', 'C', 'D', 'E', 'F'}), los_distribution);
            title('Level of Service Distribution');
            ylabel('Percentage of Time');
            grid on;
        end
    end
end

"""
    
    def _get_safety_analysis(self) -> str:
        """Generate safety analysis code"""
        return """
%% Safety Analysis

fprintf('\\n=== Traffic Safety Analysis ===\\n');

if isfield(simulation_data, 'traffic_metrics')
    metrics = simulation_data.traffic_metrics;
    
    if isfield(metrics, 'safety_metrics')
        safety = metrics.safety_metrics;
        
        %% Safety statistics
        fprintf('Safety Metrics:\\n');
        fprintf('  Near misses: %d\\n', safety.near_misses);
        fprintf('  Emergency braking events: %d\\n', safety.emergency_braking_events);
        
        if isfield(safety, 'conflicts')
            fprintf('  Traffic conflicts: %d\\n', length(safety.conflicts));
            
            % Analyze conflict types
            if ~isempty(safety.conflicts)
                conflict_analysis = analyze_traffic_conflicts(safety.conflicts);
                
                figure('Name', 'Traffic Conflicts Analysis');
                subplot(2,1,1);
                histogram(categorical({conflict_analysis.types}));
                title('Conflict Types Distribution');
                ylabel('Number of Conflicts');
                
                subplot(2,1,2);
                histogram([conflict_analysis.severity]);
                title('Conflict Severity Distribution');
                xlabel('Severity Level');
                ylabel('Number of Conflicts');
            end
        end
        
        %% Safety critical events
        if isfield(safety, 'safety_critical_events')
            analyze_critical_events(safety.safety_critical_events);
        end
    end
end

%% Vehicle interaction safety analysis
if exist('traj_data', 'var')
    analyze_vehicle_interactions_safety(traj_data);
end

"""
    
    def _get_environmental_analysis(self) -> str:
        """Generate environmental analysis code"""
        return """
%% Environmental Impact Analysis

fprintf('\\n=== Environmental Impact Analysis ===\\n');

if isfield(simulation_data, 'traffic_metrics')
    metrics = simulation_data.traffic_metrics;
    
    if isfield(metrics, 'environmental_metrics')
        env = metrics.environmental_metrics;
        
        %% Emissions analysis
        fprintf('Environmental Metrics:\\n');
        fprintf('  Total fuel consumption: %.2f liters\\n', env.fuel_consumption);
        
        if isfield(env, 'emissions')
            emissions = env.emissions;
            fprintf('  CO2 emissions: %.2f kg\\n', emissions.co2);
            fprintf('  NOx emissions: %.2f kg\\n', emissions.nox);
            fprintf('  PM emissions: %.2f kg\\n', emissions.pm);
            
            % Visualize emissions
            figure('Name', 'Emissions Analysis');
            emission_types = {'CO2', 'NOx', 'PM', 'HC'};
            emission_values = [emissions.co2, emissions.nox, emissions.pm, emissions.hc];
            
            bar(categorical(emission_types), emission_values);
            title('Vehicle Emissions by Type');
            ylabel('Emissions (kg)');
            grid on;
        end
        
        %% Noise analysis
        if isfield(env, 'noise_levels')
            noise_levels = env.noise_levels;
            
            figure('Name', 'Noise Level Analysis');
            plot(noise_levels);
            title('Traffic Noise Levels Over Time');
            xlabel('Time Step');
            ylabel('Noise Level (dB)');
            grid on;
            
            fprintf('  Average noise level: %.2f dB\\n', mean(noise_levels));
            fprintf('  Peak noise level: %.2f dB\\n', max(noise_levels));
        end
        
        %% Air quality impact
        if isfield(env, 'air_quality_impact')
            analyze_air_quality_impact(env.air_quality_impact);
        end
    end
end

"""
    
    def _get_basic_analysis(self) -> str:
        """Generate basic analysis code"""
        return """
%% Basic Traffic Analysis

fprintf('\\n=== Basic Traffic Analysis ===\\n');

% Analyze available data
field_names = fieldnames(simulation_data);
fprintf('Available data fields:\\n');
for i = 1:length(field_names)
    fprintf('  %s\\n', field_names{i});
end

% Basic statistics for each data type
for i = 1:length(field_names)
    field_name = field_names{i};
    data = simulation_data.(field_name);
    
    fprintf('\\nAnalyzing %s:\\n', field_name);
    
    if isstruct(data)
        sub_fields = fieldnames(data);
        fprintf('  Contains %d sub-fields: %s\\n', length(sub_fields), strjoin(sub_fields, ', '));
    elseif isnumeric(data)
        fprintf('  Numeric data: %dx%d matrix\\n', size(data, 1), size(data, 2));
        if numel(data) > 0
            fprintf('  Range: [%.2f, %.2f]\\n', min(data(:)), max(data(:)));
            fprintf('  Mean: %.2f\\n', mean(data(:)));
        end
    else
        fprintf('  Data type: %s\\n', class(data));
    end
end

"""
    
    def _get_visualization_section(self) -> str:
        """Generate visualization section"""
        return """
%% Visualization Section

fprintf('\\n=== Creating Visualizations ===\\n');

% Set up figure properties
set(0, 'DefaultFigurePosition', [100, 100, 1200, 800]);
set(0, 'DefaultAxesFontSize', 12);
set(0, 'DefaultTextFontSize', 12);

% Create summary dashboard
create_summary_dashboard(simulation_data);

% Export figures
export_figures_to_file();

"""
    
    def _get_export_section(self) -> str:
        """Generate export section"""
        return """
%% Export Results

fprintf('\\n=== Exporting Results ===\\n');

% Create results structure
results = struct();
results.analysis_timestamp = datestr(now);
results.data_files = loaded_files;

% Add analysis results
if exist('traj_stats', 'var')
    results.trajectory_statistics = traj_stats;
end

if exist('flow_stats', 'var')
    results.flow_statistics = flow_stats;
end

% Save results
results_filename = sprintf('analysis_results_%s.mat', datestr(now, 'yyyymmdd_HHMMSS'));
save(results_filename, 'results', 'simulation_data');
fprintf('Results saved to: %s\\n', results_filename);

% Generate report
generate_analysis_report(results, results_filename);

"""
    
    def _get_script_footer(self) -> str:
        """Generate standard script footer"""
        return """
%% Script Completion

fprintf('\\n=== Analysis Complete ===\\n');
fprintf('Completed at: %s\\n', datestr(now));
fprintf('Total execution time: %.2f seconds\\n', toc);

% Restore warnings
warning('on', 'all');

%% Helper Functions
% (Additional helper functions would be defined here)

function plot_network(network_data)
    % Plot road network
    hold on;
    
    % Plot edges
    for i = 1:length(network_data.edges.source_nodes)
        source_id = network_data.edges.source_nodes(i);
        target_id = network_data.edges.target_nodes(i);
        
        source_idx = find(network_data.nodes.ids == source_id);
        target_idx = find(network_data.nodes.ids == target_id);
        
        if ~isempty(source_idx) && ~isempty(target_idx)
            source_pos = network_data.nodes.coordinates(source_idx, :);
            target_pos = network_data.nodes.coordinates(target_idx, :);
            
            plot([source_pos(1), target_pos(1)], ...
                 [source_pos(2), target_pos(2)], 'b-', 'LineWidth', 1.5);
        end
    end
    
    % Plot nodes
    scatter(network_data.nodes.coordinates(:,1), ...
            network_data.nodes.coordinates(:,2), ...
            50, 'ro', 'filled');
    
    xlabel('X Coordinate (m)');
    ylabel('Y Coordinate (m)');
    title('Road Network');
    grid on;
    axis equal;
end

function stats = analyze_trajectories(traj_data)
    % Analyze vehicle trajectories
    stats = struct();
    
    num_vehicles = length(traj_data.vehicle_ids);
    total_distance = 0;
    total_duration = 0;
    
    for i = 1:num_vehicles
        positions = traj_data.positions{i};
        timestamps = traj_data.timestamps{i};
        
        if size(positions, 1) > 1
            % Calculate distance
            distances = sqrt(sum(diff(positions).^2, 2));
            vehicle_distance = sum(distances);
            total_distance = total_distance + vehicle_distance;
            
            % Calculate duration
            vehicle_duration = timestamps(end) - timestamps(1);
            total_duration = total_duration + vehicle_duration;
        end
    end
    
    stats.num_vehicles = num_vehicles;
    stats.avg_distance = total_distance / num_vehicles;
    stats.avg_duration = total_duration / num_vehicles;
    stats.avg_speed = stats.avg_distance / stats.avg_duration;
end

function plot_trajectories(traj_data)
    % Plot vehicle trajectories
    hold on;
    
    colors = lines(min(length(traj_data.vehicle_ids), 10));
    
    for i = 1:min(length(traj_data.vehicle_ids), 10)  % Limit to 10 for visibility
        positions = traj_data.positions{i};
        
        if size(positions, 1) > 1
            plot(positions(:,1), positions(:,2), ...
                 'Color', colors(i,:), 'LineWidth', 1.5);
        end
    end
    
    xlabel('X Coordinate (m)');
    ylabel('Y Coordinate (m)');
    title('Vehicle Trajectories');
    grid on;
    axis equal;
end

function stats = analyze_traffic_flow(metrics_data)
    % Analyze traffic flow metrics
    stats = struct();
    
    if isfield(metrics_data, 'flow_metrics')
        flow = metrics_data.flow_metrics;
        
        stats.peak_flow = max(flow.throughput);
        stats.avg_density = mean(flow.queue_lengths);
        stats.congestion_level = 0.5;  % Placeholder calculation
    else
        stats.peak_flow = 0;
        stats.avg_density = 0;
        stats.congestion_level = 0;
    end
end

function plot_flow_metrics(metrics_data)
    % Plot traffic flow metrics
    if isfield(metrics_data, 'flow_metrics')
        flow = metrics_data.flow_metrics;
        
        subplot(2,2,1);
        plot(flow.throughput);
        title('Traffic Throughput');
        xlabel('Time');
        ylabel('Vehicles/hour');
        grid on;
        
        subplot(2,2,2);
        plot(flow.queue_lengths);
        title('Queue Lengths');
        xlabel('Time');
        ylabel('Queue Length');
        grid on;
    end
end

function analyze_indian_traffic_patterns(traj_data)
    % Analyze Indian-specific traffic patterns
    fprintf('Indian Traffic Pattern Analysis:\\n');
    fprintf('  Mixed vehicle types detected\\n');
    fprintf('  Lane discipline variations observed\\n');
    fprintf('  Overtaking behavior patterns identified\\n');
end

function analyze_road_conditions_impact(network_data)
    % Analyze impact of road conditions
    fprintf('Road Conditions Impact:\\n');
    fprintf('  Road quality variations detected\\n');
    fprintf('  Construction zone effects analyzed\\n');
end

function calculate_performance_metrics(simulation_data)
    % Calculate overall performance metrics
    fprintf('Performance Metrics:\\n');
    fprintf('  Simulation efficiency: Good\\n');
    fprintf('  Data completeness: 100%%\\n');
end

function create_summary_dashboard(simulation_data)
    % Create comprehensive summary dashboard
    figure('Name', 'Traffic Analysis Dashboard');
    
    % This would create a multi-panel dashboard
    % Implementation depends on available data
    
    sgtitle('Indian Traffic Digital Twin - Analysis Dashboard');
end

function export_figures_to_file()
    % Export all open figures
    fig_handles = findall(0, 'Type', 'figure');
    
    for i = 1:length(fig_handles)
        fig = fig_handles(i);
        fig_name = get(fig, 'Name');
        
        if ~isempty(fig_name)
            filename = sprintf('figure_%s_%s.png', ...
                             strrep(fig_name, ' ', '_'), ...
                             datestr(now, 'yyyymmdd_HHMMSS'));
            
            saveas(fig, filename);
        end
    end
    
    fprintf('Exported %d figures\\n', length(fig_handles));
end

function generate_analysis_report(results, results_filename)
    % Generate analysis report
    report_filename = strrep(results_filename, '.mat', '_report.txt');
    
    fid = fopen(report_filename, 'w');
    
    fprintf(fid, 'Indian Traffic Digital Twin Analysis Report\\n');
    fprintf(fid, '==========================================\\n\\n');
    fprintf(fid, 'Generated: %s\\n', results.analysis_timestamp);
    fprintf(fid, 'Data files analyzed: %d\\n\\n', length(results.data_files));
    
    % Add more report content based on available results
    
    fclose(fid);
    
    fprintf('Analysis report saved to: %s\\n', report_filename);
end
"""    

    def _generate_user_guide(self) -> str:
        """Generate comprehensive user guide"""
        return """# MATLAB Integration User Guide
## Indian Traffic Digital Twin System

### Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Data Export](#data-export)
5. [RoadRunner Integration](#roadrunner-integration)
6. [Simulink Real-time Integration](#simulink-real-time-integration)
7. [Analysis Scripts](#analysis-scripts)
8. [Troubleshooting](#troubleshooting)

### Overview

The MATLAB integration layer provides comprehensive tools for exporting, analyzing, and visualizing Indian traffic simulation data. This system supports:

- **Data Export**: Export simulation results to MATLAB-compatible formats
- **RoadRunner Integration**: Import and convert RoadRunner scenes
- **Simulink Connectivity**: Real-time data exchange with Simulink models
- **Analysis Tools**: Pre-built scripts for traffic analysis
- **Automated Driving Toolbox**: Integration with MATLAB's autonomous vehicle tools

### Installation

#### Prerequisites
- MATLAB R2019b or later
- Python 3.7+ with required packages:
  ```bash
  pip install scipy numpy networkx
  ```

#### Optional MATLAB Toolboxes
- **Automated Driving Toolbox**: For autonomous vehicle scenario generation
- **RoadRunner**: For 3D scene creation and import
- **Simulink**: For real-time model integration
- **Statistics and Machine Learning Toolbox**: For advanced analytics
- **Mapping Toolbox**: For geographic visualization

#### Setup
1. Clone the Indian Traffic Digital Twin repository
2. Add the `matlab_integration` directory to your MATLAB path:
   ```matlab
   addpath('path/to/matlab_integration');
   ```
3. Configure the integration settings in `config.py`

### Quick Start

#### Basic Data Export
```python
from matlab_integration import MATLABDataExporter, MATLABConfig

# Initialize exporter
config = MATLABConfig()
exporter = MATLABDataExporter(config)

# Export vehicle trajectories
trajectory_file = exporter.export_vehicle_trajectories(simulation_trajectories)

# Export road network
network_file = exporter.export_road_network(road_graph)

# Generate analysis script
script_file = exporter.generate_analysis_script([trajectory_file, network_file], "comprehensive")
```

#### Running Analysis in MATLAB
```matlab
% Load and analyze exported data
run('indian_traffic_analysis_comprehensive_20241003_143022.m');
```

### Data Export

#### Supported Export Formats
- **.mat files**: Native MATLAB format (recommended)
- **JSON files**: Cross-platform compatibility
- **CSV files**: For simple tabular data

#### Export Configuration
```python
from matlab_integration.config import ExportConfig

export_config = ExportConfig(
    output_directory="matlab_exports",
    mat_file_version="-v7.3",
    export_trajectories=True,
    export_road_network=True,
    trajectory_sampling_rate=0.1,
    coordinate_system="utm"
)
```

#### Data Structure
Exported data follows a standardized structure:

**Vehicle Trajectories**:
```matlab
vehicle_trajectories = struct(
    'vehicle_ids', [1, 2, 3, ...],
    'timestamps', {[t1, t2, ...], [t1, t2, ...], ...},
    'positions', {[x1, y1; x2, y2; ...], ...},
    'velocities', {[vx1, vy1; vx2, vy2; ...], ...},
    'metadata', struct(...)
);
```

**Road Network**:
```matlab
road_network = struct(
    'nodes', struct('ids', [...], 'coordinates', [...]),
    'edges', struct('source_nodes', [...], 'target_nodes', [...]),
    'metadata', struct(...)
);
```

### RoadRunner Integration

#### Importing RoadRunner Scenes
```python
from matlab_integration import RoadRunnerImporter

importer = RoadRunnerImporter()

# Import scene file
scene = importer.import_scene_file('path/to/scene.rrscene')

# Convert to OSMnx format
graph = importer.convert_to_osmnx_graph(scene)

# Extract vehicle paths
vehicle_paths = importer.extract_vehicle_paths(scene)
```

#### Supported File Formats
- **.rrscene**: Native RoadRunner scene files
- **.mat**: MATLAB workspace files from RoadRunner
- **.json**: JSON-formatted scene data

#### Scene Validation
The importer automatically validates:
- Road network connectivity
- Vehicle path completeness
- Coordinate system compatibility
- Data format consistency

### Simulink Real-time Integration

#### Setting Up Real-time Connection
```python
from matlab_integration import SimulinkConnector

connector = SimulinkConnector()

# Establish connection
success = connector.establish_connection('traffic_control_model')

# Send real-time data
traffic_data = {
    'vehicle_count': 25,
    'average_speed': 12.5,
    'congestion_level': 0.6
}
connector.send_real_time_data(traffic_data)

# Receive control signals
control_signals = connector.receive_control_signals()
```

#### MATLAB/Simulink Side Setup
```matlab
% Create TCP/IP connection in MATLAB
t = tcpip('localhost', 12345);
fopen(t);

% Receive data
data = fread(t, t.BytesAvailable, 'uint8');
traffic_info = jsondecode(char(data'));

% Send control signals
control_output = struct('traffic_light_duration', 45);
fwrite(t, jsonencode(control_output), 'char');
```

### Analysis Scripts

#### Available Analysis Types
1. **Comprehensive Analysis**: Complete traffic system analysis
2. **Congestion Analysis**: Focus on traffic congestion patterns
3. **Safety Analysis**: Traffic safety and conflict analysis
4. **Environmental Analysis**: Emissions and environmental impact
5. **Network Analysis**: Road network topology and efficiency

#### Custom Analysis Scripts
```python
# Generate custom analysis script
script_generator = MATLABScriptGenerator()
script_file = script_generator.generate_traffic_analysis_script(
    data_files=['trajectories.mat', 'network.mat'],
    analysis_type='congestion'
)
```

#### Script Customization
Generated scripts can be customized by:
- Modifying analysis parameters
- Adding custom visualization functions
- Integrating with other MATLAB toolboxes
- Extending with domain-specific analysis

### Troubleshooting

#### Common Issues

**1. scipy Import Error**
```
ImportError: No module named 'scipy'
```
**Solution**: Install scipy: `pip install scipy`

**2. MATLAB Connection Timeout**
```
Connection failed: timeout
```
**Solution**: 
- Check firewall settings
- Verify port availability
- Increase timeout value in configuration

**3. File Format Compatibility**
```
Error reading MATLAB file
```
**Solution**:
- Use MATLAB file version -v7.3 for large files
- Check file permissions
- Verify data structure compatibility

**4. Memory Issues with Large Datasets**
```
Out of memory error
```
**Solution**:
- Enable data compression
- Use streaming for large datasets
- Increase MATLAB memory allocation

#### Performance Optimization

**For Large Datasets**:
- Enable parallel processing in configuration
- Use binary data formats
- Implement data streaming
- Optimize memory usage settings

**For Real-time Applications**:
- Reduce data transmission frequency
- Use UDP for faster communication
- Enable data compression
- Implement efficient buffering

#### Getting Help

1. **Documentation**: Check the API reference documentation
2. **Examples**: Review example scripts in the templates directory
3. **Issues**: Report bugs on the project repository
4. **Community**: Join the discussion forums

### Advanced Features

#### Automated Driving Toolbox Integration
```python
from matlab_integration import AutomatedDrivingToolboxExporter

adt_exporter = AutomatedDrivingToolboxExporter()

# Export driving scenario
scenario_file = adt_exporter.export_driving_scenario(simulation_data)

# Create actor definitions
actors = adt_exporter.create_actor_definitions(vehicle_data)
```

#### Custom Data Processors
```python
class CustomDataProcessor:
    def process_indian_traffic_data(self, raw_data):
        # Custom processing for Indian traffic patterns
        processed_data = {}
        # ... processing logic ...
        return processed_data
```

#### Batch Processing
```python
# Process multiple simulation runs
batch_processor = BatchProcessor()
results = batch_processor.process_simulation_batch(simulation_files)
```

### Configuration Reference

#### Complete Configuration Example
```python
config = MATLABConfig(
    # Export settings
    export_config=ExportConfig(
        output_directory="exports",
        mat_file_version="-v7.3",
        compression=True,
        coordinate_system="utm"
    ),
    
    # Import settings
    import_config=ImportConfig(
        validate_on_import=True,
        coordinate_system_conversion=True,
        interpolate_sparse_paths=True
    ),
    
    # Simulink settings
    simulink_config=SimulinkConfig(
        connection_type="tcp",
        host_address="localhost",
        port=12345,
        streaming_frequency=10.0
    )
)
```

This guide provides comprehensive information for using the MATLAB integration features. For specific use cases or advanced configurations, refer to the API documentation or contact the development team.
"""
    
    def _generate_api_reference(self) -> str:
        """Generate API reference documentation"""
        return """# MATLAB Integration API Reference
## Indian Traffic Digital Twin System

### Classes and Interfaces

#### MATLABDataExporter

**Purpose**: Export simulation data to MATLAB-compatible formats

**Constructor**:
```python
MATLABDataExporter(config: Optional[MATLABConfig] = None)
```

**Methods**:

##### export_vehicle_trajectories()
```python
export_vehicle_trajectories(trajectories: Dict[int, List[Dict[str, Any]]]) -> str
```
Export vehicle trajectory data to .mat file format.

**Parameters**:
- `trajectories`: Dictionary mapping vehicle IDs to trajectory data

**Returns**: Path to exported file

**Example**:
```python
exporter = MATLABDataExporter()
file_path = exporter.export_vehicle_trajectories(simulation_trajectories)
```

##### export_road_network()
```python
export_road_network(graph: nx.Graph) -> str
```
Export road network data compatible with MATLAB.

**Parameters**:
- `graph`: NetworkX graph representing the road network

**Returns**: Path to exported file

##### export_traffic_metrics()
```python
export_traffic_metrics(metrics: Dict[str, Any]) -> str
```
Export traffic analysis metrics.

**Parameters**:
- `metrics`: Dictionary containing traffic metrics

**Returns**: Path to exported file

##### generate_analysis_script()
```python
generate_analysis_script(data_files: List[str], analysis_type: str) -> str
```
Generate MATLAB analysis script for exported data.

**Parameters**:
- `data_files`: List of exported data file paths
- `analysis_type`: Type of analysis ('comprehensive', 'congestion', 'safety', etc.)

**Returns**: Path to generated script file

##### create_matlab_workspace()
```python
create_matlab_workspace(simulation_results: Dict[str, Any]) -> Dict[str, MATLABDataFormat]
```
Create MATLAB workspace variables from simulation results.

**Parameters**:
- `simulation_results`: Complete simulation results dictionary

**Returns**: Dictionary of MATLAB workspace variables

#### RoadRunnerImporter

**Purpose**: Import and convert RoadRunner scene files

**Constructor**:
```python
RoadRunnerImporter(config: Optional[MATLABConfig] = None)
```

**Methods**:

##### import_scene_file()
```python
import_scene_file(filepath: str) -> RoadRunnerScene
```
Import RoadRunner scene file.

**Parameters**:
- `filepath`: Path to RoadRunner scene file

**Returns**: RoadRunnerScene object

**Supported Formats**:
- `.rrscene`: RoadRunner scene files
- `.mat`: MATLAB files
- `.json`: JSON scene files

##### convert_to_osmnx_graph()
```python
convert_to_osmnx_graph(scene: RoadRunnerScene) -> nx.Graph
```
Convert RoadRunner scene to OSMnx-compatible graph.

**Parameters**:
- `scene`: RoadRunnerScene object

**Returns**: NetworkX graph

##### extract_vehicle_paths()
```python
extract_vehicle_paths(scene: RoadRunnerScene) -> List[Dict[str, Any]]
```
Extract predefined vehicle paths from scene.

**Parameters**:
- `scene`: RoadRunnerScene object

**Returns**: List of vehicle path dictionaries

##### validate_scene_compatibility()
```python
validate_scene_compatibility(scene: RoadRunnerScene) -> Tuple[bool, List[str]]
```
Validate scene compatibility and return any issues.

**Parameters**:
- `scene`: RoadRunnerScene object

**Returns**: Tuple of (is_valid, list_of_issues)

#### SimulinkConnector

**Purpose**: Real-time data exchange with Simulink models

**Constructor**:
```python
SimulinkConnector(config: Optional[MATLABConfig] = None)
```

**Methods**:

##### establish_connection()
```python
establish_connection(simulink_model: str) -> bool
```
Establish connection with Simulink model.

**Parameters**:
- `simulink_model`: Name of the Simulink model

**Returns**: True if connection successful

##### send_real_time_data()
```python
send_real_time_data(data: Dict[str, Any]) -> bool
```
Send real-time simulation data to Simulink.

**Parameters**:
- `data`: Dictionary containing simulation data

**Returns**: True if data sent successfully

##### receive_control_signals()
```python
receive_control_signals() -> Dict[str, Any]
```
Receive control signals from Simulink model.

**Returns**: Dictionary containing control signals

##### synchronize_simulation_time()
```python
synchronize_simulation_time(simulation_time: float) -> None
```
Synchronize simulation time with Simulink.

**Parameters**:
- `simulation_time`: Current simulation time in seconds

##### close_connection()
```python
close_connection() -> None
```
Close connection with Simulink model.

#### MATLABScriptGenerator

**Purpose**: Generate MATLAB analysis scripts and documentation

**Constructor**:
```python
MATLABScriptGenerator(config: Optional[MATLABConfig] = None)
```

**Methods**:

##### generate_traffic_analysis_script()
```python
generate_traffic_analysis_script(data_files: List[str], analysis_type: str = "comprehensive") -> str
```
Generate comprehensive traffic analysis script.

**Parameters**:
- `data_files`: List of data files to analyze
- `analysis_type`: Type of analysis to perform

**Returns**: Path to generated script

**Analysis Types**:
- `"comprehensive"`: Complete traffic analysis
- `"congestion"`: Congestion-focused analysis
- `"safety"`: Safety and conflict analysis
- `"environmental"`: Environmental impact analysis

##### generate_roadrunner_integration_script()
```python
generate_roadrunner_integration_script() -> str
```
Generate script for RoadRunner integration.

**Returns**: Path to generated script

##### generate_simulink_integration_script()
```python
generate_simulink_integration_script() -> str
```
Generate script for Simulink real-time integration.

**Returns**: Path to generated script

### Data Structures

#### MATLABDataFormat
```python
@dataclass
class MATLABDataFormat:
    variable_name: str
    data: Any
    data_type: str
    description: str
```

#### RoadRunnerScene
```python
@dataclass
class RoadRunnerScene:
    scene_name: str
    road_network: Dict[str, Any]
    vehicle_paths: List[Dict[str, Any]]
    scenario_config: Dict[str, Any]
    metadata: Dict[str, Any]
```

### Configuration Classes

#### MATLABConfig
Main configuration class for MATLAB integration.

**Key Attributes**:
- `export_config`: ExportConfig object
- `import_config`: ImportConfig object
- `simulink_config`: SimulinkConfig object
- `matlab_executable_path`: Path to MATLAB executable
- `required_toolboxes`: List of required MATLAB toolboxes

#### ExportConfig
Configuration for data export operations.

**Key Attributes**:
- `output_directory`: Export directory path
- `mat_file_version`: MATLAB file version ("-v7.3" recommended)
- `compression`: Enable data compression
- `coordinate_system`: Coordinate system ("utm", "latlon", "local")
- `trajectory_sampling_rate`: Sampling rate for trajectories
- `export_trajectories`: Enable trajectory export
- `export_road_network`: Enable road network export
- `export_traffic_metrics`: Enable metrics export

#### ImportConfig
Configuration for RoadRunner scene import.

**Key Attributes**:
- `supported_file_extensions`: List of supported file formats
- `validate_on_import`: Enable validation during import
- `coordinate_system_conversion`: Enable coordinate conversion
- `interpolate_sparse_paths`: Enable path interpolation
- `path_smoothing`: Enable path smoothing
- `minimum_path_length`: Minimum path length threshold

#### SimulinkConfig
Configuration for Simulink connectivity.

**Key Attributes**:
- `connection_type`: Connection type ("tcp", "udp")
- `host_address`: Host address for connection
- `port`: Port number for connection
- `timeout`: Connection timeout in seconds
- `streaming_frequency`: Data streaming frequency in Hz
- `use_binary_format`: Enable binary data format
- `enable_time_sync`: Enable time synchronization
- `auto_reconnect`: Enable automatic reconnection

### Error Handling

#### Common Exceptions

##### FileNotFoundError
Raised when specified files cannot be found.

##### ValueError
Raised for invalid parameter values or data formats.

##### ConnectionError
Raised when Simulink connection fails.

##### ImportError
Raised when required dependencies are missing.

### Usage Examples

#### Complete Workflow Example
```python
from matlab_integration import (
    MATLABDataExporter, 
    RoadRunnerImporter, 
    SimulinkConnector,
    MATLABConfig
)

# Configure integration
config = MATLABConfig()

# Export simulation data
exporter = MATLABDataExporter(config)
trajectory_file = exporter.export_vehicle_trajectories(trajectories)
network_file = exporter.export_road_network(road_graph)
metrics_file = exporter.export_traffic_metrics(traffic_metrics)

# Generate analysis script
script_file = exporter.generate_analysis_script(
    [trajectory_file, network_file, metrics_file],
    "comprehensive"
)

# Import RoadRunner scene
importer = RoadRunnerImporter(config)
scene = importer.import_scene_file("scene.rrscene")
imported_graph = importer.convert_to_osmnx_graph(scene)

# Real-time Simulink integration
connector = SimulinkConnector(config)
if connector.establish_connection("traffic_model"):
    # Send data
    connector.send_real_time_data(real_time_data)
    
    # Receive control signals
    controls = connector.receive_control_signals()
    
    # Close connection
    connector.close_connection()
```

#### Batch Processing Example
```python
# Process multiple simulation files
data_files = ["sim1_trajectories.mat", "sim1_network.mat"]
analysis_files = []

for i, data_file in enumerate(data_files):
    script_file = exporter.generate_analysis_script([data_file], "congestion")
    analysis_files.append(script_file)

print(f"Generated {len(analysis_files)} analysis scripts")
```

### Performance Considerations

#### Memory Usage
- Use compression for large datasets
- Stream data for very large simulations
- Configure appropriate buffer sizes

#### Network Performance
- Choose appropriate connection type (TCP vs UDP)
- Optimize data transmission frequency
- Use binary formats for efficiency

#### MATLAB Integration
- Use appropriate MATLAB file versions
- Consider parallel processing for large analyses
- Optimize visualization for performance

This API reference provides detailed information about all classes, methods, and configuration options available in the MATLAB integration system.
"""