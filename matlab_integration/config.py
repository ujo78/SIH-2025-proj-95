"""
Configuration Classes for MATLAB Integration

This module defines configuration classes for MATLAB data export,
RoadRunner import, and Simulink connectivity settings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path


@dataclass
class ExportConfig:
    """Configuration for MATLAB data export"""
    
    # File format settings
    output_directory: str = "matlab_exports"
    file_prefix: str = "traffic_sim"
    mat_file_version: str = "-v5"  # MATLAB file version
    compression: bool = True
    
    # Data export options
    export_trajectories: bool = True
    export_road_network: bool = True
    export_traffic_metrics: bool = True
    export_vehicle_interactions: bool = False
    export_emergency_events: bool = False
    
    # Trajectory export settings
    trajectory_sampling_rate: float = 0.1  # seconds
    coordinate_system: str = "utm"  # "utm", "latlon", "local"
    include_velocity_data: bool = True
    include_acceleration_data: bool = False
    
    # Road network export settings
    include_lane_geometry: bool = True
    include_traffic_signals: bool = True
    include_road_conditions: bool = True
    simplify_geometry: bool = False
    
    # Metrics export settings
    metrics_aggregation_interval: float = 60.0  # seconds
    include_congestion_metrics: bool = True
    include_safety_metrics: bool = False
    include_environmental_metrics: bool = False


@dataclass
class ImportConfig:
    """Configuration for RoadRunner scene import"""
    
    # File handling
    supported_file_extensions: List[str] = field(default_factory=lambda: [".rrscene", ".mat", ".json"])
    validate_on_import: bool = True
    backup_original_files: bool = True
    
    # Conversion settings
    coordinate_system_conversion: bool = True
    target_coordinate_system: str = "utm"
    road_network_simplification: float = 0.1  # tolerance for geometry simplification
    
    # Scene processing options
    extract_lane_markings: bool = True
    extract_traffic_signs: bool = True
    extract_road_furniture: bool = False
    process_elevation_data: bool = False
    
    # Vehicle path processing
    interpolate_sparse_paths: bool = True
    path_smoothing: bool = True
    minimum_path_length: float = 10.0  # meters
    
    # Validation settings
    check_network_connectivity: bool = True
    validate_vehicle_paths: bool = True
    report_import_warnings: bool = True


@dataclass
class SimulinkConfig:
    """Configuration for Simulink real-time connectivity"""
    
    # Connection settings
    connection_type: str = "tcp"  # "tcp", "udp", "shared_memory"
    host_address: str = "localhost"
    port: int = 12345
    timeout: float = 5.0  # seconds
    
    # Data streaming settings
    streaming_frequency: float = 10.0  # Hz
    buffer_size: int = 1000
    data_compression: bool = False
    
    # Synchronization settings
    enable_time_sync: bool = True
    sync_tolerance: float = 0.01  # seconds
    max_sync_attempts: int = 3
    
    # Data format settings
    use_binary_format: bool = True
    include_timestamps: bool = True
    coordinate_precision: int = 6  # decimal places
    
    # Error handling
    auto_reconnect: bool = True
    max_reconnect_attempts: int = 5
    reconnect_delay: float = 1.0  # seconds


@dataclass
class MATLABConfig:
    """Main configuration class for MATLAB integration"""
    
    # MATLAB installation settings
    matlab_executable_path: Optional[str] = None
    matlab_version: Optional[str] = None
    required_toolboxes: List[str] = field(default_factory=lambda: [
        "Automated Driving Toolbox",
        "RoadRunner",
        "Simulink"
    ])
    
    # Component configurations
    export_config: ExportConfig = field(default_factory=ExportConfig)
    import_config: ImportConfig = field(default_factory=ImportConfig)
    simulink_config: SimulinkConfig = field(default_factory=SimulinkConfig)
    
    # Script generation settings
    generate_analysis_scripts: bool = True
    script_template_directory: str = "matlab_templates"
    include_documentation: bool = True
    
    # Automated Driving Toolbox settings
    adt_scenario_format: str = "drivingScenario"
    adt_coordinate_system: str = "ENU"  # East-North-Up
    adt_include_sensors: bool = False
    
    # RoadRunner integration settings
    roadrunner_project_path: Optional[str] = None
    roadrunner_asset_library: Optional[str] = None
    auto_generate_scenes: bool = False
    
    # Performance settings
    enable_parallel_processing: bool = False
    max_parallel_workers: int = 4
    memory_limit_gb: float = 8.0
    
    # Logging and debugging
    enable_debug_logging: bool = False
    log_file_path: str = "matlab_integration.log"
    save_intermediate_files: bool = False
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []
        
        # Check MATLAB executable
        if self.matlab_executable_path:
            matlab_path = Path(self.matlab_executable_path)
            if not matlab_path.exists():
                issues.append(f"MATLAB executable not found: {self.matlab_executable_path}")
        
        # Check output directories
        export_dir = Path(self.export_config.output_directory)
        if not export_dir.exists():
            try:
                export_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create export directory: {e}")
        
        # Check RoadRunner project path
        if self.roadrunner_project_path:
            rr_path = Path(self.roadrunner_project_path)
            if not rr_path.exists():
                issues.append(f"RoadRunner project path not found: {self.roadrunner_project_path}")
        
        # Validate network settings
        if self.simulink_config.port < 1024 or self.simulink_config.port > 65535:
            issues.append("Simulink port must be between 1024 and 65535")
        
        return issues
    
    def get_export_file_path(self, data_type: str, timestamp: Optional[str] = None) -> str:
        """Generate export file path for given data type"""
        from datetime import datetime
        
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"{self.export_config.file_prefix}_{data_type}_{timestamp}.mat"
        return str(Path(self.export_config.output_directory) / filename)