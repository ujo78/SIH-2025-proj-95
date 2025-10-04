"""
System Robustness Integration

This module integrates the performance optimizer and error handler with the
existing traffic simulation system, providing a unified interface for
robustness and optimization features.
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from contextlib import contextmanager

try:
    from panda3d.core import NodePath, Vec3, Point3
    PANDA3D_AVAILABLE = True
except ImportError:
    PANDA3D_AVAILABLE = False
    NodePath = Vec3 = Point3 = lambda *args: None

from .performance_optimizer import (
    PerformanceOptimizer, LODLevel, QualityLevel, PerformanceMetrics
)
from .error_handler import (
    ErrorHandler, ErrorCategory, ErrorSeverity, RecoveryAction
)
from indian_features.interfaces import Point3D
from indian_features.enums import VehicleType


@dataclass
class RobustnessConfig:
    """Configuration for system robustness features"""
    enable_performance_optimization: bool = True
    enable_error_handling: bool = True
    enable_adaptive_quality: bool = True
    target_fps: float = 60.0
    min_fps: float = 30.0
    max_visible_vehicles: int = 200
    auto_recovery: bool = True
    log_directory: str = "logs"
    snapshot_directory: str = "snapshots"


class SystemRobustnessManager:
    """
    Main manager for system robustness features including performance
    optimization and error handling.
    """
    
    def __init__(self, config: RobustnessConfig, render_root: Optional[NodePath] = None):
        """
        Initialize system robustness manager.
        
        Args:
            config: Robustness configuration
            render_root: Root node for rendering (optional)
        """
        self.config = config
        self.render_root = render_root
        
        # Initialize subsystems
        self.performance_optimizer = None
        self.error_handler = None
        
        if config.enable_performance_optimization:
            self.performance_optimizer = PerformanceOptimizer(render_root)
            self.performance_optimizer.target_fps = config.target_fps
            self.performance_optimizer.min_fps = config.min_fps
            self.performance_optimizer.max_visible_vehicles = config.max_visible_vehicles
            self.performance_optimizer.enable_adaptive_quality(config.enable_adaptive_quality)
        
        if config.enable_error_handling:
            self.error_handler = ErrorHandler(
                log_directory=config.log_directory,
                snapshot_directory=config.snapshot_directory
            )
            self.error_handler.auto_recovery_enabled = config.auto_recovery
        
        # System state
        self.is_running = False
        self.update_thread = None
        self.last_update_time = 0.0
        
        # Component registry for error handling
        self.registered_components: Dict[str, Any] = {}
        
        # Performance monitoring
        self.performance_history: List[PerformanceMetrics] = []
        self.max_history_length = 300  # 5 minutes at 1 FPS
        
        print("System robustness manager initialized")
    
    def start(self) -> None:
        """Start the robustness management system."""
        if self.is_running:
            return
        
        self.is_running = True
        self.last_update_time = time.time()
        
        # Start update thread
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        if self.error_handler:
            self.error_handler.logger.log_info("System robustness manager started", "RobustnessManager")
    
    def stop(self) -> None:
        """Stop the robustness management system."""
        self.is_running = False
        
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5.0)
        
        if self.error_handler:
            self.error_handler.logger.log_info("System robustness manager stopped", "RobustnessManager")
    
    def register_component(self, name: str, component: Any) -> None:
        """
        Register a system component for monitoring and error handling.
        
        Args:
            name: Component name
            component: Component instance
        """
        self.registered_components[name] = component
        
        if self.error_handler:
            self.error_handler.state_manager.register_component(name, component)
        
        print(f"Registered component: {name}")
    
    def register_vehicle_for_optimization(self, vehicle_id: int, position: Point3D,
                                        vehicle_type: VehicleType,
                                        node_paths: Optional[Dict[LODLevel, NodePath]] = None) -> None:
        """
        Register a vehicle for performance optimization.
        
        Args:
            vehicle_id: Unique vehicle identifier
            position: Vehicle position
            vehicle_type: Type of vehicle
            node_paths: LOD node paths (optional, will create defaults if None)
        """
        if not self.performance_optimizer:
            return
        
        # Create default node paths if not provided
        if node_paths is None:
            node_paths = self._create_default_lod_nodes(vehicle_id, vehicle_type)
        
        try:
            self.performance_optimizer.register_vehicle(vehicle_id, position, node_paths)
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    e, "PerformanceOptimizer", ErrorCategory.PERFORMANCE, ErrorSeverity.MEDIUM,
                    {'vehicle_id': vehicle_id, 'vehicle_type': vehicle_type.name}
                )
    
    def unregister_vehicle(self, vehicle_id: int) -> None:
        """
        Unregister a vehicle from optimization.
        
        Args:
            vehicle_id: Vehicle identifier
        """
        if self.performance_optimizer:
            try:
                self.performance_optimizer.unregister_vehicle(vehicle_id)
            except Exception as e:
                if self.error_handler:
                    self.error_handler.handle_error(
                        e, "PerformanceOptimizer", ErrorCategory.PERFORMANCE, ErrorSeverity.LOW,
                        {'vehicle_id': vehicle_id}
                    )
    
    def update_vehicle_position(self, vehicle_id: int, position: Point3D) -> None:
        """
        Update vehicle position for optimization.
        
        Args:
            vehicle_id: Vehicle identifier
            position: New position
        """
        if self.performance_optimizer:
            try:
                self.performance_optimizer.update_vehicle_position(vehicle_id, position)
            except Exception as e:
                if self.error_handler:
                    self.error_handler.handle_error(
                        e, "PerformanceOptimizer", ErrorCategory.PERFORMANCE, ErrorSeverity.LOW,
                        {'vehicle_id': vehicle_id, 'position': {'x': position.x, 'y': position.y, 'z': position.z}}
                    )
    
    def update_camera_position(self, position: Point3D, direction: Point3D) -> None:
        """
        Update camera position for optimization calculations.
        
        Args:
            position: Camera position
            direction: Camera direction
        """
        if self.performance_optimizer:
            try:
                self.performance_optimizer.update_camera_position(position, direction)
            except Exception as e:
                if self.error_handler:
                    self.error_handler.handle_error(
                        e, "PerformanceOptimizer", ErrorCategory.PERFORMANCE, ErrorSeverity.MEDIUM,
                        {'camera_position': {'x': position.x, 'y': position.y, 'z': position.z}}
                    )
    
    def set_quality_level(self, quality: QualityLevel) -> None:
        """
        Set rendering quality level.
        
        Args:
            quality: Target quality level
        """
        if self.performance_optimizer:
            try:
                self.performance_optimizer.set_quality_level(quality)
            except Exception as e:
                if self.error_handler:
                    self.error_handler.handle_error(
                        e, "PerformanceOptimizer", ErrorCategory.PERFORMANCE, ErrorSeverity.MEDIUM,
                        {'target_quality': quality.name}
                    )
    
    @contextmanager
    def error_context(self, component: str, category: ErrorCategory = ErrorCategory.SYSTEM):
        """
        Context manager for automatic error handling.
        
        Args:
            component: Component name
            category: Error category
        """
        try:
            yield
        except Exception as e:
            if self.error_handler:
                severity = self._determine_error_severity(e)
                self.error_handler.handle_error(e, component, category, severity)
            else:
                # Re-raise if no error handler
                raise
    
    def create_checkpoint(self) -> Optional[str]:
        """
        Create a system state checkpoint.
        
        Returns:
            Checkpoint ID if successful, None otherwise
        """
        if not self.error_handler:
            return None
        
        try:
            return self.error_handler.create_recovery_checkpoint()
        except Exception as e:
            print(f"Failed to create checkpoint: {e}")
            return None
    
    def restore_checkpoint(self, checkpoint_id: Optional[str] = None) -> bool:
        """
        Restore system from checkpoint.
        
        Args:
            checkpoint_id: Checkpoint to restore (latest if None)
            
        Returns:
            True if restoration was successful
        """
        if not self.error_handler:
            return False
        
        try:
            return self.error_handler.restore_from_checkpoint(checkpoint_id)
        except Exception as e:
            print(f"Failed to restore checkpoint: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        status = {
            'robustness_manager': {
                'running': self.is_running,
                'registered_components': list(self.registered_components.keys()),
                'config': {
                    'performance_optimization': self.config.enable_performance_optimization,
                    'error_handling': self.config.enable_error_handling,
                    'adaptive_quality': self.config.enable_adaptive_quality,
                    'auto_recovery': self.config.auto_recovery
                }
            }
        }
        
        # Add performance optimizer status
        if self.performance_optimizer:
            try:
                status['performance_optimizer'] = self.performance_optimizer.get_optimization_stats()
            except Exception as e:
                status['performance_optimizer'] = {'error': str(e)}
        
        # Add error handler status
        if self.error_handler:
            try:
                status['error_handler'] = {
                    'error_statistics': self.error_handler.get_error_statistics(),
                    'system_health': self.error_handler.check_system_health(time.time())
                }
            except Exception as e:
                status['error_handler'] = {'error': str(e)}
        
        return status
    
    def get_performance_metrics(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics."""
        if self.performance_optimizer:
            return self.performance_optimizer.get_performance_metrics()
        return None
    
    def get_performance_history(self) -> List[PerformanceMetrics]:
        """Get performance metrics history."""
        return self.performance_history.copy()
    
    def _update_loop(self) -> None:
        """Main update loop running in separate thread."""
        while self.is_running:
            try:
                current_time = time.time()
                delta_time = current_time - self.last_update_time
                
                # Update performance optimizer
                if self.performance_optimizer:
                    self.performance_optimizer.update_optimization(delta_time)
                    
                    # Collect performance metrics
                    metrics = self.performance_optimizer.get_performance_metrics()
                    self.performance_history.append(metrics)
                    
                    # Maintain history length
                    if len(self.performance_history) > self.max_history_length:
                        self.performance_history.pop(0)
                
                # Update error handler (health checks, cleanup, etc.)
                if self.error_handler:
                    self.error_handler.check_system_health(current_time)
                    self.error_handler.state_manager.auto_snapshot_check(current_time)
                
                self.last_update_time = current_time
                
                # Sleep for a short time to avoid excessive CPU usage
                time.sleep(0.1)  # 10 FPS update rate
                
            except Exception as e:
                # Handle errors in the update loop itself
                if self.error_handler:
                    self.error_handler.handle_error(
                        e, "RobustnessManager", ErrorCategory.SYSTEM, ErrorSeverity.HIGH
                    )
                else:
                    print(f"Error in robustness manager update loop: {e}")
                
                # Sleep longer on error to avoid rapid error loops
                time.sleep(1.0)
    
    def _create_default_lod_nodes(self, vehicle_id: int, 
                                 vehicle_type: VehicleType) -> Dict[LODLevel, NodePath]:
        """Create default LOD node paths for a vehicle."""
        if not PANDA3D_AVAILABLE:
            return {lod: None for lod in LODLevel}
        
        node_paths = {}
        
        # Create different LOD levels
        for lod_level in LODLevel:
            if lod_level == LODLevel.CULLED:
                node_paths[lod_level] = None
                continue
            
            # Create a simple node for each LOD level
            node_name = f"vehicle_{vehicle_id}_lod_{lod_level.name.lower()}"
            node_path = NodePath(node_name)
            
            # Set different scales for different LOD levels
            if lod_level == LODLevel.HIGH:
                scale = 1.0
            elif lod_level == LODLevel.MEDIUM:
                scale = 0.8
            else:  # LOW
                scale = 0.6
            
            node_path.setScale(scale)
            
            # Apply vehicle type specific properties
            self._apply_vehicle_type_properties(node_path, vehicle_type, lod_level)
            
            node_paths[lod_level] = node_path
        
        return node_paths
    
    def _apply_vehicle_type_properties(self, node_path: NodePath, 
                                     vehicle_type: VehicleType, lod_level: LODLevel) -> None:
        """Apply vehicle type specific properties to node."""
        if not PANDA3D_AVAILABLE:
            return
        
        # Set colors based on vehicle type
        if vehicle_type == VehicleType.AUTO_RICKSHAW:
            node_path.setColor(1.0, 1.0, 0.0, 1.0)  # Yellow
        elif vehicle_type == VehicleType.BUS:
            node_path.setColor(0.8, 0.0, 0.0, 1.0)  # Red
        elif vehicle_type == VehicleType.TRUCK:
            node_path.setColor(0.0, 0.5, 0.8, 1.0)  # Blue
        elif vehicle_type == VehicleType.MOTORCYCLE:
            node_path.setColor(0.2, 0.2, 0.2, 1.0)  # Dark gray
        else:  # CAR
            node_path.setColor(0.5, 0.5, 0.5, 1.0)  # Gray
        
        # Adjust transparency for lower LOD levels
        if lod_level == LODLevel.LOW:
            current_color = node_path.getColor()
            node_path.setColor(current_color[0], current_color[1], current_color[2], 0.8)
    
    def _determine_error_severity(self, exception: Exception) -> ErrorSeverity:
        """Determine error severity based on exception type."""
        if isinstance(exception, (MemoryError, SystemError)):
            return ErrorSeverity.CRITICAL
        elif isinstance(exception, (RuntimeError, ValueError, TypeError)):
            return ErrorSeverity.HIGH
        elif isinstance(exception, (FileNotFoundError, ImportError)):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW


# Convenience functions for easy integration

def create_robustness_manager(render_root: Optional[NodePath] = None,
                            **config_kwargs) -> SystemRobustnessManager:
    """
    Create a system robustness manager with default configuration.
    
    Args:
        render_root: Root node for rendering
        **config_kwargs: Configuration overrides
        
    Returns:
        Configured robustness manager
    """
    config = RobustnessConfig(**config_kwargs)
    return SystemRobustnessManager(config, render_root)


def with_error_handling(component_name: str, robustness_manager: SystemRobustnessManager,
                       category: ErrorCategory = ErrorCategory.SYSTEM):
    """
    Decorator for automatic error handling.
    
    Args:
        component_name: Name of the component
        robustness_manager: Robustness manager instance
        category: Error category
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with robustness_manager.error_context(component_name, category):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Integration helper for existing systems
class RobustnessIntegrationHelper:
    """
    Helper class to integrate robustness features into existing systems.
    """
    
    @staticmethod
    def integrate_with_vehicle_asset_manager(asset_manager, robustness_manager: SystemRobustnessManager):
        """Integrate robustness features with VehicleAssetManager."""
        # Register the asset manager
        robustness_manager.register_component("VehicleAssetManager", asset_manager)
        
        # Wrap critical methods with error handling
        original_create_vehicle = asset_manager.create_vehicle_instance
        
        def safe_create_vehicle(vehicle):
            with robustness_manager.error_context("VehicleAssetManager", ErrorCategory.ASSET_LOADING):
                return original_create_vehicle(vehicle)
        
        asset_manager.create_vehicle_instance = safe_create_vehicle
    
    @staticmethod
    def integrate_with_traffic_flow_visualizer(visualizer, robustness_manager: SystemRobustnessManager):
        """Integrate robustness features with TrafficFlowVisualizer."""
        # Register the visualizer
        robustness_manager.register_component("TrafficFlowVisualizer", visualizer)
        
        # Wrap update methods with error handling
        original_update_density = visualizer.update_traffic_density
        
        def safe_update_density(edge_densities):
            with robustness_manager.error_context("TrafficFlowVisualizer", ErrorCategory.VISUALIZATION):
                return original_update_density(edge_densities)
        
        visualizer.update_traffic_density = safe_update_density
    
    @staticmethod
    def integrate_with_traffic_model(traffic_model, robustness_manager: SystemRobustnessManager):
        """Integrate robustness features with TrafficModel."""
        # Register the traffic model
        robustness_manager.register_component("TrafficModel", traffic_model)
        
        # Add vehicle registration for optimization
        if hasattr(traffic_model, 'indian_vehicles'):
            for vid, indian_vehicle in traffic_model.indian_vehicles.items():
                robustness_manager.register_vehicle_for_optimization(
                    vid, indian_vehicle.position, indian_vehicle.vehicle_type
                )