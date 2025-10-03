# MATLAB Integration Guide
## Indian Traffic Digital Twin System

### Overview

The MATLAB integration system is now fully functional and tested! This guide shows you how to use it with MATLAB to analyze Indian traffic simulation data.

### ✅ What's Working

All MATLAB integration components are working correctly:

- **✅ Data Export**: Exports simulation data to .mat files
- **✅ Script Generation**: Creates MATLAB analysis scripts automatically  
- **✅ RoadRunner Import**: Imports and converts RoadRunner scenes
- **✅ Simulink Connectivity**: Real-time data exchange (requires MATLAB/Simulink)
- **✅ Documentation**: Complete user guides and API references

### Quick Start

#### 1. Generate Sample Data and Scripts

Run the demo to create sample data and MATLAB scripts:

```bash
python matlab_demo.py
```

This creates:
- **Data files** (`.mat` format): Vehicle trajectories, road network, traffic metrics
- **Analysis scripts** (`.m` files): Ready-to-run MATLAB analysis code
- **Startup script**: `indian_traffic_matlab_demo.m` for easy access

#### 2. Open MATLAB

1. Launch MATLAB
2. Navigate to your project directory
3. Run the startup script:

```matlab
indian_traffic_matlab_demo
```

This will:
- Load all exported data
- Display data overview
- Create visualizations automatically
- Show available analysis options

### Using with Real Traffic Simulation

#### Export Your Simulation Data

```python
from matlab_integration import MATLABDataExporter, MATLABConfig

# Configure export settings
config = MATLABConfig()
config.export_config.output_directory = "my_exports"
config.export_config.coordinate_system = "utm"  # or "latlon", "local"

# Initialize exporter
exporter = MATLABDataExporter(config)

# Export your simulation data
trajectory_file = exporter.export_vehicle_trajectories(your_trajectories)
network_file = exporter.export_road_network(your_road_graph)  
metrics_file = exporter.export_traffic_metrics(your_metrics)

# Generate analysis script
script_file = exporter.generate_analysis_script(
    [trajectory_file, network_file, metrics_file], 
    "comprehensive"  # or "congestion", "safety", "environmental"
)
```

#### Run Analysis in MATLAB

```matlab
% Load your exported data
data_1 = load('my_exports/trajectories.mat');
data_2 = load('my_exports/network.mat');
data_3 = load('my_exports/metrics.mat');

% Run generated analysis script
run('my_analysis_script.m');
```

### Available Analysis Types

#### 1. Comprehensive Analysis
- Complete traffic system analysis
- Vehicle trajectory patterns
- Network topology analysis
- Traffic flow metrics
- Performance statistics

```python
script = generator.generate_traffic_analysis_script(data_files, "comprehensive")
```

#### 2. Congestion Analysis
- Traffic density over time
- Speed variations
- Flow rate analysis
- Level of Service (LOS) distribution
- Bottleneck identification

```python
script = generator.generate_traffic_analysis_script(data_files, "congestion")
```

#### 3. Safety Analysis
- Near-miss detection
- Traffic conflict analysis
- Emergency braking events
- Safety critical events

```python
script = generator.generate_traffic_analysis_script(data_files, "safety")
```

#### 4. Environmental Analysis
- Fuel consumption
- Emissions (CO2, NOx, PM)
- Noise level analysis
- Air quality impact

```python
script = generator.generate_traffic_analysis_script(data_files, "environmental")
```

### RoadRunner Integration

#### Import RoadRunner Scenes

```python
from matlab_integration import RoadRunnerImporter

importer = RoadRunnerImporter()

# Import scene file (.rrscene, .mat, or .json)
scene = importer.import_scene_file('path/to/scene.rrscene')

# Convert to network format
graph = importer.convert_to_osmnx_graph(scene)

# Extract vehicle paths
vehicle_paths = importer.extract_vehicle_paths(scene)
```

#### Use in MATLAB

```matlab
% Run the RoadRunner integration script
run('roadrunner_integration_script.m');

% This will help you:
% - Import RoadRunner scenes
% - Convert to MATLAB graph format
% - Analyze network properties
% - Extract vehicle paths
```

### Real-time Simulink Integration

#### Python Side (Simulation)

```python
from matlab_integration import SimulinkConnector

connector = SimulinkConnector()

# Connect to Simulink model
if connector.establish_connection('your_simulink_model'):
    
    # Send real-time data
    traffic_data = {
        'vehicle_count': 25,
        'average_speed': 12.5,
        'congestion_level': 0.6,
        'simulation_time': 45.2
    }
    connector.send_real_time_data(traffic_data)
    
    # Receive control signals
    controls = connector.receive_control_signals()
    
    # Close when done
    connector.close_connection()
```

#### MATLAB/Simulink Side

```matlab
% Run the Simulink integration script
run('simulink_integration_script.m');

% This provides:
% - TCP/IP connection setup
% - Real-time data exchange
% - Control signal processing
% - Time synchronization
```

### Data Formats

#### Vehicle Trajectories
```matlab
trajectories = struct(
    'vehicle_ids', [1, 2, 3, ...],
    'timestamps', {[t1, t2, ...], [t1, t2, ...], ...},
    'positions', {[x1, y1; x2, y2; ...], ...},
    'velocities', {[vx1, vy1; vx2, vy2; ...], ...},
    'metadata', struct(...)
);
```

#### Road Network
```matlab
network = struct(
    'nodes', struct('ids', [...], 'coordinates', [...]),
    'edges', struct('source_nodes', [...], 'target_nodes', [...]),
    'metadata', struct(...)
);
```

#### Traffic Metrics
```matlab
metrics = struct(
    'congestion_metrics', struct(...),
    'flow_metrics', struct(...),
    'safety_metrics', struct(...),
    'environmental_metrics', struct(...)
);
```

### Example MATLAB Analysis

```matlab
%% Load Indian Traffic Data
data = load('indian_traffic_trajectories.mat');
trajectories = data.vehicle_trajectories;

%% Basic Analysis
fprintf('Analyzing %d vehicles\n', length(trajectories.vehicle_ids));

% Plot all trajectories
figure;
hold on;
colors = lines(length(trajectories.vehicle_ids));

for i = 1:length(trajectories.vehicle_ids)
    pos = trajectories.positions{i};
    plot(pos(:,1), pos(:,2), 'Color', colors(i,:), 'LineWidth', 2);
end

xlabel('X Coordinate (m)');
ylabel('Y Coordinate (m)');
title('Indian Traffic Vehicle Trajectories');
grid on;
axis equal;

%% Calculate Statistics
total_distances = zeros(length(trajectories.vehicle_ids), 1);

for i = 1:length(trajectories.vehicle_ids)
    pos = trajectories.positions{i};
    if size(pos, 1) > 1
        distances = sqrt(sum(diff(pos).^2, 2));
        total_distances(i) = sum(distances);
    end
end

fprintf('Average travel distance: %.2f m\n', mean(total_distances));
fprintf('Max travel distance: %.2f m\n', max(total_distances));

%% Speed Analysis
if isfield(trajectories, 'velocities')
    avg_speeds = zeros(length(trajectories.vehicle_ids), 1);
    
    for i = 1:length(trajectories.vehicle_ids)
        vel = trajectories.velocities{i};
        speeds = sqrt(sum(vel.^2, 2));
        avg_speeds(i) = mean(speeds);
    end
    
    figure;
    histogram(avg_speeds, 10);
    xlabel('Average Speed (m/s)');
    ylabel('Number of Vehicles');
    title('Speed Distribution');
    grid on;
end
```

### Troubleshooting

#### Common Issues

1. **"scipy not found"**
   ```bash
   pip install scipy
   ```

2. **"MATLAB not found"**
   - Install MATLAB or use the generated scripts manually
   - Data is exported in .mat format regardless

3. **"File format error"**
   - Files are exported in MATLAB v5 format for compatibility
   - Use `load()` function in MATLAB to read .mat files

4. **"Connection timeout" (Simulink)**
   - Check firewall settings
   - Verify MATLAB/Simulink is running
   - Ensure correct port configuration

#### Performance Tips

- Use compression for large datasets
- Export data in chunks for very large simulations
- Use appropriate coordinate systems (UTM recommended)
- Enable parallel processing for large analyses

### File Structure

After running the integration, you'll have:

```
project/
├── matlab_demo_exports/           # Exported .mat files
│   ├── trajectories_*.mat
│   ├── road_network_*.mat
│   └── metrics_*.mat
├── matlab_demo_scripts/           # Generated analysis scripts
│   ├── comprehensive_analysis_*.m
│   ├── congestion_analysis_*.m
│   ├── roadrunner_integration_*.m
│   └── simulink_integration_*.m
├── matlab_templates/              # Documentation and templates
│   ├── MATLAB_Integration_Guide_*.md
│   └── MATLAB_API_Reference_*.md
└── indian_traffic_matlab_demo.m   # Main startup script
```

### Next Steps

1. **Customize Analysis**: Modify generated scripts for your specific needs
2. **Add Toolboxes**: Integrate with MATLAB toolboxes (Mapping, Statistics, etc.)
3. **Automate Workflows**: Create batch processing scripts
4. **Real-time Integration**: Set up Simulink models for control systems
5. **Visualization**: Create custom dashboards and reports

### Support

- Check the generated documentation files for detailed API reference
- Review example scripts for implementation patterns
- Test with sample data before using real simulation results

The MATLAB integration is fully functional and ready for production use with Indian traffic simulation data!