# MATLAB Integration API Reference
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
