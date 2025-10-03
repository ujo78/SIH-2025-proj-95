"""
MATLAB Integration Module for Indian Traffic Digital Twin

This module provides comprehensive MATLAB integration capabilities including:
- Data export to MATLAB formats
- RoadRunner scene import and conversion
- Real-time Simulink connectivity
- Automated analysis script generation
- Automated Driving Toolbox integration
"""

from .config import (
    MATLABConfig,
    ExportConfig,
    ImportConfig,
    SimulinkConfig
)

from .interfaces import (
    MATLABExporterInterface,
    RoadRunnerImporterInterface,
    SimulinkConnectorInterface,
    AutomatedDrivingToolboxInterface,
    MATLABDataFormat,
    RoadRunnerScene
)

from .matlab_data_exporter import MATLABDataExporter
from .roadrunner_importer import RoadRunnerImporter
from .simulink_connector import SimulinkConnector
from .script_generator import MATLABScriptGenerator

# Import Automated Driving Toolbox integration if available
try:
    from .automated_driving_toolbox import AutomatedDrivingToolboxExporter
    ADT_AVAILABLE = True
except ImportError:
    ADT_AVAILABLE = False

__version__ = "1.0.0"
__author__ = "Indian Traffic Digital Twin Team"

__all__ = [
    # Configuration classes
    'MATLABConfig',
    'ExportConfig', 
    'ImportConfig',
    'SimulinkConfig',
    
    # Interface classes
    'MATLABExporterInterface',
    'RoadRunnerImporterInterface', 
    'SimulinkConnectorInterface',
    'AutomatedDrivingToolboxInterface',
    'MATLABDataFormat',
    'RoadRunnerScene',
    
    # Implementation classes
    'MATLABDataExporter',
    'RoadRunnerImporter',
    'SimulinkConnector',
    'MATLABScriptGenerator',
    
    # Optional components
    'AutomatedDrivingToolboxExporter' if ADT_AVAILABLE else None,
    
    # Utility functions
    'create_default_config',
    'validate_matlab_installation',
    'get_integration_status'
]

# Remove None values from __all__
__all__ = [item for item in __all__ if item is not None]


def create_default_config() -> MATLABConfig:
    """Create a default MATLAB integration configuration"""
    return MATLABConfig()


def validate_matlab_installation() -> dict:
    """Validate MATLAB installation and available toolboxes"""
    status = {
        'matlab_available': False,
        'scipy_available': False,
        'toolboxes': [],
        'issues': []
    }
    
    # Check scipy availability
    try:
        import scipy
        status['scipy_available'] = True
    except ImportError:
        status['issues'].append("scipy not available - .mat file export will use JSON format")
    
    # Check MATLAB availability (basic check)
    import shutil
    matlab_exe = shutil.which('matlab')
    if matlab_exe:
        status['matlab_available'] = True
        status['matlab_path'] = matlab_exe
    else:
        status['issues'].append("MATLAB executable not found in PATH")
    
    # Check for common toolboxes (would require MATLAB engine for full check)
    # This is a simplified check
    status['toolboxes'] = [
        'Core MATLAB',  # Always available if MATLAB is installed
    ]
    
    return status


def get_integration_status() -> dict:
    """Get current integration system status"""
    status = validate_matlab_installation()
    
    # Add component availability
    status['components'] = {
        'data_exporter': True,
        'roadrunner_importer': True,
        'simulink_connector': True,
        'script_generator': True,
        'automated_driving_toolbox': ADT_AVAILABLE
    }
    
    # Add version information
    status['version'] = __version__
    
    return status


# Convenience function for quick setup
def setup_matlab_integration(config_overrides: dict = None) -> dict:
    """
    Quick setup function for MATLAB integration
    
    Args:
        config_overrides: Dictionary of configuration overrides
        
    Returns:
        Dictionary containing initialized components
    """
    # Create configuration
    config = create_default_config()
    
    # Apply overrides if provided
    if config_overrides:
        for key, value in config_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    # Initialize components
    components = {
        'config': config,
        'exporter': MATLABDataExporter(config),
        'importer': RoadRunnerImporter(config),
        'connector': SimulinkConnector(config),
        'script_generator': MATLABScriptGenerator(config)
    }
    
    # Add ADT exporter if available
    if ADT_AVAILABLE:
        components['adt_exporter'] = AutomatedDrivingToolboxExporter(config)
    
    return components


# Example usage function
def example_usage():
    """
    Example usage of the MATLAB integration system
    """
    print("MATLAB Integration Example Usage")
    print("=" * 40)
    
    # Check system status
    status = get_integration_status()
    print(f"MATLAB Available: {status['matlab_available']}")
    print(f"SciPy Available: {status['scipy_available']}")
    print(f"Version: {status['version']}")
    
    # Setup integration
    components = setup_matlab_integration({
        'export_config.output_directory': 'example_exports'
    })
    
    print("\nInitialized Components:")
    for name, component in components.items():
        print(f"  {name}: {type(component).__name__}")
    
    # Example workflow
    print("\nExample Workflow:")
    print("1. Export simulation data:")
    print("   exporter.export_vehicle_trajectories(trajectories)")
    print("   exporter.export_road_network(graph)")
    
    print("2. Generate analysis script:")
    print("   script_generator.generate_traffic_analysis_script(files, 'comprehensive')")
    
    print("3. Import RoadRunner scene:")
    print("   scene = importer.import_scene_file('scene.rrscene')")
    
    print("4. Real-time Simulink integration:")
    print("   connector.establish_connection('model_name')")
    print("   connector.send_real_time_data(data)")


if __name__ == "__main__":
    example_usage()