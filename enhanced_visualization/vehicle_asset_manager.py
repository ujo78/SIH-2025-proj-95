"""
VehicleAssetManager Implementation

This module implements the VehicleAssetInterface for managing 3D vehicle assets
specific to Indian vehicle types, including loading, animation, and visual indicators
for vehicle behavior states and interactions.
"""

import math
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

try:
    from panda3d.core import (
        NodePath, Loader, Vec3, Vec4, Point3, Quat,
        CollisionNode, CollisionSphere, BitMask32,
        Material, Texture, TextureStage, LerpPosInterval,
        LerpHprInterval, Sequence, Parallel, LerpColorInterval,
        CardMaker, GeomNode, RenderState, ColorBlendAttrib,
        TransparencyAttrib, BillboardEffect
    )
    from direct.interval.IntervalGlobal import Func, Wait
    PANDA3D_AVAILABLE = True
except ImportError:
    PANDA3D_AVAILABLE = False
    # Mock classes for development without Panda3D
    class NodePath:
        def __init__(self, *args): pass
        def setPos(self, *args): pass
        def setHpr(self, *args): pass
        def setScale(self, *args): pass
        def setColor(self, *args): pass
        def setTexture(self, *args): pass
        def reparentTo(self, *args): pass
        def removeNode(self): pass
        def show(self): pass
        def hide(self): pass
    
    Vec3 = Vec4 = Point3 = Quat = lambda *args: None
    Sequence = Parallel = LerpPosInterval = LerpHprInterval = lambda *args: None

try:
    # Try relative imports first (when used as package)
    from .interfaces import VehicleAssetInterface, VehicleVisual
    from .config import VisualizationConfig, AssetConfig
except ImportError:
    # Fall back to absolute imports (when run directly)
    from enhanced_visualization.interfaces import VehicleAssetInterface, VehicleVisual
    from enhanced_visualization.config import VisualizationConfig, AssetConfig
from indian_features.enums import VehicleType, BehaviorProfile
from indian_features.interfaces import Point3D


@dataclass
class VehicleInstance:
    """Represents a vehicle instance in the 3D scene"""
    vehicle_id: int
    vehicle_type: VehicleType
    node_path: NodePath
    behavior_indicators: Dict[str, NodePath]
    current_animation: Optional[Any] = None
    last_update_time: float = 0.0
    trail_points: List[Point3D] = None
    
    def __post_init__(self):
        if self.trail_points is None:
            self.trail_points = []


@dataclass
class VehicleInteractionVisual:
    """Visual representation of vehicle interactions"""
    interaction_type: str  # "overtaking", "following", "merging", "blocking"
    primary_vehicle_id: int
    secondary_vehicle_id: int
    intensity: float  # 0.0 to 1.0
    duration: float
    visual_elements: List[NodePath] = None
    
    def __post_init__(self):
        if self.visual_elements is None:
            self.visual_elements = []


class VehicleAssetManager(VehicleAssetInterface):
    """
    Manages 3D vehicle assets and animations for Indian vehicle types.
    
    This class handles loading vehicle models, creating instances, animating
    movement, and providing visual indicators for vehicle behavior states
    and interactions.
    """
    
    def __init__(self, config: VisualizationConfig, render_root: Optional[NodePath] = None):
        """
        Initialize the vehicle asset manager.
        
        Args:
            config: Visualization configuration
            render_root: Root node for rendering (optional, for testing)
        """
        self.config = config
        self.asset_config = config.asset_config
        
        # Initialize Panda3D components if available
        if PANDA3D_AVAILABLE and render_root is not None:
            self.render = render_root
            self.loader = Loader.getGlobalPtr() if hasattr(Loader, 'getGlobalPtr') else None
        else:
            self.render = None
            self.loader = None
        
        # Asset management
        self.vehicle_models: Dict[VehicleType, NodePath] = {}
        self.vehicle_instances: Dict[int, VehicleInstance] = {}
        self.interaction_visuals: Dict[str, VehicleInteractionVisual] = {}
        
        # Scene nodes
        self.vehicles_node = None
        self.effects_node = None
        self.trails_node = None
        
        # Animation management
        self.active_animations: Dict[int, Any] = {}
        self.animation_sequences: Dict[str, Any] = {}
        
        # Behavior indicators
        self.behavior_materials = {}
        self.interaction_effects = {}
        
        # Performance settings
        self.max_visible_vehicles = 200
        self.trail_length = 50
        self.update_frequency = 30.0  # Hz
        
        # Initialize the system
        self._initialize_scene_nodes()
        self._create_behavior_materials()
    
    def load_vehicle_models(self) -> Dict[VehicleType, str]:
        """
        Load 3D models for different Indian vehicle types.
        
        Returns:
            Dictionary mapping vehicle types to model paths
        """
        model_paths = {}
        
        if not PANDA3D_AVAILABLE:
            print("Loading vehicle models (mock)")
            # Return mock paths for testing
            for vehicle_type in VehicleType:
                model_paths[vehicle_type] = f"mock_path_{vehicle_type.value}.egg"
            return model_paths
        
        for vehicle_type, model_path in self.asset_config.vehicle_model_paths.items():
            try:
                # Load the model
                full_path = Path(self.asset_config.models_directory) / model_path
                
                if full_path.exists() and self.loader:
                    model = self.loader.loadModel(str(full_path))
                    if model:
                        # Apply scaling
                        scale = self.asset_config.vehicle_scales.get(vehicle_type, 1.0)
                        model.setScale(scale)
                        
                        # Store the model
                        self.vehicle_models[vehicle_type] = model
                        model_paths[vehicle_type] = str(full_path)
                        
                        # Apply Indian vehicle characteristics
                        self._apply_indian_vehicle_styling(model, vehicle_type)
                        
                        print(f"Loaded model for {vehicle_type}: {model_path}")
                    else:
                        print(f"Failed to load model: {full_path}")
                        # Create fallback model
                        self.vehicle_models[vehicle_type] = self._create_fallback_model(vehicle_type)
                        model_paths[vehicle_type] = f"fallback_{vehicle_type.value}"
                else:
                    print(f"Model file not found: {full_path}")
                    # Create fallback model
                    self.vehicle_models[vehicle_type] = self._create_fallback_model(vehicle_type)
                    model_paths[vehicle_type] = f"fallback_{vehicle_type.value}"
                    
            except Exception as e:
                print(f"Error loading model for {vehicle_type}: {e}")
                # Create fallback model
                self.vehicle_models[vehicle_type] = self._create_fallback_model(vehicle_type)
                model_paths[vehicle_type] = f"fallback_{vehicle_type.value}"
        
        print(f"Loaded {len(self.vehicle_models)} vehicle models")
        return model_paths
    
    def create_vehicle_instance(self, vehicle: VehicleVisual) -> Any:
        """
        Create a 3D instance of a vehicle in the scene.
        
        Args:
            vehicle: Vehicle visual data
            
        Returns:
            Vehicle instance reference
        """
        if not PANDA3D_AVAILABLE or not self.vehicles_node:
            print(f"Creating vehicle instance {vehicle.vehicle_id} (mock)")
            return f"mock_instance_{vehicle.vehicle_id}"
        
        # Get the base model
        base_model = self.vehicle_models.get(vehicle.vehicle_type)
        if not base_model:
            print(f"No model available for vehicle type: {vehicle.vehicle_type}")
            return None
        
        # Create instance
        instance_node = base_model.copyTo(self.vehicles_node)
        instance_node.setName(f"vehicle_{vehicle.vehicle_id}")
        
        # Set initial position and orientation
        instance_node.setPos(vehicle.position.x, vehicle.position.y, vehicle.position.z)
        instance_node.setH(vehicle.heading)
        
        # Apply custom scaling if specified
        if vehicle.scale != 1.0:
            current_scale = instance_node.getScale()
            instance_node.setScale(current_scale * vehicle.scale)
        
        # Apply custom color if specified
        if vehicle.color:
            instance_node.setColor(*vehicle.color, 1.0)
        
        # Create behavior indicators
        behavior_indicators = self._create_behavior_indicators(instance_node, vehicle)
        
        # Create vehicle instance record
        vehicle_instance = VehicleInstance(
            vehicle_id=vehicle.vehicle_id,
            vehicle_type=vehicle.vehicle_type,
            node_path=instance_node,
            behavior_indicators=behavior_indicators,
            last_update_time=time.time()
        )
        
        self.vehicle_instances[vehicle.vehicle_id] = vehicle_instance
        
        print(f"Created vehicle instance {vehicle.vehicle_id} of type {vehicle.vehicle_type}")
        return vehicle_instance
    
    def update_vehicle_position(self, vehicle_id: int, position: Point3D, heading: float) -> None:
        """
        Update vehicle position and orientation.
        
        Args:
            vehicle_id: ID of the vehicle to update
            position: New position
            heading: New heading in degrees
        """
        if vehicle_id not in self.vehicle_instances:
            return
        
        instance = self.vehicle_instances[vehicle_id]
        
        if not PANDA3D_AVAILABLE:
            print(f"Updating vehicle {vehicle_id} position to ({position.x}, {position.y}, {position.z}) (mock)")
            return
        
        # Update position and heading
        instance.node_path.setPos(position.x, position.y, position.z)
        instance.node_path.setH(heading)
        
        # Update trail
        self._update_vehicle_trail(instance, position)
        
        # Update behavior indicators based on movement
        self._update_behavior_indicators(instance, position, heading)
        
        instance.last_update_time = time.time()
    
    def animate_vehicle_movement(self, vehicle_id: int, path: List[Point3D], duration: float) -> None:
        """
        Animate vehicle movement along a path.
        
        Args:
            vehicle_id: ID of the vehicle to animate
            path: List of points defining the path
            duration: Animation duration in seconds
        """
        if vehicle_id not in self.vehicle_instances or not path:
            return
        
        instance = self.vehicle_instances[vehicle_id]
        
        if not PANDA3D_AVAILABLE:
            print(f"Animating vehicle {vehicle_id} along path with {len(path)} points (mock)")
            return
        
        # Stop any existing animation
        if vehicle_id in self.active_animations:
            self.active_animations[vehicle_id].finish()
        
        # Create animation sequence
        animation_sequence = self._create_path_animation(instance, path, duration)
        
        if animation_sequence:
            self.active_animations[vehicle_id] = animation_sequence
            animation_sequence.start()
            
            print(f"Started animation for vehicle {vehicle_id}")
    
    def show_vehicle_interactions(self, interactions: List[Dict[str, Any]]) -> None:
        """
        Visualize vehicle interactions (overtaking, following, etc.).
        
        Args:
            interactions: List of interaction data
        """
        if not PANDA3D_AVAILABLE:
            print(f"Showing {len(interactions)} vehicle interactions (mock)")
            return
        
        # Clear existing interaction visuals
        self._clear_interaction_visuals()
        
        for interaction in interactions:
            self._create_interaction_visual(interaction)
        
        print(f"Displaying {len(interactions)} vehicle interactions")
    
    def remove_vehicle(self, vehicle_id: int) -> None:
        """
        Remove vehicle from the scene.
        
        Args:
            vehicle_id: ID of the vehicle to remove
        """
        if vehicle_id not in self.vehicle_instances:
            return
        
        instance = self.vehicle_instances[vehicle_id]
        
        if not PANDA3D_AVAILABLE:
            print(f"Removing vehicle {vehicle_id} (mock)")
        else:
            # Stop any active animation
            if vehicle_id in self.active_animations:
                self.active_animations[vehicle_id].finish()
                del self.active_animations[vehicle_id]
            
            # Remove behavior indicators
            for indicator in instance.behavior_indicators.values():
                indicator.removeNode()
            
            # Remove main node
            instance.node_path.removeNode()
        
        # Remove from tracking
        del self.vehicle_instances[vehicle_id]
        
        print(f"Removed vehicle {vehicle_id}")
    
    def set_vehicle_visibility(self, vehicle_id: int, visible: bool) -> None:
        """
        Set vehicle visibility in the scene.
        
        Args:
            vehicle_id: ID of the vehicle
            visible: Whether the vehicle should be visible
        """
        if vehicle_id not in self.vehicle_instances:
            return
        
        instance = self.vehicle_instances[vehicle_id]
        
        if not PANDA3D_AVAILABLE:
            print(f"Setting vehicle {vehicle_id} visibility to {visible} (mock)")
        else:
            if visible:
                instance.node_path.show()
            else:
                instance.node_path.hide()
    
    def _initialize_scene_nodes(self) -> None:
        """Initialize scene node hierarchy."""
        if not PANDA3D_AVAILABLE or not self.render:
            return
        
        self.vehicles_node = self.render.attachNewNode("vehicles")
        self.effects_node = self.render.attachNewNode("vehicle_effects")
        self.trails_node = self.render.attachNewNode("vehicle_trails")
    
    def _create_behavior_materials(self) -> None:
        """Create materials for behavior indicators."""
        if not PANDA3D_AVAILABLE:
            return
        
        # Create materials for different behavior states
        self.behavior_materials = {
            "aggressive": self._create_material(Vec4(1.0, 0.0, 0.0, 0.8)),  # Red
            "cautious": self._create_material(Vec4(0.0, 1.0, 0.0, 0.8)),    # Green
            "normal": self._create_material(Vec4(0.0, 0.0, 1.0, 0.8)),      # Blue
            "overtaking": self._create_material(Vec4(1.0, 1.0, 0.0, 0.8)),  # Yellow
            "following": self._create_material(Vec4(0.5, 0.5, 1.0, 0.8))    # Light blue
        }
    
    def _create_material(self, color: Vec4) -> Any:
        """Create a material with the specified color."""
        if not PANDA3D_AVAILABLE:
            return None
        
        material = Material()
        material.setAmbient(color)
        material.setDiffuse(color)
        material.setEmission(color * 0.3)
        return material
    
    def _apply_indian_vehicle_styling(self, model: NodePath, vehicle_type: VehicleType) -> None:
        """Apply Indian-specific styling to vehicle models."""
        if not PANDA3D_AVAILABLE:
            return
        
        # Apply colors typical of Indian vehicles
        if vehicle_type == VehicleType.AUTO_RICKSHAW:
            model.setColor(1.0, 1.0, 0.0, 1.0)  # Yellow
        elif vehicle_type == VehicleType.BUS:
            model.setColor(0.8, 0.0, 0.0, 1.0)  # Red
        elif vehicle_type == VehicleType.TRUCK:
            model.setColor(0.0, 0.5, 0.8, 1.0)  # Blue
        elif vehicle_type == VehicleType.MOTORCYCLE:
            model.setColor(0.2, 0.2, 0.2, 1.0)  # Dark gray
        # Cars keep default colors for variety
    
    def _create_fallback_model(self, vehicle_type: VehicleType) -> Optional[NodePath]:
        """Create a simple fallback model for a vehicle type."""
        if not PANDA3D_AVAILABLE:
            return None
        
        # Create a simple box as fallback
        fallback_node = NodePath(f"fallback_{vehicle_type.value}")
        
        # Set size based on vehicle type
        if vehicle_type == VehicleType.BUS:
            fallback_node.setScale(12.0, 3.0, 3.5)  # Long bus
        elif vehicle_type == VehicleType.TRUCK:
            fallback_node.setScale(10.0, 2.5, 3.0)  # Truck
        elif vehicle_type == VehicleType.AUTO_RICKSHAW:
            fallback_node.setScale(3.0, 1.5, 2.0)   # Small auto
        elif vehicle_type == VehicleType.MOTORCYCLE:
            fallback_node.setScale(2.0, 0.8, 1.2)   # Motorcycle
        else:  # Car
            fallback_node.setScale(4.5, 2.0, 1.5)   # Standard car
        
        # Apply appropriate color
        self._apply_indian_vehicle_styling(fallback_node, vehicle_type)
        
        return fallback_node
    
    def _create_behavior_indicators(self, vehicle_node: NodePath, vehicle: VehicleVisual) -> Dict[str, NodePath]:
        """Create visual indicators for vehicle behavior."""
        indicators = {}
        
        if not PANDA3D_AVAILABLE:
            return indicators
        
        # Create speed indicator (above vehicle)
        speed_indicator = self._create_speed_indicator(vehicle_node)
        if speed_indicator:
            indicators["speed"] = speed_indicator
        
        # Create behavior state indicator
        behavior_indicator = self._create_behavior_state_indicator(vehicle_node)
        if behavior_indicator:
            indicators["behavior"] = behavior_indicator
        
        return indicators
    
    def _create_speed_indicator(self, vehicle_node: NodePath) -> Optional[NodePath]:
        """Create a speed indicator above the vehicle."""
        if not PANDA3D_AVAILABLE:
            return None
        
        # Create a simple colored bar above the vehicle
        indicator = NodePath("speed_indicator")
        indicator.setPos(0, 0, 3.0)  # Above vehicle
        indicator.setScale(0.5, 0.1, 0.1)
        indicator.setColor(0.0, 1.0, 0.0, 0.8)  # Green by default
        indicator.reparentTo(vehicle_node)
        
        return indicator
    
    def _create_behavior_state_indicator(self, vehicle_node: NodePath) -> Optional[NodePath]:
        """Create a behavior state indicator."""
        if not PANDA3D_AVAILABLE:
            return None
        
        # Create a small sphere to indicate behavior state
        indicator = NodePath("behavior_indicator")
        indicator.setPos(0, 0, 2.5)  # Above vehicle
        indicator.setScale(0.3)
        indicator.setColor(0.0, 0.0, 1.0, 0.8)  # Blue by default
        indicator.reparentTo(vehicle_node)
        
        return indicator
    
    def _update_vehicle_trail(self, instance: VehicleInstance, position: Point3D) -> None:
        """Update the trail behind a vehicle."""
        # Add current position to trail
        instance.trail_points.append(position)
        
        # Limit trail length
        if len(instance.trail_points) > self.trail_length:
            instance.trail_points.pop(0)
        
        # Update trail visualization (simplified for now)
        # In full implementation, would create/update trail geometry
    
    def _update_behavior_indicators(self, instance: VehicleInstance, position: Point3D, heading: float) -> None:
        """Update behavior indicators based on vehicle state."""
        if not PANDA3D_AVAILABLE:
            return
        
        # Update speed indicator color based on speed
        if "speed" in instance.behavior_indicators:
            speed_indicator = instance.behavior_indicators["speed"]
            # Color from green (slow) to red (fast)
            # This would use actual speed data in full implementation
            speed_indicator.setColor(0.5, 1.0, 0.0, 0.8)
        
        # Update behavior indicator
        if "behavior" in instance.behavior_indicators:
            behavior_indicator = instance.behavior_indicators["behavior"]
            # This would reflect actual behavior state in full implementation
            behavior_indicator.setColor(0.0, 0.0, 1.0, 0.8)
    
    def _create_path_animation(self, instance: VehicleInstance, path: List[Point3D], duration: float) -> Optional[Any]:
        """Create animation sequence for path following."""
        if not PANDA3D_AVAILABLE or len(path) < 2:
            return None
        
        # Create position intervals for each segment
        intervals = []
        segment_duration = duration / (len(path) - 1)
        
        for i in range(len(path) - 1):
            start_pos = Point3(path[i].x, path[i].y, path[i].z)
            end_pos = Point3(path[i + 1].x, path[i + 1].y, path[i + 1].z)
            
            # Position animation
            pos_interval = LerpPosInterval(
                instance.node_path,
                segment_duration,
                end_pos,
                startPos=start_pos
            )
            
            # Calculate heading for this segment
            dx = path[i + 1].x - path[i].x
            dy = path[i + 1].y - path[i].y
            heading = math.degrees(math.atan2(dy, dx))
            
            # Heading animation
            hpr_interval = LerpHprInterval(
                instance.node_path,
                segment_duration,
                Vec3(heading, 0, 0)
            )
            
            # Combine position and heading
            combined_interval = Parallel(pos_interval, hpr_interval)
            intervals.append(combined_interval)
        
        # Create sequence of all intervals
        return Sequence(*intervals)
    
    def _clear_interaction_visuals(self) -> None:
        """Clear existing interaction visuals."""
        for interaction_visual in self.interaction_visuals.values():
            for element in interaction_visual.visual_elements:
                if PANDA3D_AVAILABLE:
                    element.removeNode()
        
        self.interaction_visuals.clear()
    
    def _create_interaction_visual(self, interaction: Dict[str, Any]) -> None:
        """Create visual representation of a vehicle interaction."""
        if not PANDA3D_AVAILABLE:
            return
        
        interaction_type = interaction.get("type", "unknown")
        primary_id = interaction.get("primary_vehicle_id")
        secondary_id = interaction.get("secondary_vehicle_id")
        
        if primary_id not in self.vehicle_instances or secondary_id not in self.vehicle_instances:
            return
        
        primary_vehicle = self.vehicle_instances[primary_id]
        secondary_vehicle = self.vehicle_instances[secondary_id]
        
        # Create visual elements based on interaction type
        visual_elements = []
        
        if interaction_type == "overtaking":
            # Create arrow or line showing overtaking maneuver
            visual_elements.extend(self._create_overtaking_visual(primary_vehicle, secondary_vehicle))
        elif interaction_type == "following":
            # Create line showing following relationship
            visual_elements.extend(self._create_following_visual(primary_vehicle, secondary_vehicle))
        
        # Store interaction visual
        interaction_id = f"{primary_id}_{secondary_id}_{interaction_type}"
        self.interaction_visuals[interaction_id] = VehicleInteractionVisual(
            interaction_type=interaction_type,
            primary_vehicle_id=primary_id,
            secondary_vehicle_id=secondary_id,
            intensity=interaction.get("intensity", 1.0),
            duration=interaction.get("duration", 5.0),
            visual_elements=visual_elements
        )
    
    def _create_overtaking_visual(self, primary: VehicleInstance, secondary: VehicleInstance) -> List[NodePath]:
        """Create visual elements for overtaking interaction."""
        if not PANDA3D_AVAILABLE:
            return []
        
        # Create curved arrow from secondary to primary vehicle
        # Simplified implementation - would create proper curved geometry in full version
        arrow_node = NodePath("overtaking_arrow")
        arrow_node.setColor(1.0, 1.0, 0.0, 0.8)  # Yellow
        arrow_node.reparentTo(self.effects_node)
        
        return [arrow_node]
    
    def _create_following_visual(self, primary: VehicleInstance, secondary: VehicleInstance) -> List[NodePath]:
        """Create visual elements for following interaction."""
        if not PANDA3D_AVAILABLE:
            return []
        
        # Create line connecting the vehicles
        line_node = NodePath("following_line")
        line_node.setColor(0.5, 0.5, 1.0, 0.6)  # Light blue
        line_node.reparentTo(self.effects_node)
        
        return [line_node]