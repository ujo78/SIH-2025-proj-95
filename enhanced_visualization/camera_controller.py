"""
CameraController Implementation

This module implements the CameraControlInterface for advanced camera management
and scene navigation, including preset positions, follow-vehicle mode, and
cinematic camera paths with smooth transitions.
"""

import math
import time
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

try:
    from panda3d.core import (
        NodePath, Vec3, Vec4, Point3, Quat, Mat4,
        LerpPosInterval, LerpHprInterval, LerpQuatInterval,
        Sequence, Parallel, Func, Wait
    )
    from direct.showbase.DirectObject import DirectObject
    from direct.task import Task
    PANDA3D_AVAILABLE = True
except ImportError:
    PANDA3D_AVAILABLE = False
    # Mock classes for development without Panda3D
    class NodePath:
        def __init__(self, *args): pass
        def setPos(self, *args): pass
        def setHpr(self, *args): pass
        def lookAt(self, *args): pass
    
    class DirectObject:
        def accept(self, *args): pass
        def ignore(self, *args): pass
    
    Vec3 = Vec4 = Point3 = Quat = Mat4 = lambda *args: None
    Sequence = Parallel = LerpPosInterval = LerpHprInterval = lambda *args: None

try:
    # Try relative imports first (when used as package)
    from .interfaces import CameraControlInterface
    from .config import VisualizationConfig, CameraConfig
except ImportError:
    # Fall back to absolute imports (when run directly)
    from enhanced_visualization.interfaces import CameraControlInterface
    from enhanced_visualization.config import VisualizationConfig, CameraConfig

from indian_features.interfaces import Point3D


class CameraMode(Enum):
    """Camera control modes"""
    FREE = "free"
    FOLLOW_VEHICLE = "follow_vehicle"
    PRESET = "preset"
    CINEMATIC = "cinematic"
    ORBIT = "orbit"
    FIRST_PERSON = "first_person"


@dataclass
class CameraState:
    """Represents the current camera state"""
    position: Point3D
    target: Point3D
    up_vector: Point3D
    fov: float
    mode: CameraMode
    follow_target_id: Optional[int] = None
    animation_active: bool = False


@dataclass
class CameraPreset:
    """Represents a camera preset configuration"""
    name: str
    position: Point3D
    target: Point3D
    fov: float
    description: str
    transition_duration: float = 2.0


@dataclass
class CinematicWaypoint:
    """Waypoint for cinematic camera paths"""
    position: Point3D
    target: Point3D
    fov: float
    duration: float
    ease_in: bool = True
    ease_out: bool = True


class CameraController(CameraControlInterface, DirectObject if PANDA3D_AVAILABLE else object):
    """
    Advanced camera controller for 3D scene navigation.
    
    This class provides comprehensive camera control including preset positions,
    smooth transitions, vehicle following, and cinematic camera paths for
    enhanced visualization of Indian traffic scenarios.
    """
    
    def __init__(self, config: VisualizationConfig, camera_node: Optional[NodePath] = None):
        """
        Initialize the camera controller.
        
        Args:
            config: Visualization configuration
            camera_node: Panda3D camera node (optional, for testing)
        """
        if PANDA3D_AVAILABLE:
            DirectObject.__init__(self)
        
        self.config = config
        self.camera_config = config.camera_config
        
        # Camera node setup
        if PANDA3D_AVAILABLE and camera_node is not None:
            self.camera = camera_node
        else:
            self.camera = None
        
        # Camera state management
        self.current_state = CameraState(
            position=Point3D(*self.camera_config.default_position),
            target=Point3D(*self.camera_config.default_target),
            up_vector=Point3D(0, 0, 1),
            fov=self.camera_config.field_of_view,
            mode=CameraMode.FREE
        )
        
        # Camera presets
        self.presets: Dict[str, CameraPreset] = {}
        self._initialize_presets()
        
        # Follow mode settings
        self.follow_target_id: Optional[int] = None
        self.follow_offset = Point3D(
            0, -self.camera_config.follow_distance, self.camera_config.follow_height
        )
        self.follow_smoothing = self.camera_config.follow_smoothing
        
        # Animation management
        self.active_animation: Optional[Any] = None
        self.cinematic_path: List[CinematicWaypoint] = []
        self.cinematic_active = False
        
        # Input handling
        self.free_camera_enabled = True
        self.mouse_sensitivity = 1.0
        self.keyboard_speed = self.camera_config.movement_speed
        
        # Movement state
        self.movement_keys = {
            'forward': False, 'backward': False,
            'left': False, 'right': False,
            'up': False, 'down': False
        }
        
        # Orbit mode settings
        self.orbit_center = Point3D(0, 0, 0)
        self.orbit_distance = 100.0
        self.orbit_angle_h = 0.0
        self.orbit_angle_p = -30.0
        
        # Performance tracking
        self.last_update_time = time.time()
        self.update_frequency = 60.0  # Hz
        
        # Initialize input handling
        self._setup_input_handling()
        
        # Start update task
        self._start_update_task()
    
    def set_camera_position(self, position: Point3D, target: Point3D) -> None:
        """
        Set camera position and target.
        
        Args:
            position: Camera position
            target: Camera target (look-at point)
        """
        self.current_state.position = position
        self.current_state.target = target
        self.current_state.mode = CameraMode.FREE
        
        if not PANDA3D_AVAILABLE:
            print(f"Setting camera position to ({position.x}, {position.y}, {position.z}) (mock)")
            return
        
        if self.camera:
            self.camera.setPos(position.x, position.y, position.z)
            self.camera.lookAt(target.x, target.y, target.z)
        
        print(f"Camera positioned at ({position.x:.1f}, {position.y:.1f}, {position.z:.1f})")
    
    def create_smooth_transition(self, start_pos: Point3D, end_pos: Point3D, duration: float) -> None:
        """
        Create smooth camera transition between positions.
        
        Args:
            start_pos: Starting position
            end_pos: Ending position
            duration: Transition duration in seconds
        """
        if not PANDA3D_AVAILABLE:
            print(f"Creating smooth transition from ({start_pos.x}, {start_pos.y}, {start_pos.z}) "
                  f"to ({end_pos.x}, {end_pos.y}, {end_pos.z}) over {duration}s (mock)")
            return
        
        if not self.camera:
            return
        
        # Stop any existing animation
        if self.active_animation:
            self.active_animation.finish()
        
        # Create position interpolation
        start_point = Point3(start_pos.x, start_pos.y, start_pos.z)
        end_point = Point3(end_pos.x, end_pos.y, end_pos.z)
        
        pos_interval = LerpPosInterval(
            self.camera,
            duration,
            end_point,
            startPos=start_point
        )
        
        # Create sequence with callback
        self.active_animation = Sequence(
            pos_interval,
            Func(self._on_transition_complete, end_pos)
        )
        
        self.current_state.animation_active = True
        self.active_animation.start()
        
        print(f"Started smooth transition to ({end_pos.x:.1f}, {end_pos.y:.1f}, {end_pos.z:.1f})")
    
    def follow_vehicle(self, vehicle_id: int, offset: Point3D) -> None:
        """
        Set camera to follow a specific vehicle.
        
        Args:
            vehicle_id: ID of the vehicle to follow
            offset: Camera offset from vehicle position
        """
        self.follow_target_id = vehicle_id
        self.follow_offset = offset
        self.current_state.mode = CameraMode.FOLLOW_VEHICLE
        self.current_state.follow_target_id = vehicle_id
        
        if not PANDA3D_AVAILABLE:
            print(f"Following vehicle {vehicle_id} with offset ({offset.x}, {offset.y}, {offset.z}) (mock)")
            return
        
        print(f"Camera now following vehicle {vehicle_id}")
    
    def set_preset_view(self, preset_name: str) -> None:
        """
        Switch to a predefined camera preset.
        
        Args:
            preset_name: Name of the preset to activate
        """
        if preset_name not in self.presets:
            print(f"Camera preset '{preset_name}' not found")
            return
        
        preset = self.presets[preset_name]
        
        if not PANDA3D_AVAILABLE:
            print(f"Switching to preset '{preset_name}' (mock)")
            return
        
        # Create smooth transition to preset
        self.create_smooth_transition(
            self.current_state.position,
            preset.position,
            preset.transition_duration
        )
        
        # Update state
        self.current_state.mode = CameraMode.PRESET
        self.current_state.target = preset.target
        self.current_state.fov = preset.fov
        
        print(f"Switched to camera preset: {preset_name}")
    
    def enable_free_camera(self, enable: bool) -> None:
        """
        Enable/disable free camera movement.
        
        Args:
            enable: Whether to enable free camera mode
        """
        self.free_camera_enabled = enable
        
        if enable:
            self.current_state.mode = CameraMode.FREE
            self._enable_input_handling()
        else:
            self._disable_input_handling()
        
        print(f"Free camera mode: {'enabled' if enable else 'disabled'}")
    
    def create_cinematic_path(self, waypoints: List[Point3D], duration: float) -> None:
        """
        Create cinematic camera path through waypoints.
        
        Args:
            waypoints: List of waypoints for the camera path
            duration: Total duration for the path
        """
        if len(waypoints) < 2:
            print("Cinematic path requires at least 2 waypoints")
            return
        
        if not PANDA3D_AVAILABLE:
            print(f"Creating cinematic path with {len(waypoints)} waypoints over {duration}s (mock)")
            return
        
        # Convert waypoints to cinematic waypoints
        self.cinematic_path = []
        segment_duration = duration / (len(waypoints) - 1)
        
        for i, waypoint in enumerate(waypoints):
            # Calculate target (look ahead to next waypoint or current direction)
            if i < len(waypoints) - 1:
                target = waypoints[i + 1]
            else:
                # For last waypoint, maintain previous direction
                if i > 0:
                    direction = Point3D(
                        waypoints[i].x - waypoints[i-1].x,
                        waypoints[i].y - waypoints[i-1].y,
                        waypoints[i].z - waypoints[i-1].z
                    )
                    target = Point3D(
                        waypoint.x + direction.x,
                        waypoint.y + direction.y,
                        waypoint.z + direction.z
                    )
                else:
                    target = waypoint
            
            cinematic_waypoint = CinematicWaypoint(
                position=waypoint,
                target=target,
                fov=self.current_state.fov,
                duration=segment_duration,
                ease_in=(i == 0),
                ease_out=(i == len(waypoints) - 1)
            )
            
            self.cinematic_path.append(cinematic_waypoint)
        
        # Start cinematic sequence
        self._start_cinematic_sequence()
        
        print(f"Started cinematic path with {len(waypoints)} waypoints")
    
    def set_orbit_mode(self, center: Point3D, distance: float) -> None:
        """
        Set camera to orbit around a center point.
        
        Args:
            center: Center point to orbit around
            distance: Distance from center
        """
        self.orbit_center = center
        self.orbit_distance = distance
        self.current_state.mode = CameraMode.ORBIT
        
        # Calculate initial orbit position
        self._update_orbit_position()
        
        print(f"Camera orbiting around ({center.x:.1f}, {center.y:.1f}, {center.z:.1f})")
    
    def get_camera_state(self) -> CameraState:
        """Get current camera state."""
        return self.current_state
    
    def add_preset(self, name: str, position: Point3D, target: Point3D, 
                   fov: float = None, description: str = "") -> None:
        """
        Add a new camera preset.
        
        Args:
            name: Preset name
            position: Camera position
            target: Camera target
            fov: Field of view (optional)
            description: Preset description
        """
        if fov is None:
            fov = self.camera_config.field_of_view
        
        preset = CameraPreset(
            name=name,
            position=position,
            target=target,
            fov=fov,
            description=description
        )
        
        self.presets[name] = preset
        print(f"Added camera preset: {name}")
    
    def _initialize_presets(self) -> None:
        """Initialize default camera presets."""
        preset_configs = self.camera_config.camera_presets
        
        for name, config in preset_configs.items():
            position = Point3D(*config["position"])
            target = Point3D(*config["target"])
            
            preset = CameraPreset(
                name=name,
                position=position,
                target=target,
                fov=self.camera_config.field_of_view,
                description=f"Default {name} view"
            )
            
            self.presets[name] = preset
    
    def _setup_input_handling(self) -> None:
        """Setup input event handling."""
        if not PANDA3D_AVAILABLE:
            return
        
        # Keyboard events for movement
        self.accept("w", self._set_movement_key, ["forward", True])
        self.accept("w-up", self._set_movement_key, ["forward", False])
        self.accept("s", self._set_movement_key, ["backward", True])
        self.accept("s-up", self._set_movement_key, ["backward", False])
        self.accept("a", self._set_movement_key, ["left", True])
        self.accept("a-up", self._set_movement_key, ["left", False])
        self.accept("d", self._set_movement_key, ["right", True])
        self.accept("d-up", self._set_movement_key, ["right", False])
        self.accept("q", self._set_movement_key, ["up", True])
        self.accept("q-up", self._set_movement_key, ["up", False])
        self.accept("e", self._set_movement_key, ["down", True])
        self.accept("e-up", self._set_movement_key, ["down", False])
        
        # Mouse events for looking
        self.accept("mouse1", self._start_mouse_look)
        self.accept("mouse1-up", self._stop_mouse_look)
        
        # Preset hotkeys
        for i, preset_name in enumerate(self.presets.keys()):
            if i < 9:  # F1-F9
                self.accept(f"f{i+1}", self.set_preset_view, [preset_name])
    
    def _enable_input_handling(self) -> None:
        """Enable input handling for free camera mode."""
        # Input handling is always active, just check free_camera_enabled in update
        pass
    
    def _disable_input_handling(self) -> None:
        """Disable input handling."""
        # Reset movement state
        for key in self.movement_keys:
            self.movement_keys[key] = False
    
    def _set_movement_key(self, key: str, pressed: bool) -> None:
        """Set movement key state."""
        if key in self.movement_keys:
            self.movement_keys[key] = pressed
    
    def _start_mouse_look(self) -> None:
        """Start mouse look mode."""
        # Implementation would capture mouse for looking
        pass
    
    def _stop_mouse_look(self) -> None:
        """Stop mouse look mode."""
        # Implementation would release mouse capture
        pass
    
    def _start_update_task(self) -> None:
        """Start the camera update task."""
        if not PANDA3D_AVAILABLE:
            return
        
        # In a full Panda3D implementation, this would start a task
        # For now, we'll rely on manual updates
        pass
    
    def update(self, dt: float, vehicle_positions: Dict[int, Point3D] = None) -> None:
        """
        Update camera based on current mode and input.
        
        Args:
            dt: Delta time since last update
            vehicle_positions: Dictionary of vehicle positions for follow mode
        """
        if not self.camera or not PANDA3D_AVAILABLE:
            return
        
        current_time = time.time()
        
        # Skip update if too frequent
        if current_time - self.last_update_time < 1.0 / self.update_frequency:
            return
        
        self.last_update_time = current_time
        
        # Update based on current mode
        if self.current_state.mode == CameraMode.FREE and self.free_camera_enabled:
            self._update_free_camera(dt)
        elif self.current_state.mode == CameraMode.FOLLOW_VEHICLE:
            self._update_follow_camera(dt, vehicle_positions)
        elif self.current_state.mode == CameraMode.ORBIT:
            self._update_orbit_camera(dt)
        elif self.current_state.mode == CameraMode.CINEMATIC:
            self._update_cinematic_camera(dt)
    
    def _update_free_camera(self, dt: float) -> None:
        """Update free camera movement."""
        if not self.free_camera_enabled or self.current_state.animation_active:
            return
        
        # Calculate movement vector
        movement = Vec3(0, 0, 0)
        speed = self.keyboard_speed * dt
        
        if self.movement_keys['forward']:
            movement.y += speed
        if self.movement_keys['backward']:
            movement.y -= speed
        if self.movement_keys['left']:
            movement.x -= speed
        if self.movement_keys['right']:
            movement.x += speed
        if self.movement_keys['up']:
            movement.z += speed
        if self.movement_keys['down']:
            movement.z -= speed
        
        # Apply movement relative to camera orientation
        if movement.length() > 0:
            current_pos = self.camera.getPos()
            new_pos = current_pos + movement
            self.camera.setPos(new_pos)
            
            # Update state
            self.current_state.position = Point3D(new_pos.x, new_pos.y, new_pos.z)
    
    def _update_follow_camera(self, dt: float, vehicle_positions: Dict[int, Point3D] = None) -> None:
        """Update follow camera mode."""
        if not vehicle_positions or self.follow_target_id not in vehicle_positions:
            return
        
        target_pos = vehicle_positions[self.follow_target_id]
        
        # Calculate desired camera position
        desired_pos = Point3D(
            target_pos.x + self.follow_offset.x,
            target_pos.y + self.follow_offset.y,
            target_pos.z + self.follow_offset.z
        )
        
        # Smooth interpolation to desired position
        current_pos = self.current_state.position
        
        lerp_factor = min(1.0, self.follow_smoothing * dt * 60)  # 60 FPS reference
        
        new_pos = Point3D(
            current_pos.x + (desired_pos.x - current_pos.x) * lerp_factor,
            current_pos.y + (desired_pos.y - current_pos.y) * lerp_factor,
            current_pos.z + (desired_pos.z - current_pos.z) * lerp_factor
        )
        
        # Update camera
        self.camera.setPos(new_pos.x, new_pos.y, new_pos.z)
        self.camera.lookAt(target_pos.x, target_pos.y, target_pos.z)
        
        # Update state
        self.current_state.position = new_pos
        self.current_state.target = target_pos
    
    def _update_orbit_camera(self, dt: float) -> None:
        """Update orbit camera mode."""
        # Auto-rotate around center
        rotation_speed = 30.0  # degrees per second
        self.orbit_angle_h += rotation_speed * dt
        
        if self.orbit_angle_h >= 360.0:
            self.orbit_angle_h -= 360.0
        
        self._update_orbit_position()
    
    def _update_orbit_position(self) -> None:
        """Update camera position for orbit mode."""
        if not PANDA3D_AVAILABLE or not self.camera:
            return
        
        # Calculate position on orbit
        h_rad = math.radians(self.orbit_angle_h)
        p_rad = math.radians(self.orbit_angle_p)
        
        x = self.orbit_center.x + self.orbit_distance * math.cos(p_rad) * math.sin(h_rad)
        y = self.orbit_center.y + self.orbit_distance * math.cos(p_rad) * math.cos(h_rad)
        z = self.orbit_center.z + self.orbit_distance * math.sin(p_rad)
        
        # Update camera
        self.camera.setPos(x, y, z)
        self.camera.lookAt(self.orbit_center.x, self.orbit_center.y, self.orbit_center.z)
        
        # Update state
        self.current_state.position = Point3D(x, y, z)
        self.current_state.target = self.orbit_center
    
    def _update_cinematic_camera(self, dt: float) -> None:
        """Update cinematic camera mode."""
        # Cinematic updates are handled by animation sequences
        pass
    
    def _start_cinematic_sequence(self) -> None:
        """Start cinematic camera sequence."""
        if not PANDA3D_AVAILABLE or not self.cinematic_path:
            return
        
        # Stop any existing animation
        if self.active_animation:
            self.active_animation.finish()
        
        # Create animation intervals for each segment
        intervals = []
        
        for i, waypoint in enumerate(self.cinematic_path):
            if i == 0:
                continue  # Skip first waypoint (starting position)
            
            prev_waypoint = self.cinematic_path[i - 1]
            
            # Position animation
            start_pos = Point3(prev_waypoint.position.x, prev_waypoint.position.y, prev_waypoint.position.z)
            end_pos = Point3(waypoint.position.x, waypoint.position.y, waypoint.position.z)
            
            pos_interval = LerpPosInterval(
                self.camera,
                waypoint.duration,
                end_pos,
                startPos=start_pos
            )
            
            # Look-at animation (simplified)
            # In full implementation, would use LerpQuatInterval for smooth rotation
            
            intervals.append(pos_interval)
        
        # Create sequence
        self.active_animation = Sequence(*intervals, Func(self._on_cinematic_complete))
        self.current_state.mode = CameraMode.CINEMATIC
        self.current_state.animation_active = True
        self.cinematic_active = True
        
        self.active_animation.start()
    
    def _on_transition_complete(self, end_pos: Point3D) -> None:
        """Called when a camera transition completes."""
        self.current_state.animation_active = False
        self.current_state.position = end_pos
        print("Camera transition completed")
    
    def _on_cinematic_complete(self) -> None:
        """Called when cinematic sequence completes."""
        self.current_state.animation_active = False
        self.cinematic_active = False
        self.current_state.mode = CameraMode.FREE
        print("Cinematic sequence completed")
    
    def cleanup(self) -> None:
        """Cleanup camera controller resources."""
        if PANDA3D_AVAILABLE:
            self.ignoreAll()
        
        if self.active_animation:
            self.active_animation.finish()
        
        print("Camera controller cleaned up")