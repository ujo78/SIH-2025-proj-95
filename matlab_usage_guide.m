% MATLAB Usage Guide for Indian Traffic Digital Twin
% Generated on: 2025-10-03 18:20:17

%% Quick Start Guide

% 1. LOAD EXPORTED DATA
% The following data files have been exported from your simulation:

% File 1: matlab_exports\traffic_sim_trajectories_20251003_182017.mat
data_1 = load('matlab_exports\traffic_sim_trajectories_20251003_182017.mat');
fprintf('Loaded matlab_exports\traffic_sim_trajectories_20251003_182017.mat\n');

% File 2: matlab_exports\traffic_sim_road_network_20251003_182017.mat
data_2 = load('matlab_exports\traffic_sim_road_network_20251003_182017.mat');
fprintf('Loaded matlab_exports\traffic_sim_road_network_20251003_182017.mat\n');

% File 3: matlab_exports\traffic_sim_metrics_20251003_182017.mat
data_3 = load('matlab_exports\traffic_sim_metrics_20251003_182017.mat');
fprintf('Loaded matlab_exports\traffic_sim_metrics_20251003_182017.mat\n');


%% 2. BASIC DATA EXPLORATION

% Check what data is available
if exist('data_1', 'var')
    disp('Available fields in data_1:');
    disp(fieldnames(data_1));
end

% Display basic statistics
if exist('data_1', 'var') && isfield(data_1, 'vehicle_trajectories')
    traj = data_1.vehicle_trajectories;
    fprintf('Number of vehicles: %d\n', length(traj.vehicle_ids));
    fprintf('Simulation metadata: %s\n', traj.metadata.coordinate_system);
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
    fprintf('\nNetwork Analysis:\n');
    fprintf('  Nodes: %d\n', length(network.nodes.ids));
    fprintf('  Edges: %d\n', length(network.edges.source_nodes));
    fprintf('  Total length: %.2f km\n', sum(network.edges.lengths)/1000);
    fprintf('  Average edge length: %.2f m\n', mean(network.edges.lengths));
end

%% 5. EXPORT RESULTS

% Save analysis results
results = struct();
results.analysis_date = datestr(now);
results.data_files = {'matlab_exports\traffic_sim_trajectories_20251003_182017.mat', 'matlab_exports\traffic_sim_road_network_20251003_182017.mat', 'matlab_exports\traffic_sim_metrics_20251003_182017.mat', };

% Add your analysis results here
% results.trajectory_stats = calculate_trajectory_stats(data_1.vehicle_trajectories);

% Save results
save('indian_traffic_analysis_results.mat', 'results');
fprintf('Analysis results saved to indian_traffic_analysis_results.mat\n');

%% 6. NEXT STEPS

fprintf('\n=== Next Steps ===\n');
fprintf('1. Run the generated analysis scripts:\n');
fprintf('   run(''matlab_templates\indian_traffic_analysis_comprehensive_20251003_182017.m'')\n');
fprintf('   run(''matlab_templates\indian_traffic_analysis_congestion_20251003_182017.m'')\n');
fprintf('   run(''matlab_templates\indian_traffic_analysis_safety_20251003_182017.m'')\n');
fprintf('   run(''matlab_templates\indian_traffic_analysis_environmental_20251003_182017.m'')\n');
fprintf('   run(''matlab_templates\roadrunner_integration_20251003_182017.m'')\n');
fprintf('   run(''matlab_templates\simulink_integration_20251003_182017.m'')\n');

fprintf('2. Customize the analysis for your specific needs\n');
fprintf('3. Integrate with other MATLAB toolboxes as needed\n');
fprintf('4. Set up real-time Simulink integration if required\n');

fprintf('\nFor more information, see the generated documentation files.\n');
