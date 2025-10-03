"""
Configuration Classes for Enhanced Visualization

This module defines configuration classes for 3D rendering, asset management,
and visualization performance settings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

from indian_features.enums import VehicleType, WeatherType, RoadQuality


@dataclass
class RenderingConfig:
    """Configuration for 3D rendering settings"""
    
    # Display settings
    window_width: int = 1920
    window_height: int = 1080
    fullscreen: bool = False
    vsync: bool = True
    
    # Rendering quality
    anti_aliasing: int = 4  # MSAA samples
    anisotropic_filtering: int = 16
    shadow_quality: str = "high"  # "low", "medium", "high", "ultra"
    texture_quality: str = "high"
    
    # Performance settings
    target_fps: int = 60
    max_draw_distance: float = 5000.0  # meters
    lod_distances: List[float] = field(default_factory=lambda: [100.0, 500.0, 1000.0, 2000.0])
    
    # Lighting settings
    enable_dynamic_lighting: bool = True
    shadow_map_size: int = 2048
    ambient_light_intensity: float = 0.3
    sun_light_intensity: float = 0.8
    
    # Weather effects
    enable_weather_effects: bool = True
    particle_density: int = 1000
    fog_density_range: Tuple[float, float] = (0.0, 0.1)
    
    # Post-processing effects
    enable_bloom: bool = True
    enable_motion_blur: bool = False
    enable_depth_of_field: bool = False
    color_correction: bool = True


@dataclass
class AssetConfig:
    """Configuration for 3D asset management"""
    
    # Asset directories
    models_directory: str = "assets/models"
    textures_directory: str = "assets/textures"
    sounds_directory: str = "assets/sounds"
    
    # Vehicle model settings
    vehicle_model_paths: Dict[VehicleType, str] = field(default_factory=lambda: {
        VehicleType.CAR: "vehicles/indian_car.egg",
        VehicleType.BUS: "vehicles/indian_bus.egg",
        VehicleType.AUTO_RICKSHAW: "vehicles/auto_rickshaw.egg",
        VehicleType.MOTORCYCLE: "vehicles/motorcycle.egg",
        VehicleType.TRUCK: "vehicles/indian_truck.egg",
        VehicleType.BICYCLE: "vehicles/bicycle.egg"
    })
    
    # Vehicle scaling factors
    vehicle_scales: Dict[VehicleType, float] = field(default_factory=lambda: {
        VehicleType.CAR: 1.0,
        VehicleType.BUS: 1.0,
        VehicleType.AUTO_RICKSHAW: 1.0,
        VehicleType.MOTORCYCLE: 1.0,
        VehicleType.TRUCK: 1.0,
        VehicleType.BICYCLE: 1.0
    })
    
    # Building assets
    building_model_library: str = "buildings/indian_buildings"
    building_texture_library: str = "textures/building_textures"
    
    # Road infrastructure assets
    road_texture_paths: Dict[RoadQuality, str] = field(default_factory=lambda: {
        RoadQuality.EXCELLENT: "roads/asphalt_new.jpg",
        RoadQuality.GOOD: "roads/asphalt_good.jpg",
        RoadQuality.POOR: "roads/asphalt_worn.jpg",
        RoadQuality.VERY_POOR: "roads/asphalt_damaged.jpg"
    })
    
    pothole_model_path: str = "roads/pothole.egg"
    construction_barrier_path: str = "infrastructure/construction_barrier.egg"
    traffic_sign_library: str = "signs/indian_traffic_signs"
    
    # Environment assets
    tree_models: List[str] = field(default_factory=lambda: [
        "environment/palm_tree.egg",
        "environment/banyan_tree.egg",
        "environment/neem_tree.egg"
    ])
    
    street_furniture: Dict[str, str] = field(default_factory=lambda: {
        "street_light": "infrastructure/street_light.egg",
        "bus_stop": "infrastructure/bus_stop.egg",
        "traffic_light": "infrastructure/traffic_light.egg",
        "auto_stand": "infrastructure/auto_stand.egg"
    })
    
    # Asset loading settings
    preload_all_assets: bool = False
    asset_cache_size_mb: int = 512
    compress_textures: bool = True
    generate_mipmaps: bool = True


@dataclass
class CameraConfig:
    """Configuration for camera controls and presets"""
    
    # Default camera settings
    default_position: Tuple[float, float, float] = (0.0, -100.0, 50.0)
    default_target: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    field_of_view: float = 60.0  # degrees
    near_plane: float = 1.0
    far_plane: float = 10000.0
    
    # Movement settings
    movement_speed: float = 50.0  # units per second
    rotation_speed: float = 90.0  # degrees per second
    zoom_speed: float = 10.0
    smooth_movement: bool = True
    
    # Follow camera settings
    follow_distance: float = 20.0
    follow_height: float = 10.0
    follow_smoothing: float = 0.1
    
    # Preset camera positions
    camera_presets: Dict[str, Dict[str, Tuple[float, float, float]]] = field(default_factory=lambda: {
        "overview": {
            "position": (0.0, -200.0, 150.0),
            "target": (0.0, 0.0, 0.0)
        },
        "intersection": {
            "position": (50.0, -50.0, 30.0),
            "target": (0.0, 0.0, 0.0)
        },
        "street_level": {
            "position": (10.0, -10.0, 5.0),
            "target": (0.0, 0.0, 0.0)
        },
        "aerial": {
            "position": (0.0, -500.0, 300.0),
            "target": (0.0, 0.0, 0.0)
        }
    })
    
    # Cinematic settings
    enable_cinematic_mode: bool = False
    cinematic_speed_multiplier: float = 0.5
    auto_focus: bool = True


@dataclass
class UIConfig:
    """Configuration for user interface elements"""
    
    # UI layout settings
    show_fps_counter: bool = True
    show_simulation_stats: bool = True
    show_minimap: bool = True
    ui_scale: float = 1.0
    
    # Control panel settings
    control_panel_width: int = 300
    control_panel_position: str = "right"  # "left", "right", "bottom"
    collapsible_panels: bool = True
    
    # Information display
    vehicle_info_on_hover: bool = True
    road_info_on_click: bool = True
    show_tooltips: bool = True
    tooltip_delay: float = 0.5  # seconds
    
    # Color schemes for traffic visualization
    traffic_density_colors: Dict[str, Tuple[float, float, float]] = field(default_factory=lambda: {
        "free_flow": (0.0, 1.0, 0.0),      # Green
        "light_traffic": (0.5, 1.0, 0.0),  # Yellow-green
        "moderate_traffic": (1.0, 1.0, 0.0), # Yellow
        "heavy_traffic": (1.0, 0.5, 0.0),  # Orange
        "congested": (1.0, 0.0, 0.0)       # Red
    })
    
    # Emergency alert colors
    emergency_colors: Dict[str, Tuple[float, float, float]] = field(default_factory=lambda: {
        "accident": (1.0, 0.0, 0.0),       # Red
        "flooding": (0.0, 0.0, 1.0),       # Blue
        "construction": (1.0, 0.5, 0.0),   # Orange
        "closure": (0.5, 0.0, 0.5)         # Purple
    })
    
    # Font settings
    font_family: str = "arial"
    font_size: int = 12
    ui_font_size: int = 10


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization"""
    
    # Level of detail settings
    enable_lod: bool = True
    vehicle_lod_distances: List[float] = field(default_factory=lambda: [50.0, 150.0, 500.0])
    building_lod_distances: List[float] = field(default_factory=lambda: [100.0, 300.0, 1000.0])
    
    # Culling settings
    enable_frustum_culling: bool = True
    enable_occlusion_culling: bool = False
    culling_margin: float = 10.0  # meters
    
    # Batching and instancing
    enable_batching: bool = True
    max_batch_size: int = 100
    enable_instancing: bool = True
    
    # Memory management
    texture_memory_limit_mb: int = 1024
    geometry_memory_limit_mb: int = 512
    auto_garbage_collection: bool = True
    gc_interval: float = 30.0  # seconds
    
    # Threading settings
    enable_multithreading: bool = True
    max_worker_threads: int = 4
    async_asset_loading: bool = True
    
    # Quality scaling
    auto_quality_scaling: bool = True
    min_fps_threshold: int = 30
    quality_scale_factor: float = 0.8


@dataclass
class VisualizationConfig:
    """Main configuration class for enhanced visualization"""
    
    # Component configurations
    rendering_config: RenderingConfig = field(default_factory=RenderingConfig)
    asset_config: AssetConfig = field(default_factory=AssetConfig)
    camera_config: CameraConfig = field(default_factory=CameraConfig)
    ui_config: UIConfig = field(default_factory=UIConfig)
    performance_config: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Scene settings
    scene_bounds: Tuple[float, float, float, float] = (-1000.0, -1000.0, 1000.0, 1000.0)  # min_x, min_y, max_x, max_y
    coordinate_system: str = "utm"
    up_axis: str = "z"  # "y" or "z"
    
    # Simulation integration
    real_time_updates: bool = True
    update_frequency: float = 30.0  # Hz
    interpolate_movement: bool = True
    
    # Recording and export
    enable_recording: bool = False
    recording_format: str = "mp4"
    recording_quality: str = "high"
    screenshot_format: str = "png"
    
    def validate_configuration(self) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []
        
        # Check asset directories
        for directory in [self.asset_config.models_directory, 
                         self.asset_config.textures_directory,
                         self.asset_config.sounds_directory]:
            if not Path(directory).exists():
                issues.append(f"Asset directory not found: {directory}")
        
        # Check performance settings
        if self.performance_config.max_worker_threads < 1:
            issues.append("max_worker_threads must be at least 1")
        
        if self.rendering_config.target_fps < 1:
            issues.append("target_fps must be at least 1")
        
        # Check memory limits
        total_memory = (self.performance_config.texture_memory_limit_mb + 
                       self.performance_config.geometry_memory_limit_mb)
        if total_memory > 4096:  # 4GB warning
            issues.append(f"Total memory limit ({total_memory}MB) may be too high")
        
        return issues