"""
Error Handler and Recovery System

This module implements comprehensive error handling and recovery mechanisms
for the traffic simulation system, including graceful degradation, fallback
mechanisms, robust logging, and simulation state recovery.
"""

import os
import sys
import json
import pickle
import traceback
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import weakref
from collections import defaultdict

try:
    from panda3d.core import NodePath, Texture, Material
    PANDA3D_AVAILABLE = True
except ImportError:
    PANDA3D_AVAILABLE = False
    # Mock classes for development without Panda3D
    class NodePath:
        def __init__(self, *args): pass
        def removeNode(self): pass
    
    Texture = Material = lambda *args: None

from indian_features.interfaces import Point3D
from indian_features.enums import VehicleType, EmergencyType


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = 1       # Minor issues, system continues normally
    MEDIUM = 2    # Moderate issues, some features may be disabled
    HIGH = 3      # Serious issues, significant degradation
    CRITICAL = 4  # Critical issues, system may need restart


class ErrorCategory(Enum):
    """Error categories for classification"""
    VISUALIZATION = "visualization"
    SIMULATION = "simulation"
    ASSET_LOADING = "asset_loading"
    NETWORK = "network"
    MEMORY = "memory"
    PERFORMANCE = "performance"
    USER_INPUT = "user_input"
    SYSTEM = "system"


class RecoveryAction(Enum):
    """Available recovery actions"""
    IGNORE = "ignore"
    RETRY = "retry"
    FALLBACK = "fallback"
    RESTART_COMPONENT = "restart_component"
    RESTART_SYSTEM = "restart_system"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"


@dataclass
class ErrorReport:
    """Comprehensive error report"""
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    component: str
    error_type: str
    message: str
    traceback_info: str
    context: Dict[str, Any] = field(default_factory=dict)
    recovery_action: Optional[RecoveryAction] = None
    recovery_successful: bool = False
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class SystemState:
    """System state snapshot for recovery"""
    timestamp: datetime
    simulation_time: float
    vehicle_count: int
    active_emergencies: List[str]
    weather_conditions: Dict[str, Any]
    camera_position: Dict[str, float]
    quality_settings: Dict[str, Any]
    performance_metrics: Dict[str, float]
    custom_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackAsset:
    """Fallback asset information"""
    asset_type: str
    original_path: str
    fallback_path: Optional[str]
    fallback_generator: Optional[Callable] = None
    is_procedural: bool = False


class ErrorLogger:
    """
    Advanced logging system with multiple output formats and rotation.
    """
    
    def __init__(self, log_directory: str = "logs"):
        """
        Initialize error logger.
        
        Args:
            log_directory: Directory to store log files
        """
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger("TrafficSimulation")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = self.log_directory / f"traffic_sim_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Error-specific file handler
        error_file = self.log_directory / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
        
        # JSON log handler for structured logging
        json_file = self.log_directory / f"structured_{datetime.now().strftime('%Y%m%d')}.json"
        self.json_log_file = open(json_file, 'a', encoding='utf-8')
        
        self.logger.info("Error logging system initialized")
    
    def log_error(self, error_report: ErrorReport) -> None:
        """Log an error report in multiple formats."""
        # Standard logging
        log_message = (
            f"[{error_report.category.value}] {error_report.component}: "
            f"{error_report.message}"
        )
        
        if error_report.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_report.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_report.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Detailed logging for higher severity
        if error_report.severity.value >= ErrorSeverity.MEDIUM.value:
            self.logger.debug(f"Error details: {error_report.traceback_info}")
            self.logger.debug(f"Context: {error_report.context}")
        
        # JSON structured logging
        json_entry = {
            "timestamp": error_report.timestamp.isoformat(),
            "error_id": error_report.error_id,
            "category": error_report.category.value,
            "severity": error_report.severity.name,
            "component": error_report.component,
            "error_type": error_report.error_type,
            "message": error_report.message,
            "context": error_report.context,
            "recovery_action": error_report.recovery_action.value if error_report.recovery_action else None,
            "recovery_successful": error_report.recovery_successful,
            "retry_count": error_report.retry_count
        }
        
        self.json_log_file.write(json.dumps(json_entry) + '\n')
        self.json_log_file.flush()
    
    def log_info(self, message: str, component: str = "System") -> None:
        """Log informational message."""
        self.logger.info(f"[{component}] {message}")
    
    def log_warning(self, message: str, component: str = "System") -> None:
        """Log warning message."""
        self.logger.warning(f"[{component}] {message}")
    
    def close(self) -> None:
        """Close logging resources."""
        if hasattr(self, 'json_log_file') and self.json_log_file:
            self.json_log_file.close()


class AssetFallbackManager:
    """
    Manages fallback assets and procedural generation for missing resources.
    """
    
    def __init__(self):
        """Initialize asset fallback manager."""
        self.fallback_assets: Dict[str, FallbackAsset] = {}
        self.asset_cache: Dict[str, Any] = {}
        self.procedural_generators: Dict[str, Callable] = {}
        
        # Register default fallback generators
        self._register_default_generators()
    
    def register_fallback(self, asset_type: str, original_path: str, 
                         fallback_path: Optional[str] = None,
                         fallback_generator: Optional[Callable] = None) -> None:
        """
        Register a fallback asset.
        
        Args:
            asset_type: Type of asset (e.g., "vehicle_model", "texture")
            original_path: Original asset path that might fail
            fallback_path: Path to fallback asset
            fallback_generator: Function to generate fallback procedurally
        """
        self.fallback_assets[original_path] = FallbackAsset(
            asset_type=asset_type,
            original_path=original_path,
            fallback_path=fallback_path,
            fallback_generator=fallback_generator,
            is_procedural=fallback_generator is not None
        )
    
    def get_fallback_asset(self, original_path: str) -> Optional[Any]:
        """
        Get fallback asset for a failed original asset.
        
        Args:
            original_path: Path of the original asset that failed
            
        Returns:
            Fallback asset or None if no fallback available
        """
        if original_path in self.asset_cache:
            return self.asset_cache[original_path]
        
        if original_path not in self.fallback_assets:
            # Try to find a generic fallback based on file extension
            fallback = self._find_generic_fallback(original_path)
            if not fallback:
                return None
        else:
            fallback = self.fallback_assets[original_path]
        
        # Try fallback file first
        if fallback.fallback_path and os.path.exists(fallback.fallback_path):
            try:
                # Load fallback asset (implementation depends on asset type)
                asset = self._load_asset(fallback.fallback_path, fallback.asset_type)
                self.asset_cache[original_path] = asset
                return asset
            except Exception as e:
                print(f"Failed to load fallback asset {fallback.fallback_path}: {e}")
        
        # Try procedural generation
        if fallback.fallback_generator:
            try:
                asset = fallback.fallback_generator()
                self.asset_cache[original_path] = asset
                return asset
            except Exception as e:
                print(f"Failed to generate procedural fallback for {original_path}: {e}")
        
        return None
    
    def _register_default_generators(self) -> None:
        """Register default procedural asset generators."""
        self.procedural_generators.update({
            "vehicle_model": self._generate_simple_vehicle_model,
            "texture": self._generate_simple_texture,
            "material": self._generate_simple_material,
            "road_segment": self._generate_simple_road_segment
        })
    
    def _find_generic_fallback(self, original_path: str) -> Optional[FallbackAsset]:
        """Find generic fallback based on file type."""
        path = Path(original_path)
        extension = path.suffix.lower()
        
        # Map extensions to asset types
        extension_map = {
            '.egg': 'vehicle_model',
            '.bam': 'vehicle_model',
            '.obj': 'vehicle_model',
            '.png': 'texture',
            '.jpg': 'texture',
            '.jpeg': 'texture',
            '.tga': 'texture'
        }
        
        asset_type = extension_map.get(extension)
        if asset_type and asset_type in self.procedural_generators:
            return FallbackAsset(
                asset_type=asset_type,
                original_path=original_path,
                fallback_path=None,
                fallback_generator=self.procedural_generators[asset_type],
                is_procedural=True
            )
        
        return None
    
    def _load_asset(self, path: str, asset_type: str) -> Any:
        """Load asset based on type."""
        if not PANDA3D_AVAILABLE:
            return f"mock_asset_{asset_type}"
        
        # Implementation would depend on Panda3D asset loading
        # This is a simplified version
        if asset_type == "vehicle_model":
            # Would use loader.loadModel(path)
            return NodePath(f"fallback_model_{Path(path).stem}")
        elif asset_type == "texture":
            # Would use loader.loadTexture(path)
            return f"fallback_texture_{Path(path).stem}"
        
        return None
    
    def _generate_simple_vehicle_model(self) -> Any:
        """Generate a simple procedural vehicle model."""
        if not PANDA3D_AVAILABLE:
            return "mock_procedural_vehicle"
        
        # Create a simple box as vehicle model
        model_node = NodePath("procedural_vehicle")
        # In full implementation, would create actual geometry
        return model_node
    
    def _generate_simple_texture(self) -> Any:
        """Generate a simple procedural texture."""
        if not PANDA3D_AVAILABLE:
            return "mock_procedural_texture"
        
        # In full implementation, would create a simple colored texture
        return "procedural_texture"
    
    def _generate_simple_material(self) -> Any:
        """Generate a simple procedural material."""
        if not PANDA3D_AVAILABLE:
            return "mock_procedural_material"
        
        # In full implementation, would create a basic material
        return "procedural_material"
    
    def _generate_simple_road_segment(self) -> Any:
        """Generate a simple procedural road segment."""
        if not PANDA3D_AVAILABLE:
            return "mock_procedural_road"
        
        # In full implementation, would create road geometry
        return "procedural_road"


class StateManager:
    """
    Manages system state snapshots for recovery purposes.
    """
    
    def __init__(self, max_snapshots: int = 10, snapshot_directory: str = "snapshots"):
        """
        Initialize state manager.
        
        Args:
            max_snapshots: Maximum number of snapshots to keep
            snapshot_directory: Directory to store state snapshots
        """
        self.max_snapshots = max_snapshots
        self.snapshot_directory = Path(snapshot_directory)
        self.snapshot_directory.mkdir(exist_ok=True)
        
        self.snapshots: List[SystemState] = []
        self.auto_snapshot_interval = 60.0  # seconds
        self.last_auto_snapshot = 0.0
        
        # Weak references to system components for state capture
        self.component_refs: Dict[str, Any] = {}
    
    def register_component(self, name: str, component: Any) -> None:
        """
        Register a system component for state capture.
        
        Args:
            name: Component name
            component: Component instance
        """
        self.component_refs[name] = weakref.ref(component)
    
    def create_snapshot(self, custom_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a system state snapshot.
        
        Args:
            custom_data: Additional custom data to include
            
        Returns:
            Snapshot ID
        """
        timestamp = datetime.now()
        
        # Gather state from registered components
        state_data = self._gather_component_states()
        
        # Create state snapshot
        snapshot = SystemState(
            timestamp=timestamp,
            simulation_time=state_data.get('simulation_time', 0.0),
            vehicle_count=state_data.get('vehicle_count', 0),
            active_emergencies=state_data.get('active_emergencies', []),
            weather_conditions=state_data.get('weather_conditions', {}),
            camera_position=state_data.get('camera_position', {'x': 0, 'y': 0, 'z': 0}),
            quality_settings=state_data.get('quality_settings', {}),
            performance_metrics=state_data.get('performance_metrics', {}),
            custom_data=custom_data or {}
        )
        
        # Add to snapshots list
        self.snapshots.append(snapshot)
        
        # Maintain snapshot limit
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)
        
        # Save to disk
        snapshot_id = f"snapshot_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        self._save_snapshot_to_disk(snapshot, snapshot_id)
        
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: Optional[str] = None) -> bool:
        """
        Restore system state from a snapshot.
        
        Args:
            snapshot_id: ID of snapshot to restore (latest if None)
            
        Returns:
            True if restoration was successful
        """
        if not self.snapshots:
            return False
        
        # Find snapshot
        if snapshot_id:
            snapshot = self._find_snapshot_by_id(snapshot_id)
        else:
            snapshot = self.snapshots[-1]  # Latest snapshot
        
        if not snapshot:
            return False
        
        try:
            # Restore component states
            self._restore_component_states(snapshot)
            return True
            
        except Exception as e:
            print(f"Failed to restore snapshot: {e}")
            return False
    
    def get_available_snapshots(self) -> List[Dict[str, Any]]:
        """Get list of available snapshots."""
        return [
            {
                'timestamp': snapshot.timestamp.isoformat(),
                'simulation_time': snapshot.simulation_time,
                'vehicle_count': snapshot.vehicle_count,
                'active_emergencies': len(snapshot.active_emergencies)
            }
            for snapshot in self.snapshots
        ]
    
    def auto_snapshot_check(self, current_time: float) -> None:
        """Check if automatic snapshot should be created."""
        if current_time - self.last_auto_snapshot >= self.auto_snapshot_interval:
            self.create_snapshot({'auto_generated': True})
            self.last_auto_snapshot = current_time
    
    def _gather_component_states(self) -> Dict[str, Any]:
        """Gather state data from registered components."""
        state_data = {}
        
        for name, component_ref in self.component_refs.items():
            component = component_ref()
            if component is None:
                continue
            
            try:
                # Try to get state from component
                if hasattr(component, 'get_state'):
                    state_data[name] = component.get_state()
                elif hasattr(component, '__dict__'):
                    # Fallback: serialize component attributes
                    state_data[name] = self._serialize_component_state(component)
            except Exception as e:
                print(f"Failed to gather state from component {name}: {e}")
        
        return state_data
    
    def _serialize_component_state(self, component: Any) -> Dict[str, Any]:
        """Serialize component state to dictionary."""
        state = {}
        
        for attr_name, attr_value in component.__dict__.items():
            if attr_name.startswith('_'):
                continue  # Skip private attributes
            
            try:
                # Only serialize basic types and collections
                if isinstance(attr_value, (int, float, str, bool, list, dict, tuple)):
                    state[attr_name] = attr_value
                elif hasattr(attr_value, '__dict__'):
                    # Try to serialize nested objects
                    state[attr_name] = self._serialize_component_state(attr_value)
            except Exception:
                continue  # Skip attributes that can't be serialized
        
        return state
    
    def _restore_component_states(self, snapshot: SystemState) -> None:
        """Restore component states from snapshot."""
        # This is a simplified implementation
        # In practice, each component would need specific restoration logic
        
        for name, component_ref in self.component_refs.items():
            component = component_ref()
            if component is None:
                continue
            
            try:
                if hasattr(component, 'restore_state') and name in snapshot.custom_data:
                    component.restore_state(snapshot.custom_data[name])
            except Exception as e:
                print(f"Failed to restore state for component {name}: {e}")
    
    def _save_snapshot_to_disk(self, snapshot: SystemState, snapshot_id: str) -> None:
        """Save snapshot to disk."""
        try:
            snapshot_file = self.snapshot_directory / f"{snapshot_id}.pkl"
            with open(snapshot_file, 'wb') as f:
                pickle.dump(snapshot, f)
        except Exception as e:
            print(f"Failed to save snapshot to disk: {e}")
    
    def _find_snapshot_by_id(self, snapshot_id: str) -> Optional[SystemState]:
        """Find snapshot by ID."""
        target_timestamp = datetime.strptime(snapshot_id.split('_', 1)[1], '%Y%m%d_%H%M%S')
        
        for snapshot in self.snapshots:
            if abs((snapshot.timestamp - target_timestamp).total_seconds()) < 1.0:
                return snapshot
        
        return None


class ErrorHandler:
    """
    Main error handling and recovery system coordinator.
    """
    
    def __init__(self, log_directory: str = "logs", snapshot_directory: str = "snapshots"):
        """
        Initialize error handler.
        
        Args:
            log_directory: Directory for log files
            snapshot_directory: Directory for state snapshots
        """
        self.logger = ErrorLogger(log_directory)
        self.asset_manager = AssetFallbackManager()
        self.state_manager = StateManager(snapshot_directory=snapshot_directory)
        
        # Error tracking
        self.error_reports: Dict[str, ErrorReport] = {}
        self.error_counter = 0
        self.recovery_strategies: Dict[str, Callable] = {}
        
        # System health monitoring
        self.component_health: Dict[str, bool] = {}
        self.last_health_check = 0.0
        self.health_check_interval = 30.0  # seconds
        
        # Recovery settings
        self.auto_recovery_enabled = True
        self.max_recovery_attempts = 3
        self.recovery_cooldown = 60.0  # seconds
        self.last_recovery_attempt: Dict[str, float] = {}
        
        # Register default recovery strategies
        self._register_default_recovery_strategies()
        
        self.logger.log_info("Error handling system initialized", "ErrorHandler")
    
    def handle_error(self, exception: Exception, component: str, 
                    category: ErrorCategory, severity: ErrorSeverity,
                    context: Optional[Dict[str, Any]] = None) -> ErrorReport:
        """
        Handle an error with appropriate recovery actions.
        
        Args:
            exception: The exception that occurred
            component: Component where error occurred
            category: Error category
            severity: Error severity level
            context: Additional context information
            
        Returns:
            Error report with recovery information
        """
        # Create error report
        self.error_counter += 1
        error_id = f"ERR_{self.error_counter:06d}"
        
        error_report = ErrorReport(
            error_id=error_id,
            timestamp=datetime.now(),
            category=category,
            severity=severity,
            component=component,
            error_type=type(exception).__name__,
            message=str(exception),
            traceback_info=traceback.format_exc(),
            context=context or {}
        )
        
        # Log the error
        self.logger.log_error(error_report)
        
        # Attempt recovery if enabled
        if self.auto_recovery_enabled:
            recovery_action = self._determine_recovery_action(error_report)
            error_report.recovery_action = recovery_action
            
            if recovery_action != RecoveryAction.IGNORE:
                success = self._execute_recovery_action(error_report)
                error_report.recovery_successful = success
        
        # Store error report
        self.error_reports[error_id] = error_report
        
        # Update component health
        self.component_health[component] = error_report.recovery_successful
        
        return error_report
    
    def register_recovery_strategy(self, error_pattern: str, 
                                 recovery_function: Callable) -> None:
        """
        Register a custom recovery strategy.
        
        Args:
            error_pattern: Pattern to match errors (component:error_type)
            recovery_function: Function to execute for recovery
        """
        self.recovery_strategies[error_pattern] = recovery_function
        self.logger.log_info(f"Registered recovery strategy for {error_pattern}", "ErrorHandler")
    
    def check_system_health(self, current_time: float) -> Dict[str, Any]:
        """
        Check overall system health.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            System health report
        """
        if current_time - self.last_health_check < self.health_check_interval:
            return self._get_cached_health_report()
        
        # Perform health checks
        health_report = {
            'overall_health': 'healthy',
            'component_health': dict(self.component_health),
            'recent_errors': self._get_recent_errors(),
            'recovery_success_rate': self._calculate_recovery_success_rate(),
            'recommendations': []
        }
        
        # Determine overall health
        unhealthy_components = [
            comp for comp, healthy in self.component_health.items() 
            if not healthy
        ]
        
        if len(unhealthy_components) > len(self.component_health) * 0.5:
            health_report['overall_health'] = 'critical'
            health_report['recommendations'].append('Consider system restart')
        elif unhealthy_components:
            health_report['overall_health'] = 'degraded'
            health_report['recommendations'].append(
                f'Check components: {", ".join(unhealthy_components)}'
            )
        
        # Check for recurring errors
        recurring_errors = self._find_recurring_errors()
        if recurring_errors:
            health_report['recommendations'].extend([
                f'Investigate recurring error: {error}' for error in recurring_errors
            ])
        
        self.last_health_check = current_time
        return health_report
    
    def create_recovery_checkpoint(self) -> str:
        """Create a recovery checkpoint."""
        return self.state_manager.create_snapshot({'checkpoint': True})
    
    def restore_from_checkpoint(self, checkpoint_id: Optional[str] = None) -> bool:
        """Restore system from checkpoint."""
        success = self.state_manager.restore_snapshot(checkpoint_id)
        
        if success:
            self.logger.log_info(f"Successfully restored from checkpoint {checkpoint_id}", "ErrorHandler")
            # Reset component health after successful restore
            for component in self.component_health:
                self.component_health[component] = True
        else:
            self.logger.log_warning(f"Failed to restore from checkpoint {checkpoint_id}", "ErrorHandler")
        
        return success
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        if not self.error_reports:
            return {'total_errors': 0}
        
        # Categorize errors
        by_category = defaultdict(int)
        by_severity = defaultdict(int)
        by_component = defaultdict(int)
        
        recovery_attempts = 0
        successful_recoveries = 0
        
        for error_report in self.error_reports.values():
            by_category[error_report.category.value] += 1
            by_severity[error_report.severity.name] += 1
            by_component[error_report.component] += 1
            
            if error_report.recovery_action and error_report.recovery_action != RecoveryAction.IGNORE:
                recovery_attempts += 1
                if error_report.recovery_successful:
                    successful_recoveries += 1
        
        return {
            'total_errors': len(self.error_reports),
            'by_category': dict(by_category),
            'by_severity': dict(by_severity),
            'by_component': dict(by_component),
            'recovery_attempts': recovery_attempts,
            'successful_recoveries': successful_recoveries,
            'recovery_success_rate': (
                successful_recoveries / max(1, recovery_attempts) * 100
            )
        }
    
    def _determine_recovery_action(self, error_report: ErrorReport) -> RecoveryAction:
        """Determine appropriate recovery action for an error."""
        # Check for custom recovery strategies
        pattern = f"{error_report.component}:{error_report.error_type}"
        if pattern in self.recovery_strategies:
            return RecoveryAction.RETRY
        
        # Default recovery logic based on category and severity
        if error_report.category == ErrorCategory.ASSET_LOADING:
            return RecoveryAction.FALLBACK
        elif error_report.category == ErrorCategory.VISUALIZATION:
            if error_report.severity.value >= ErrorSeverity.HIGH.value:
                return RecoveryAction.RESTART_COMPONENT
            else:
                return RecoveryAction.FALLBACK
        elif error_report.category == ErrorCategory.MEMORY:
            return RecoveryAction.RESTART_COMPONENT
        elif error_report.severity == ErrorSeverity.CRITICAL:
            return RecoveryAction.RESTART_SYSTEM
        elif error_report.severity.value >= ErrorSeverity.MEDIUM.value:
            return RecoveryAction.RETRY
        else:
            return RecoveryAction.IGNORE
    
    def _execute_recovery_action(self, error_report: ErrorReport) -> bool:
        """Execute the determined recovery action."""
        action = error_report.recovery_action
        component = error_report.component
        
        # Check recovery cooldown
        if component in self.last_recovery_attempt:
            time_since_last = time.time() - self.last_recovery_attempt[component]
            if time_since_last < self.recovery_cooldown:
                return False
        
        try:
            if action == RecoveryAction.RETRY:
                return self._retry_operation(error_report)
            elif action == RecoveryAction.FALLBACK:
                return self._apply_fallback(error_report)
            elif action == RecoveryAction.RESTART_COMPONENT:
                return self._restart_component(error_report)
            elif action == RecoveryAction.RESTART_SYSTEM:
                return self._restart_system(error_report)
            else:
                return True  # IGNORE action
                
        except Exception as e:
            self.logger.log_error(ErrorReport(
                error_id=f"RECOVERY_{error_report.error_id}",
                timestamp=datetime.now(),
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH,
                component="ErrorHandler",
                error_type=type(e).__name__,
                message=f"Recovery action failed: {str(e)}",
                traceback_info=traceback.format_exc()
            ))
            return False
        finally:
            self.last_recovery_attempt[component] = time.time()
    
    def _retry_operation(self, error_report: ErrorReport) -> bool:
        """Retry the failed operation."""
        pattern = f"{error_report.component}:{error_report.error_type}"
        
        if pattern in self.recovery_strategies:
            try:
                recovery_func = self.recovery_strategies[pattern]
                return recovery_func(error_report)
            except Exception:
                return False
        
        # Generic retry logic
        error_report.retry_count += 1
        return error_report.retry_count <= error_report.max_retries
    
    def _apply_fallback(self, error_report: ErrorReport) -> bool:
        """Apply fallback mechanisms."""
        if error_report.category == ErrorCategory.ASSET_LOADING:
            # Try to get fallback asset
            asset_path = error_report.context.get('asset_path')
            if asset_path:
                fallback = self.asset_manager.get_fallback_asset(asset_path)
                return fallback is not None
        
        return False
    
    def _restart_component(self, error_report: ErrorReport) -> bool:
        """Restart a specific component."""
        # This would need to be implemented based on specific component architecture
        self.logger.log_info(f"Attempting to restart component: {error_report.component}", "ErrorHandler")
        
        # For now, just mark component as healthy and create checkpoint
        self.component_health[error_report.component] = True
        self.state_manager.create_snapshot({'component_restart': error_report.component})
        
        return True
    
    def _restart_system(self, error_report: ErrorReport) -> bool:
        """Restart the entire system."""
        self.logger.log_warning("System restart requested due to critical error", "ErrorHandler")
        
        # Create emergency checkpoint
        self.state_manager.create_snapshot({'emergency_restart': True})
        
        # In a real implementation, this would trigger system restart
        return False  # Indicate that manual intervention is needed
    
    def _register_default_recovery_strategies(self) -> None:
        """Register default recovery strategies for common errors."""
        
        def asset_loading_recovery(error_report: ErrorReport) -> bool:
            """Recovery strategy for asset loading failures."""
            asset_path = error_report.context.get('asset_path', '')
            fallback = self.asset_manager.get_fallback_asset(asset_path)
            return fallback is not None
        
        def memory_error_recovery(error_report: ErrorReport) -> bool:
            """Recovery strategy for memory errors."""
            # Force garbage collection and try again
            import gc
            gc.collect()
            return True
        
        self.recovery_strategies.update({
            'VehicleAssetManager:FileNotFoundError': asset_loading_recovery,
            'TrafficFlowVisualizer:MemoryError': memory_error_recovery,
            'CityRenderer:TextureLoadError': asset_loading_recovery
        })
    
    def _get_recent_errors(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get errors from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_errors = []
        for error_report in self.error_reports.values():
            if error_report.timestamp >= cutoff_time:
                recent_errors.append({
                    'error_id': error_report.error_id,
                    'timestamp': error_report.timestamp.isoformat(),
                    'component': error_report.component,
                    'severity': error_report.severity.name,
                    'message': error_report.message
                })
        
        return sorted(recent_errors, key=lambda x: x['timestamp'], reverse=True)
    
    def _calculate_recovery_success_rate(self) -> float:
        """Calculate overall recovery success rate."""
        recovery_attempts = sum(
            1 for report in self.error_reports.values()
            if report.recovery_action and report.recovery_action != RecoveryAction.IGNORE
        )
        
        if recovery_attempts == 0:
            return 100.0
        
        successful_recoveries = sum(
            1 for report in self.error_reports.values()
            if report.recovery_successful
        )
        
        return (successful_recoveries / recovery_attempts) * 100.0
    
    def _find_recurring_errors(self, threshold: int = 3) -> List[str]:
        """Find errors that occur repeatedly."""
        error_patterns = defaultdict(int)
        
        for error_report in self.error_reports.values():
            pattern = f"{error_report.component}:{error_report.error_type}"
            error_patterns[pattern] += 1
        
        return [
            pattern for pattern, count in error_patterns.items()
            if count >= threshold
        ]
    
    def _get_cached_health_report(self) -> Dict[str, Any]:
        """Get cached health report."""
        return {
            'overall_health': 'unknown',
            'component_health': dict(self.component_health),
            'note': 'Cached report - full check pending'
        }