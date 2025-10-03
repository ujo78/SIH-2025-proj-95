# MATLAB Integration User Guide
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
