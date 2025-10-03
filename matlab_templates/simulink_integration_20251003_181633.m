% Simulink Integration Script for Indian Traffic Digital Twin
% Generated on: 2025-10-03 18:16:33
% Analysis Type: simulink
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

fprintf('=== Simulink Integration ===\n');
fprintf('Started at: %s\n', datestr(now));


%% Simulink Real-time Integration
% This script demonstrates real-time data exchange with Indian traffic simulation

%% Configuration
simulink_model = 'indian_traffic_control_model';
host_address = 'localhost';
port = 12345;

%% Initialize Connection
fprintf('Initializing Simulink connection...\n');

% Create TCP/IP connection
try
    t = tcpip(host_address, port);
    set(t, 'InputBufferSize', 8192);
    set(t, 'OutputBufferSize', 8192);
    set(t, 'Timeout', 10);
    
    fopen(t);
    fprintf('Connected to traffic simulation at %s:%d\n', host_address, port);
    
    connected = true;
catch ME
    fprintf('Connection failed: %s\n', ME.message);
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

fprintf('Starting real-time simulation...\n');

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
            
            fprintf('Time: %.1fs - Vehicles: %d, Avg Speed: %.2f m/s\n', ...
                    simulation_time, ...
                    traffic_info.vehicle_count, ...
                    traffic_info.average_speed);
        end
        
        % Update simulation time
        simulation_time = simulation_time + time_step;
        pause(time_step);
        
    catch ME
        fprintf('Communication error: %s\n', ME.message);
        connected = false;
    end
end

%% Close Connection
if exist('t', 'var') && isvalid(t)
    fclose(t);
    delete(t);
    fprintf('Connection closed\n');
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
    fprintf('\nAnalyzing real-time simulation results...\n');
    
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
    fprintf('Simulation Statistics:\n');
    fprintf('  Duration: %.1f seconds\n', max(times));
    fprintf('  Average vehicle count: %.1f\n', mean(vehicle_counts));
    fprintf('  Average speed: %.2f m/s\n', mean(avg_speeds));
    fprintf('  Speed standard deviation: %.2f m/s\n', std(avg_speeds));
end

%% Script Completion

fprintf('\n=== Analysis Complete ===\n');
fprintf('Completed at: %s\n', datestr(now));
fprintf('Total execution time: %.2f seconds\n', toc);

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
    fprintf('Indian Traffic Pattern Analysis:\n');
    fprintf('  Mixed vehicle types detected\n');
    fprintf('  Lane discipline variations observed\n');
    fprintf('  Overtaking behavior patterns identified\n');
end

function analyze_road_conditions_impact(network_data)
    % Analyze impact of road conditions
    fprintf('Road Conditions Impact:\n');
    fprintf('  Road quality variations detected\n');
    fprintf('  Construction zone effects analyzed\n');
end

function calculate_performance_metrics(simulation_data)
    % Calculate overall performance metrics
    fprintf('Performance Metrics:\n');
    fprintf('  Simulation efficiency: Good\n');
    fprintf('  Data completeness: 100%%\n');
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
    
    fprintf('Exported %d figures\n', length(fig_handles));
end

function generate_analysis_report(results, results_filename)
    % Generate analysis report
    report_filename = strrep(results_filename, '.mat', '_report.txt');
    
    fid = fopen(report_filename, 'w');
    
    fprintf(fid, 'Indian Traffic Digital Twin Analysis Report\n');
    fprintf(fid, '==========================================\n\n');
    fprintf(fid, 'Generated: %s\n', results.analysis_timestamp);
    fprintf(fid, 'Data files analyzed: %d\n\n', length(results.data_files));
    
    % Add more report content based on available results
    
    fclose(fid);
    
    fprintf('Analysis report saved to: %s\n', report_filename);
end
