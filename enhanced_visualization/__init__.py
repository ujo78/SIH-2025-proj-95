"""
Enhanced Visualization Module

This module provides 3D visualization capabilities for Indian traffic simulation
including city rendering, vehicle asset management, traffic flow visualization,
camera controls, and UI overlays.
"""

from .interfaces import (
    CityRendererInterface,
    VehicleAssetInterface,
    TrafficVisualizerInterface,
    CameraControlInterface,
    UIOverlayInterface,
    BuildingInfo,
    RoadSegmentVisual,
    VehicleVisual
)

from .config import (
    VisualizationConfig,
    RenderingConfig,
    AssetConfig,
    CameraConfig,
    UIConfig,
    PerformanceConfig
)

# Import implementations only if Panda3D is available
try:
    from .city_renderer import IndianCityRenderer
    from .vehicle_asset_manager import VehicleAssetManager
    from .traffic_flow_visualizer import TrafficFlowVisualizer
    from .camera_controller import CameraController
    from .ui_overlay import UIOverlay
    
    PANDA3D_AVAILABLE = True
except ImportError:
    # Panda3D not available - provide mock implementations or None
    IndianCityRenderer = None
    VehicleAssetManager = None
    TrafficFlowVisualizer = None
    CameraController = None
    UIOverlay = None
    
    PANDA3D_AVAILABLE = False

__all__ = [
    # Interfaces
    'CityRendererInterface',
    'VehicleAssetInterface', 
    'TrafficVisualizerInterface',
    'CameraControlInterface',
    'UIOverlayInterface',
    'BuildingInfo',
    'RoadSegmentVisual',
    'VehicleVisual',
    
    # Configuration
    'VisualizationConfig',
    'RenderingConfig',
    'AssetConfig',
    'CameraConfig',
    'UIConfig',
    'PerformanceConfig',
    
    # Implementations (may be None if Panda3D not available)
    'IndianCityRenderer',
    'VehicleAssetManager',
    'TrafficFlowVisualizer',
    'CameraController',
    'UIOverlay',
    
    # Utility
    'PANDA3D_AVAILABLE'
]

def create_visualization_system(config: VisualizationConfig, render_root=None, camera_node=None, aspect2d=None):
    """
    Create a complete visualization system with all components.
    
    Args:
        config: Visualization configuration
        render_root: Panda3D render root node (optional)
        camera_node: Panda3D camera node (optional)
        aspect2d: Panda3D aspect2d node for UI (optional)
    
    Returns:
        Dictionary containing all visualization components, or None if Panda3D unavailable
    """
    if not PANDA3D_AVAILABLE:
        print("Panda3D not available - cannot create visualization system")
        return None
    
    try:
        # Create all visualization components
        city_renderer = IndianCityRenderer(config, render_root)
        vehicle_manager = VehicleAssetManager(config, render_root)
        traffic_visualizer = TrafficFlowVisualizer(config, render_root)
        camera_controller = CameraController(config, camera_node)
        ui_overlay = UIOverlay(config, aspect2d)
        
        # Load vehicle models
        vehicle_manager.load_vehicle_models()
        
        return {
            'city_renderer': city_renderer,
            'vehicle_manager': vehicle_manager,
            'traffic_visualizer': traffic_visualizer,
            'camera_controller': camera_controller,
            'ui_overlay': ui_overlay,
            'config': config
        }
        
    except Exception as e:
        print(f"Error creating visualization system: {e}")
        return None

def get_default_config() -> VisualizationConfig:
    """Get default visualization configuration."""
    return VisualizationConfig()