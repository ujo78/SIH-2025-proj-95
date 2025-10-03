% Indian Traffic Digital Twin - MATLAB Demo
% Generated on: 2025-10-03 18:30:53
%
% This script provides a quick start for analyzing Indian traffic simulation data

clear; clc; close all;

fprintf('=== Indian Traffic Digital Twin - MATLAB Demo ===\n');
fprintf('Generated on: 2025-10-03 18:30:53\n\n');

%% 1. Load Simulation Data
fprintf('Loading simulation data...\n');

% Load exported data files

try
    data_1 = load('matlab_demo_exports/indian_traffic_demo_trajectories_20251003_183053.mat');
    fprintf('  Loaded: matlab_demo_exports/indian_traffic_demo_trajectories_20251003_183053.mat\n');
catch ME
    fprintf('  Failed to load: matlab_demo_exports/indian_traffic_demo_trajectories_20251003_183053.mat\n');
    fprintf('    Error: %s\n', ME.message);
end

try
    data_2 = load('matlab_demo_exports/indian_traffic_demo_road_network_20251003_183053.mat');
    fprintf('  Loaded: matlab_demo_exports/indian_traffic_demo_road_network_20251003_183053.mat\n');
catch ME
    fprintf('  Failed to load: matlab_demo_exports/indian_traffic_demo_road_network_20251003_183053.mat\n');
    fprintf('    Error: %s\n', ME.message);
end

try
    data_3 = load('matlab_demo_exports/indian_traffic_demo_metrics_20251003_183053.mat');
    fprintf('  Loaded: matlab_demo_exports/indian_traffic_demo_metrics_20251003_183053.mat\n');
catch ME
    fprintf('  Failed to load: matlab_demo_exports/indian_traffic_demo_metrics_20251003_183053.mat\n');
    fprintf('    Error: %s\n', ME.message);
end

%% 2. Quick Data Overview
fprintf('\nData Overview:\n');

% Vehicle trajectories
if exist('data_1', 'var') && isfield(data_1, 'vehicle_trajectories')
    traj = data_1.vehicle_trajectories;
    fprintf('  Vehicles tracked: %d\n', length(traj.vehicle_ids));
    
    % Calculate basic statistics
    total_points = 0;
    for i = 1:length(traj.positions)
        if iscell(traj.positions)
            total_points = total_points + size(traj.positions{i}, 1);
        end
    end
    fprintf('  Total trajectory points: %d\n', total_points);
end

% Road network
if exist('data_2', 'var') && isfield(data_2, 'road_network')
    network = data_2.road_network;
    fprintf('  Network nodes: %d\n', length(network.nodes.ids));
    fprintf('  Network edges: %d\n', length(network.edges.source_nodes));
    fprintf('  Total road length: %.2f km\n', sum(network.edges.lengths)/1000);
end

% Traffic metrics
if exist('data_3', 'var') && isfield(data_3, 'traffic_metrics')
    metrics = data_3.traffic_metrics;
    if isfield(metrics, 'flow_metrics')
        fprintf('  Total vehicles simulated: %d\n', metrics.flow_metrics.total_vehicles);
        fprintf('  Completed trips: %d\n', metrics.flow_metrics.completed_trips);
    end
end

%% 3. Quick Visualization
fprintf('\nCreating visualizations...\n');

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
    
    fprintf('  Vehicle trajectories plotted\n');
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
    
    fprintf('  Road network plotted\n');
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
    
    fprintf('  Traffic metrics plotted\n');
end

%% 4. Available Analysis Scripts
fprintf('\nAvailable analysis scripts:\n');
fprintf('  - indian_traffic_analysis_comprehensive_20251003_183053.m\n');
fprintf('    Run with: run(''matlab_demo_scripts/indian_traffic_analysis_comprehensive_20251003_183053.m'')\n');
fprintf('  - indian_traffic_analysis_congestion_20251003_183053.m\n');
fprintf('    Run with: run(''matlab_demo_scripts/indian_traffic_analysis_congestion_20251003_183053.m'')\n');
fprintf('  - roadrunner_integration_20251003_183053.m\n');
fprintf('    Run with: run(''matlab_demo_scripts/roadrunner_integration_20251003_183053.m'')\n');
fprintf('  - simulink_integration_20251003_183053.m\n');
fprintf('    Run with: run(''matlab_demo_scripts/simulink_integration_20251003_183053.m'')\n');

%% 5. Next Steps
fprintf('\nNext Steps:\n');
fprintf('1. Explore the generated visualizations\n');
fprintf('2. Run detailed analysis scripts listed above\n');
fprintf('3. Modify analysis parameters for your specific needs\n');
fprintf('4. Export results for further processing\n');

fprintf('\n=== Demo Complete ===\n');
fprintf('For more information, see the generated documentation.\n');

% Save workspace for later use
save('indian_traffic_demo_workspace.mat');
fprintf('\nWorkspace saved to: indian_traffic_demo_workspace.mat\n');
