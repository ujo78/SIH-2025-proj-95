"""
Performance Optimizer Implementation

This module implements advanced performance optimization features including
vehicle culling, level-of-detail systems, spatial partitioning, adaptive
quality settings, and memory pooling for large-scale traffic simulations.
"""

import math
import time
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import weakref

try:
    from panda3d.core import (
        NodePath, Vec3, Point3, BoundingSphere, CollisionTraverser,
        CollisionNode, CollisionSphere, BitMask32, PythonTask,
        TaskManager, ClockObject
    )
    PANDA3D_AVAILABLE = True
except ImportError:
    PANDA3D_AVAILABLE = False
    # Mock classes for development without Panda3D
    class NodePath:
        def __init__(self, *args): pass
        def setPos(self, *args): pass
        def getPos(self): return (0, 0, 0)
        def getDistance(self, other): return 0.0
        def show(self): pass
        def hide(self): pass
        def removeNode(self): pass
    
    Vec3 = Point3 = lambda *args: None
    BoundingSphere = CollisionNode = CollisionSphere = lambda *args: None

from indian_features.interfaces import Point3D
from indian_features.enums import VehicleType


class LODLevel(Enum):
    """Level of Detail enumeration"""
    HIGH = 0      # Full detail, close to camera
    MEDIUM = 1    # Reduced detail, medium distance
    LOW = 2       # Minimal detail, far distance
    CULLED = 3    # Not rendered, too far or occluded


class QualityLevel(Enum):
    """Rendering quality levels"""
    ULTRA = 0     # Maximum quality
    HIGH = 1      # High quality
    MEDIUM = 2    # Medium quality
    LOW = 3       # Low quality
    MINIMAL = 4   # Minimal quality for performance


@dataclass
class PerformanceMetrics:
    """Performance monitoring metrics"""
    frame_rate: float = 0.0
    frame_time: float = 0.0
    visible_vehicles: int = 0
    total_vehicles: int = 0
    culled_vehicles: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    gpu_usage_percent: float = 0.0
    spatial_queries_per_frame: int = 0
    lod_transitions_per_frame: int = 0


@dataclass
class SpatialCell:
    """Spatial partitioning cell"""
    cell_id: Tuple[int, int]
    bounds: Tuple[Point3D, Point3D]  # min, max corners
    vehicles: Set[int] = field(default_factory=set)
    last_update: float = 0.0
    is_dirty: bool = True


@dataclass
class VehicleLOD:
    """Vehicle Level of Detail data"""
    vehicle_id: int
    current_lod: LODLevel
    distance_to_camera: float
    last_lod_update: float
    node_paths: Dict[LODLevel, Optional[NodePath]] = field(default_factory=dict)
    is_visible: bool = True
    is_in_frustum: bool = True


@dataclass
class PooledObject:
    """Pooled object for memory management"""
    object_id: str
    object_type: str
    instance: Any
    is_active: bool = False
    last_used: float = 0.0
    creation_time: float = 0.0


class SpatialPartitioner:
    """
    Spatial partitioning system for efficient collision detection and culling.
    Uses a grid-based approach for fast spatial queries.
    """
    
    def __init__(self, world_bounds: Tuple[Point3D, Point3D], cell_size: float = 100.0):
        """
        Initialize spatial partitioner.
        
        Args:
            world_bounds: (min_point, max_point) defining world boundaries
            cell_size: Size of each spatial cell in world units
        """
        self.world_min, self.world_max = world_bounds
        self.cell_size = cell_size
        
        # Calculate grid dimensions
        self.grid_width = int(math.ceil((self.world_max.x - self.world_min.x) / cell_size))
        self.grid_height = int(math.ceil((self.world_max.y - self.world_min.y) / cell_size))
        
        # Spatial grid
        self.cells: Dict[Tuple[int, int], SpatialCell] = {}
        self.vehicle_positions: Dict[int, Point3D] = {}
        self.vehicle_cells: Dict[int, Tuple[int, int]] = {}
        
        # Performance tracking
        self.query_count = 0
        self.last_query_reset = time.time()
        
        print(f"Initialized spatial partitioner: {self.grid_width}x{self.grid_height} cells")
    
    def get_cell_coords(self, position: Point3D) -> Tuple[int, int]:
        """Get cell coordinates for a world position."""
        cell_x = int((position.x - self.world_min.x) / self.cell_size)
        cell_y = int((position.y - self.world_min.y) / self.cell_size)
        
        # Clamp to grid bounds
        cell_x = max(0, min(self.grid_width - 1, cell_x))
        cell_y = max(0, min(self.grid_height - 1, cell_y))
        
        return (cell_x, cell_y)
    
    def get_or_create_cell(self, cell_coords: Tuple[int, int]) -> SpatialCell:
        """Get or create a spatial cell."""
        if cell_coords not in self.cells:
            cell_x, cell_y = cell_coords
            
            # Calculate cell bounds
            min_x = self.world_min.x + cell_x * self.cell_size
            min_y = self.world_min.y + cell_y * self.cell_size
            max_x = min_x + self.cell_size
            max_y = min_y + self.cell_size
            
            min_point = Point3D(min_x, min_y, self.world_min.z)
            max_point = Point3D(max_x, max_y, self.world_max.z)
            
            self.cells[cell_coords] = SpatialCell(
                cell_id=cell_coords,
                bounds=(min_point, max_point),
                last_update=time.time()
            )
        
        return self.cells[cell_coords]
    
    def update_vehicle_position(self, vehicle_id: int, position: Point3D) -> None:
        """Update vehicle position in spatial grid."""
        old_cell_coords = self.vehicle_cells.get(vehicle_id)
        new_cell_coords = self.get_cell_coords(position)
        
        # Remove from old cell if changed
        if old_cell_coords and old_cell_coords != new_cell_coords:
            if old_cell_coords in self.cells:
                self.cells[old_cell_coords].vehicles.discard(vehicle_id)
                self.cells[old_cell_coords].is_dirty = True
        
        # Add to new cell
        new_cell = self.get_or_create_cell(new_cell_coords)
        new_cell.vehicles.add(vehicle_id)
        new_cell.is_dirty = True
        new_cell.last_update = time.time()
        
        # Update tracking
        self.vehicle_positions[vehicle_id] = position
        self.vehicle_cells[vehicle_id] = new_cell_coords
    
    def remove_vehicle(self, vehicle_id: int) -> None:
        """Remove vehicle from spatial grid."""
        if vehicle_id in self.vehicle_cells:
            cell_coords = self.vehicle_cells[vehicle_id]
            if cell_coords in self.cells:
                self.cells[cell_coords].vehicles.discard(vehicle_id)
                self.cells[cell_coords].is_dirty = True
            
            del self.vehicle_cells[vehicle_id]
            del self.vehicle_positions[vehicle_id]
    
    def query_nearby_vehicles(self, position: Point3D, radius: float) -> List[int]:
        """Query vehicles within radius of position."""
        self.query_count += 1
        
        nearby_vehicles = []
        
        # Calculate search area in cells
        cell_radius = int(math.ceil(radius / self.cell_size))
        center_cell = self.get_cell_coords(position)
        
        # Search surrounding cells
        for dx in range(-cell_radius, cell_radius + 1):
            for dy in range(-cell_radius, cell_radius + 1):
                cell_x = center_cell[0] + dx
                cell_y = center_cell[1] + dy
                
                if (0 <= cell_x < self.grid_width and 0 <= cell_y < self.grid_height):
                    cell_coords = (cell_x, cell_y)
                    if cell_coords in self.cells:
                        cell = self.cells[cell_coords]
                        
                        # Check each vehicle in cell
                        for vehicle_id in cell.vehicles:
                            if vehicle_id in self.vehicle_positions:
                                vehicle_pos = self.vehicle_positions[vehicle_id]
                                distance = self._calculate_distance(position, vehicle_pos)
                                
                                if distance <= radius:
                                    nearby_vehicles.append(vehicle_id)
        
        return nearby_vehicles
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get spatial partitioner performance statistics."""
        current_time = time.time()
        time_elapsed = current_time - self.last_query_reset
        
        stats = {
            'total_cells': len(self.cells),
            'active_cells': sum(1 for cell in self.cells.values() if len(cell.vehicles) > 0),
            'total_vehicles': len(self.vehicle_positions),
            'queries_per_second': self.query_count / max(0.001, time_elapsed),
            'average_vehicles_per_cell': (
                sum(len(cell.vehicles) for cell in self.cells.values()) / 
                max(1, len(self.cells))
            )
        }
        
        # Reset query counter
        if time_elapsed > 1.0:
            self.query_count = 0
            self.last_query_reset = current_time
        
        return stats
    
    def _calculate_distance(self, pos1: Point3D, pos2: Point3D) -> float:
        """Calculate distance between two points."""
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        dz = pos1.z - pos2.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)


class MemoryPool:
    """
    Memory pool for efficient object reuse and garbage collection management.
    """
    
    def __init__(self, max_pool_size: int = 1000):
        """
        Initialize memory pool.
        
        Args:
            max_pool_size: Maximum number of objects to keep in pool
        """
        self.max_pool_size = max_pool_size
        self.pools: Dict[str, List[PooledObject]] = defaultdict(list)
        self.active_objects: Dict[str, PooledObject] = {}
        self.object_counter = 0
        self.total_created = 0
        self.total_reused = 0
        
        # Cleanup settings
        self.cleanup_interval = 30.0  # seconds
        self.max_idle_time = 60.0     # seconds
        self.last_cleanup = time.time()
    
    def acquire_object(self, object_type: str, factory_func: callable) -> Tuple[str, Any]:
        """
        Acquire an object from the pool or create new one.
        
        Args:
            object_type: Type identifier for the object
            factory_func: Function to create new object if pool is empty
            
        Returns:
            Tuple of (object_id, object_instance)
        """
        current_time = time.time()
        
        # Try to reuse from pool
        if object_type in self.pools and self.pools[object_type]:
            pooled_obj = self.pools[object_type].pop()
            pooled_obj.is_active = True
            pooled_obj.last_used = current_time
            
            self.active_objects[pooled_obj.object_id] = pooled_obj
            self.total_reused += 1
            
            return pooled_obj.object_id, pooled_obj.instance
        
        # Create new object
        self.object_counter += 1
        object_id = f"{object_type}_{self.object_counter}"
        
        try:
            instance = factory_func()
            
            pooled_obj = PooledObject(
                object_id=object_id,
                object_type=object_type,
                instance=instance,
                is_active=True,
                last_used=current_time,
                creation_time=current_time
            )
            
            self.active_objects[object_id] = pooled_obj
            self.total_created += 1
            
            return object_id, instance
            
        except Exception as e:
            print(f"Error creating object of type {object_type}: {e}")
            return None, None
    
    def release_object(self, object_id: str) -> bool:
        """
        Release an object back to the pool.
        
        Args:
            object_id: ID of the object to release
            
        Returns:
            True if object was released successfully
        """
        if object_id not in self.active_objects:
            return False
        
        pooled_obj = self.active_objects[object_id]
        pooled_obj.is_active = False
        pooled_obj.last_used = time.time()
        
        # Add back to pool if there's space
        object_type = pooled_obj.object_type
        if len(self.pools[object_type]) < self.max_pool_size:
            self.pools[object_type].append(pooled_obj)
        else:
            # Pool is full, destroy the object
            self._destroy_object(pooled_obj)
        
        del self.active_objects[object_id]
        return True
    
    def cleanup_idle_objects(self) -> int:
        """
        Clean up idle objects that haven't been used recently.
        
        Returns:
            Number of objects cleaned up
        """
        current_time = time.time()
        
        if current_time - self.last_cleanup < self.cleanup_interval:
            return 0
        
        cleaned_count = 0
        
        # Clean up each pool
        for object_type, pool in self.pools.items():
            objects_to_remove = []
            
            for pooled_obj in pool:
                if current_time - pooled_obj.last_used > self.max_idle_time:
                    objects_to_remove.append(pooled_obj)
            
            # Remove idle objects
            for obj in objects_to_remove:
                pool.remove(obj)
                self._destroy_object(obj)
                cleaned_count += 1
        
        self.last_cleanup = current_time
        return cleaned_count
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get memory pool statistics."""
        total_pooled = sum(len(pool) for pool in self.pools.values())
        
        return {
            'total_created': self.total_created,
            'total_reused': self.total_reused,
            'reuse_ratio': self.total_reused / max(1, self.total_created + self.total_reused),
            'active_objects': len(self.active_objects),
            'pooled_objects': total_pooled,
            'pool_types': len(self.pools),
            'pools_by_type': {
                obj_type: len(pool) for obj_type, pool in self.pools.items()
            }
        }
    
    def _destroy_object(self, pooled_obj: PooledObject) -> None:
        """Destroy a pooled object and clean up resources."""
        try:
            # If it's a Panda3D NodePath, remove it properly
            if PANDA3D_AVAILABLE and hasattr(pooled_obj.instance, 'removeNode'):
                pooled_obj.instance.removeNode()
            
            # Clear reference
            pooled_obj.instance = None
            
        except Exception as e:
            print(f"Error destroying object {pooled_obj.object_id}: {e}")


class PerformanceOptimizer:
    """
    Main performance optimization system that coordinates all optimization features.
    """
    
    def __init__(self, render_root: Optional[NodePath] = None):
        """
        Initialize performance optimizer.
        
        Args:
            render_root: Root node for rendering (optional, for testing)
        """
        self.render = render_root
        self.panda3d_enabled = PANDA3D_AVAILABLE and render_root is not None
        
        # Performance settings
        self.target_fps = 60.0
        self.min_fps = 30.0
        self.max_visible_vehicles = 200
        self.lod_distances = {
            LODLevel.HIGH: 100.0,
            LODLevel.MEDIUM: 300.0,
            LODLevel.LOW: 800.0,
            LODLevel.CULLED: 1500.0
        }
        
        # Current quality level
        self.current_quality = QualityLevel.HIGH
        self.adaptive_quality_enabled = True
        
        # Initialize subsystems
        world_bounds = (Point3D(-2000, -2000, -10), Point3D(2000, 2000, 100))
        self.spatial_partitioner = SpatialPartitioner(world_bounds, cell_size=150.0)
        self.memory_pool = MemoryPool(max_pool_size=500)
        
        # Vehicle management
        self.vehicle_lods: Dict[int, VehicleLOD] = {}
        self.camera_position = Point3D(0, 0, 0)
        self.camera_direction = Point3D(0, 1, 0)
        
        # Performance monitoring
        self.metrics = PerformanceMetrics()
        self.frame_times = []
        self.max_frame_history = 60
        
        # Update intervals
        self.lod_update_interval = 0.1  # 10 FPS
        self.culling_update_interval = 0.05  # 20 FPS
        self.quality_update_interval = 1.0  # 1 FPS
        
        self.last_lod_update = 0.0
        self.last_culling_update = 0.0
        self.last_quality_update = 0.0
        
        # Threading for background tasks
        self.optimization_thread = None
        self.should_stop_optimization = False
        
        print("Performance optimizer initialized")
    
    def register_vehicle(self, vehicle_id: int, position: Point3D, 
                        node_paths: Dict[LODLevel, NodePath]) -> None:
        """
        Register a vehicle for performance optimization.
        
        Args:
            vehicle_id: Unique vehicle identifier
            position: Vehicle's world position
            node_paths: Dictionary mapping LOD levels to NodePath objects
        """
        # Create LOD data
        vehicle_lod = VehicleLOD(
            vehicle_id=vehicle_id,
            current_lod=LODLevel.HIGH,
            distance_to_camera=0.0,
            last_lod_update=time.time(),
            node_paths=node_paths
        )
        
        self.vehicle_lods[vehicle_id] = vehicle_lod
        
        # Register with spatial partitioner
        self.spatial_partitioner.update_vehicle_position(vehicle_id, position)
        
        # Initially show only high LOD
        self._set_vehicle_lod(vehicle_id, LODLevel.HIGH)
    
    def unregister_vehicle(self, vehicle_id: int) -> None:
        """
        Unregister a vehicle from optimization.
        
        Args:
            vehicle_id: Vehicle identifier to remove
        """
        if vehicle_id in self.vehicle_lods:
            vehicle_lod = self.vehicle_lods[vehicle_id]
            
            # Hide all LOD levels
            for lod_level, node_path in vehicle_lod.node_paths.items():
                if node_path and self.panda3d_enabled:
                    node_path.hide()
            
            del self.vehicle_lods[vehicle_id]
        
        # Remove from spatial partitioner
        self.spatial_partitioner.remove_vehicle(vehicle_id)
    
    def update_vehicle_position(self, vehicle_id: int, position: Point3D) -> None:
        """
        Update vehicle position for optimization calculations.
        
        Args:
            vehicle_id: Vehicle identifier
            position: New world position
        """
        if vehicle_id in self.vehicle_lods:
            # Update spatial partitioner
            self.spatial_partitioner.update_vehicle_position(vehicle_id, position)
            
            # Update distance to camera
            distance = self._calculate_distance(position, self.camera_position)
            self.vehicle_lods[vehicle_id].distance_to_camera = distance
    
    def update_camera_position(self, position: Point3D, direction: Point3D) -> None:
        """
        Update camera position and direction for optimization.
        
        Args:
            position: Camera world position
            direction: Camera look direction
        """
        self.camera_position = position
        self.camera_direction = direction
    
    def update_optimization(self, delta_time: float) -> None:
        """
        Main optimization update loop.
        
        Args:
            delta_time: Time elapsed since last update
        """
        current_time = time.time()
        
        # Update performance metrics
        self._update_performance_metrics(delta_time)
        
        # Update LOD system
        if current_time - self.last_lod_update >= self.lod_update_interval:
            self._update_lod_system()
            self.last_lod_update = current_time
        
        # Update culling system
        if current_time - self.last_culling_update >= self.culling_update_interval:
            self._update_culling_system()
            self.last_culling_update = current_time
        
        # Update adaptive quality
        if (self.adaptive_quality_enabled and 
            current_time - self.last_quality_update >= self.quality_update_interval):
            self._update_adaptive_quality()
            self.last_quality_update = current_time
        
        # Cleanup memory pool
        self.memory_pool.cleanup_idle_objects()
    
    def set_quality_level(self, quality: QualityLevel) -> None:
        """
        Manually set rendering quality level.
        
        Args:
            quality: Target quality level
        """
        if quality != self.current_quality:
            self.current_quality = quality
            self._apply_quality_settings(quality)
            print(f"Quality level set to: {quality.name}")
    
    def enable_adaptive_quality(self, enabled: bool) -> None:
        """
        Enable or disable adaptive quality adjustment.
        
        Args:
            enabled: Whether to enable adaptive quality
        """
        self.adaptive_quality_enabled = enabled
        print(f"Adaptive quality {'enabled' if enabled else 'disabled'}")
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        return self.metrics
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics."""
        spatial_stats = self.spatial_partitioner.get_performance_stats()
        pool_stats = self.memory_pool.get_pool_stats()
        
        lod_distribution = defaultdict(int)
        for vehicle_lod in self.vehicle_lods.values():
            lod_distribution[vehicle_lod.current_lod.name] += 1
        
        return {
            'performance_metrics': {
                'frame_rate': self.metrics.frame_rate,
                'frame_time_ms': self.metrics.frame_time * 1000,
                'visible_vehicles': self.metrics.visible_vehicles,
                'total_vehicles': self.metrics.total_vehicles,
                'culled_vehicles': self.metrics.culled_vehicles,
                'memory_usage_mb': self.metrics.memory_usage_mb
            },
            'quality_settings': {
                'current_quality': self.current_quality.name,
                'adaptive_enabled': self.adaptive_quality_enabled,
                'target_fps': self.target_fps,
                'min_fps': self.min_fps
            },
            'lod_system': {
                'lod_distribution': dict(lod_distribution),
                'lod_distances': {level.name: dist for level, dist in self.lod_distances.items()}
            },
            'spatial_partitioning': spatial_stats,
            'memory_pool': pool_stats
        }
    
    def _update_performance_metrics(self, delta_time: float) -> None:
        """Update performance monitoring metrics."""
        # Calculate frame rate
        if delta_time > 0:
            current_fps = 1.0 / delta_time
            self.frame_times.append(delta_time)
            
            # Keep frame history limited
            if len(self.frame_times) > self.max_frame_history:
                self.frame_times.pop(0)
            
            # Calculate average FPS
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            self.metrics.frame_rate = 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
            self.metrics.frame_time = avg_frame_time
        
        # Update vehicle counts
        self.metrics.total_vehicles = len(self.vehicle_lods)
        self.metrics.visible_vehicles = sum(
            1 for lod in self.vehicle_lods.values() 
            if lod.is_visible and lod.current_lod != LODLevel.CULLED
        )
        self.metrics.culled_vehicles = sum(
            1 for lod in self.vehicle_lods.values() 
            if lod.current_lod == LODLevel.CULLED
        )
        
        # Update spatial query count
        spatial_stats = self.spatial_partitioner.get_performance_stats()
        self.metrics.spatial_queries_per_frame = int(spatial_stats.get('queries_per_second', 0) / 60.0)
    
    def _update_lod_system(self) -> None:
        """Update Level of Detail for all vehicles."""
        lod_transitions = 0
        
        for vehicle_id, vehicle_lod in self.vehicle_lods.items():
            # Calculate appropriate LOD level based on distance
            new_lod = self._calculate_lod_level(vehicle_lod.distance_to_camera)
            
            if new_lod != vehicle_lod.current_lod:
                self._set_vehicle_lod(vehicle_id, new_lod)
                lod_transitions += 1
        
        self.metrics.lod_transitions_per_frame = lod_transitions
    
    def _calculate_lod_level(self, distance: float) -> LODLevel:
        """Calculate appropriate LOD level based on distance."""
        # Adjust distances based on current quality level
        quality_multiplier = self._get_quality_distance_multiplier()
        
        adjusted_distances = {
            level: dist * quality_multiplier 
            for level, dist in self.lod_distances.items()
        }
        
        if distance <= adjusted_distances[LODLevel.HIGH]:
            return LODLevel.HIGH
        elif distance <= adjusted_distances[LODLevel.MEDIUM]:
            return LODLevel.MEDIUM
        elif distance <= adjusted_distances[LODLevel.LOW]:
            return LODLevel.LOW
        else:
            return LODLevel.CULLED
    
    def _get_quality_distance_multiplier(self) -> float:
        """Get distance multiplier based on current quality level."""
        multipliers = {
            QualityLevel.ULTRA: 1.5,
            QualityLevel.HIGH: 1.0,
            QualityLevel.MEDIUM: 0.8,
            QualityLevel.LOW: 0.6,
            QualityLevel.MINIMAL: 0.4
        }
        return multipliers.get(self.current_quality, 1.0)
    
    def _set_vehicle_lod(self, vehicle_id: int, lod_level: LODLevel) -> None:
        """Set LOD level for a specific vehicle."""
        if vehicle_id not in self.vehicle_lods:
            return
        
        vehicle_lod = self.vehicle_lods[vehicle_id]
        old_lod = vehicle_lod.current_lod
        
        if not self.panda3d_enabled:
            vehicle_lod.current_lod = lod_level
            return
        
        # Hide old LOD
        if old_lod in vehicle_lod.node_paths and vehicle_lod.node_paths[old_lod]:
            vehicle_lod.node_paths[old_lod].hide()
        
        # Show new LOD
        if lod_level != LODLevel.CULLED:
            if lod_level in vehicle_lod.node_paths and vehicle_lod.node_paths[lod_level]:
                vehicle_lod.node_paths[lod_level].show()
                vehicle_lod.is_visible = True
            else:
                # Fallback to lower LOD if specific level not available
                fallback_lod = self._find_fallback_lod(vehicle_lod.node_paths, lod_level)
                if fallback_lod and vehicle_lod.node_paths[fallback_lod]:
                    vehicle_lod.node_paths[fallback_lod].show()
                    vehicle_lod.is_visible = True
        else:
            vehicle_lod.is_visible = False
        
        vehicle_lod.current_lod = lod_level
        vehicle_lod.last_lod_update = time.time()
    
    def _find_fallback_lod(self, node_paths: Dict[LODLevel, NodePath], 
                          target_lod: LODLevel) -> Optional[LODLevel]:
        """Find best available fallback LOD level."""
        # Try lower quality levels first
        fallback_order = [LODLevel.HIGH, LODLevel.MEDIUM, LODLevel.LOW]
        
        for lod in fallback_order:
            if lod in node_paths and node_paths[lod]:
                return lod
        
        return None
    
    def _update_culling_system(self) -> None:
        """Update frustum culling and occlusion culling."""
        # Simplified frustum culling - in full implementation would use proper frustum
        visible_count = 0
        
        for vehicle_id, vehicle_lod in self.vehicle_lods.items():
            # Simple distance-based culling for now
            is_in_range = vehicle_lod.distance_to_camera <= self.lod_distances[LODLevel.CULLED]
            
            # Check if vehicle should be visible
            should_be_visible = (is_in_range and 
                               visible_count < self.max_visible_vehicles and
                               vehicle_lod.current_lod != LODLevel.CULLED)
            
            if should_be_visible != vehicle_lod.is_visible:
                if self.panda3d_enabled:
                    for lod_level, node_path in vehicle_lod.node_paths.items():
                        if node_path:
                            if should_be_visible and lod_level == vehicle_lod.current_lod:
                                node_path.show()
                            else:
                                node_path.hide()
                
                vehicle_lod.is_visible = should_be_visible
            
            if should_be_visible:
                visible_count += 1
    
    def _update_adaptive_quality(self) -> None:
        """Update quality level based on performance."""
        current_fps = self.metrics.frame_rate
        
        # Determine if quality adjustment is needed
        if current_fps < self.min_fps and self.current_quality != QualityLevel.MINIMAL:
            # Decrease quality
            new_quality_value = min(QualityLevel.MINIMAL.value, self.current_quality.value + 1)
            new_quality = QualityLevel(new_quality_value)
            self.set_quality_level(new_quality)
            
        elif (current_fps > self.target_fps * 1.2 and 
              self.current_quality != QualityLevel.ULTRA):
            # Increase quality
            new_quality_value = max(QualityLevel.ULTRA.value, self.current_quality.value - 1)
            new_quality = QualityLevel(new_quality_value)
            self.set_quality_level(new_quality)
    
    def _apply_quality_settings(self, quality: QualityLevel) -> None:
        """Apply quality-specific settings."""
        # Adjust LOD distances based on quality
        base_distances = {
            LODLevel.HIGH: 100.0,
            LODLevel.MEDIUM: 300.0,
            LODLevel.LOW: 800.0,
            LODLevel.CULLED: 1500.0
        }
        
        quality_multipliers = {
            QualityLevel.ULTRA: 1.5,
            QualityLevel.HIGH: 1.0,
            QualityLevel.MEDIUM: 0.8,
            QualityLevel.LOW: 0.6,
            QualityLevel.MINIMAL: 0.4
        }
        
        multiplier = quality_multipliers.get(quality, 1.0)
        self.lod_distances = {
            level: dist * multiplier 
            for level, dist in base_distances.items()
        }
        
        # Adjust maximum visible vehicles
        max_vehicles_by_quality = {
            QualityLevel.ULTRA: 300,
            QualityLevel.HIGH: 200,
            QualityLevel.MEDIUM: 150,
            QualityLevel.LOW: 100,
            QualityLevel.MINIMAL: 50
        }
        
        self.max_visible_vehicles = max_vehicles_by_quality.get(quality, 200)
    
    def _calculate_distance(self, pos1: Point3D, pos2: Point3D) -> float:
        """Calculate distance between two points."""
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        dz = pos1.z - pos2.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)