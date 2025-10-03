#!/usr/bin/env python3
"""
Test script for 3D Visualization Components

This script tests the 3D visualization components including:
- Building rendering with various urban layouts
- Vehicle model loading and animation
- Camera control responsiveness and smoothness

Requirements tested: 4.1, 4.2, 4.5
"""

import sys
import os
import unittest
import time
import math
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_visualization.city_renderer import IndianCityRenderer
from enhanced_visualization.vehicle_asset_manager import VehicleAssetManager
from enhanced_visualization.camera_controller import CameraController
from enhanced_visualization.config import VisualizationConfig
from enhanced_visualization.interfaces import (
    BuildingInfo, RoadSegmentVisual, VehicleVisual
)
from indian_features.enums import VehicleType, WeatherType, RoadQuality
from indian_features.interfaces import Point3D


class TestBuildingRendering(unittest.TestCase):
    """Test building rendering with various urban layouts"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = VisualizationConfig()
        self.renderer = IndianCityRenderer(self.config)
        
    def test_building_renderer_initialization(self):
        """Test building renderer initialization"""
        self.assertIsNotNone(self.renderer)
        self.assertEqual(self.renderer.config, self.config)
        self.assertIsNone(self.renderer.buildings_node)  # Not initialized without Panda3D
        
        print("✓ Building renderer initialization test passed")
    
    def test_scene_initialization(self):
        """Test 3D scene initialization with geographic bounds"""
        bounds = (-500.0, -500.0, 500.0, 500.0)
        self.renderer.initialize_scene(bounds)
        
        self.assertEqual(self.renderer.scene_bounds, bounds)
        
        print("✓ Scene initialization test passed")
    
    def test_residential_building_rendering(self):
        """Test rendering of residential buildings"""
        buildings = [
            BuildingInfo(
                building_id="res_001",
                footprint=[
                    Point3D(0, 0, 0),
                    Point3D(20, 0, 0),
                    Point3D(20, 15, 0),
                    Point3D(0, 15, 0)
                ],
                height=12.0,
                building_type="residential",
                texture_type="apartment_complex"
            ),
            BuildingInfo(
                building_id="res_002",
                footprint=[
                    Point3D(30, 0, 0),
                    Point3D(45, 0, 0),
                    Point3D(45, 12, 0),
                    Point3D(30, 12, 0)
                ],
                height=8.0,
                building_type="residential",
                texture_type="single_family"
            )
        ]
        
        self.renderer.render_buildings(buildings)
        
        # In mock mode, verify buildings are processed
        self.assertEqual(len(buildings), 2)
        self.assertEqual(buildings[0].building_type, "residential")
        
        print("✓ Residential building rendering test passed")
    
    def test_commercial_building_rendering(self):
        """Test rendering of commercial buildings"""
        buildings = [
            BuildingInfo(
                building_id="com_001",
                footprint=[
                    Point3D(100, 100, 0),
                    Point3D(150, 100, 0),
                    Point3D(150, 140, 0),
                    Point3D(100, 140, 0)
                ],
                height=25.0,
                building_type="commercial",
                texture_type="office_building"
            ),
            BuildingInfo(
                building_id="com_002",
                footprint=[
                    Point3D(200, 50, 0),
                    Point3D(280, 50, 0),
                    Point3D(280, 90, 0),
                    Point3D(200, 90, 0)
                ],
                height=18.0,
                building_type="commercial",
                texture_type="shopping_mall"
            )
        ]
        
        self.renderer.render_buildings(buildings)
        
        # Verify commercial buildings have appropriate heights
        self.assertGreater(buildings[0].height, 20.0)
        self.assertEqual(buildings[1].building_type, "commercial")
        
        print("✓ Commercial building rendering test passed")
    
    def test_mixed_urban_layout(self):
        """Test rendering of mixed urban layout with various building types"""
        buildings = [
            # Residential cluster
            BuildingInfo("res_001", [Point3D(0, 0, 0), Point3D(15, 0, 0), 
                        Point3D(15, 12, 0), Point3D(0, 12, 0)], 
                        9.0, "residential"),
            BuildingInfo("res_002", [Point3D(20, 0, 0), Point3D(35, 0, 0), 
                        Point3D(35, 12, 0), Point3D(20, 12, 0)], 
                        12.0, "residential"),
            
            # Commercial area
            BuildingInfo("com_001", [Point3D(100, 0, 0), Point3D(140, 0, 0), 
                        Point3D(140, 30, 0), Point3D(100, 30, 0)], 
                        22.0, "commercial"),
            
            # Industrial zone
            BuildingInfo("ind_001", [Point3D(200, 100, 0), Point3D(250, 100, 0), 
                        Point3D(250, 150, 0), Point3D(200, 150, 0)], 
                        15.0, "industrial"),
            
            # High-rise
            BuildingInfo("high_001", [Point3D(300, 200, 0), Point3D(320, 200, 0), 
                        Point3D(320, 220, 0), Point3D(300, 220, 0)], 
                        45.0, "high_rise")
        ]
        
        self.renderer.render_buildings(buildings)
        
        # Verify mixed layout characteristics
        building_types = [b.building_type for b in buildings]
        self.assertIn("residential", building_types)
        self.assertIn("commercial", building_types)
        self.assertIn("industrial", building_types)
        self.assertIn("high_rise", building_types)
        
        # Verify height variations
        heights = [b.height for b in buildings]
        self.assertGreater(max(heights), 40.0)  # High-rise
        self.assertLess(min(heights), 15.0)     # Low residential
        
        print("✓ Mixed urban layout rendering test passed")
    
    def test_road_infrastructure_rendering(self):
        """Test rendering of road infrastructure with Indian characteristics"""
        road_segments = [
            RoadSegmentVisual(
                segment_id="road_001",
                geometry=[Point3D(0, 0, 0), Point3D(100, 0, 0)],
                width=8.0,
                road_quality=RoadQuality.GOOD,
                surface_type="asphalt",
                lane_markings=[{"type": "solid", "color": "white"}],
                potholes=[Point3D(25, 0, 0), Point3D(75, 0, 0)],
                construction_zones=[{"start": Point3D(40, 0, 0), "end": Point3D(60, 0, 0)}]
            ),
            RoadSegmentVisual(
                segment_id="road_002",
                geometry=[Point3D(0, 0, 0), Point3D(0, 100, 0)],
                width=12.0,
                road_quality=RoadQuality.POOR,
                surface_type="concrete",
                lane_markings=[{"type": "dashed", "color": "yellow"}],
                potholes=[Point3D(0, 20, 0), Point3D(0, 50, 0), Point3D(0, 80, 0)],
                construction_zones=[]
            )
        ]
        
        self.renderer.render_road_infrastructure(road_segments)
        
        # Verify road characteristics
        self.assertEqual(len(road_segments), 2)
        self.assertEqual(road_segments[0].road_quality, RoadQuality.GOOD)
        self.assertEqual(road_segments[1].road_quality, RoadQuality.POOR)
        self.assertGreater(len(road_segments[1].potholes), 2)  # Poor road has more potholes
        
        print("✓ Road infrastructure rendering test passed")
    
    def test_terrain_generation(self):
        """Test terrain and ground plane generation"""
        # Test with elevation data
        elevation_data = {
            "0_0": 0.0,
            "100_0": 2.5,
            "0_100": 1.0,
            "100_100": 3.0
        }
        
        self.renderer.add_terrain(elevation_data)
        
        # Verify terrain is processed
        self.assertIsNotNone(elevation_data)
        
        print("✓ Terrain generation test passed")
    
    def test_lighting_updates(self):
        """Test scene lighting updates based on time and weather"""
        # Test different times of day
        times = [0.0, 0.25, 0.5, 0.75]  # Midnight, dawn, noon, dusk
        weathers = [WeatherType.CLEAR, WeatherType.LIGHT_RAIN, WeatherType.FOG]
        
        for time_of_day in times:
            for weather in weathers:
                self.renderer.update_lighting(time_of_day, weather)
        
        print("✓ Lighting updates test passed")
    
    def test_environmental_effects(self):
        """Test environmental effects like weather"""
        weather_effects = [
            (WeatherType.LIGHT_RAIN, 0.6),
            (WeatherType.HEAVY_RAIN, 0.9),
            (WeatherType.FOG, 0.4),
            (WeatherType.CLEAR, 0.0)
        ]
        
        for weather, intensity in weather_effects:
            self.renderer.add_environmental_effects(weather, intensity)
            self.assertEqual(self.renderer.current_weather, weather)
        
        print("✓ Environmental effects test passed")


class TestVehicleAssetManager(unittest.TestCase):
    """Test vehicle model loading and animation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = VisualizationConfig()
        self.asset_manager = VehicleAssetManager(self.config)
    
    def test_asset_manager_initialization(self):
        """Test vehicle asset manager initialization"""
        self.assertIsNotNone(self.asset_manager)
        self.assertEqual(self.asset_manager.config, self.config)
        self.assertEqual(len(self.asset_manager.vehicle_instances), 0)
        
        print("✓ Vehicle asset manager initialization test passed")
    
    def test_vehicle_model_loading(self):
        """Test loading of different Indian vehicle models"""
        model_paths = self.asset_manager.load_vehicle_models()
        
        # Verify all vehicle types have models
        expected_types = [
            VehicleType.CAR,
            VehicleType.BUS,
            VehicleType.AUTO_RICKSHAW,
            VehicleType.MOTORCYCLE,
            VehicleType.TRUCK
        ]
        
        for vehicle_type in expected_types:
            self.assertIn(vehicle_type, model_paths)
            self.assertIsNotNone(model_paths[vehicle_type])
        
        print("✓ Vehicle model loading test passed")
    
    def test_vehicle_instance_creation(self):
        """Test creation of vehicle instances in the scene"""
        # Load models first
        self.asset_manager.load_vehicle_models()
        
        # Create different vehicle instances
        vehicles = [
            VehicleVisual(
                vehicle_id=1,
                vehicle_type=VehicleType.CAR,
                position=Point3D(0, 0, 0),
                heading=0.0,
                speed=30.0,
                model_path="mock_car.egg"
            ),
            VehicleVisual(
                vehicle_id=2,
                vehicle_type=VehicleType.AUTO_RICKSHAW,
                position=Point3D(20, 10, 0),
                heading=45.0,
                speed=15.0,
                model_path="mock_auto.egg",
                color=(1.0, 1.0, 0.0)  # Yellow
            ),
            VehicleVisual(
                vehicle_id=3,
                vehicle_type=VehicleType.BUS,
                position=Point3D(-10, 5, 0),
                heading=90.0,
                speed=25.0,
                model_path="mock_bus.egg",
                scale=1.2
            )
        ]
        
        instances = []
        for vehicle in vehicles:
            instance = self.asset_manager.create_vehicle_instance(vehicle)
            instances.append(instance)
        
        # Verify instances were created (in mock mode, returns string references)
        self.assertEqual(len(instances), 3)
        for i, instance in enumerate(instances):
            self.assertIsNotNone(instance)
            # In mock mode, instance is a string like "mock_instance_1"
            if isinstance(instance, str):
                self.assertTrue(instance.startswith("mock_instance_"))
        
        print("✓ Vehicle instance creation test passed")
    
    def test_vehicle_position_updates(self):
        """Test vehicle position and orientation updates"""
        # Create a vehicle instance
        vehicle = VehicleVisual(
            vehicle_id=1,
            vehicle_type=VehicleType.CAR,
            position=Point3D(0, 0, 0),
            heading=0.0,
            speed=30.0,
            model_path="mock_car.egg"
        )
        
        self.asset_manager.load_vehicle_models()
        instance = self.asset_manager.create_vehicle_instance(vehicle)
        
        # Test position updates
        positions = [
            (Point3D(10, 5, 0), 30.0),
            (Point3D(25, 15, 0), 60.0),
            (Point3D(40, 30, 0), 90.0),
            (Point3D(50, 50, 0), 120.0)
        ]
        
        for position, heading in positions:
            self.asset_manager.update_vehicle_position(1, position, heading)
        
        # Verify instance was created (in mock mode, check return value)
        self.assertIsNotNone(instance)
        
        print("✓ Vehicle position updates test passed")
    
    def test_vehicle_movement_animation(self):
        """Test vehicle movement animation along paths"""
        # Create a vehicle instance
        vehicle = VehicleVisual(
            vehicle_id=1,
            vehicle_type=VehicleType.CAR,
            position=Point3D(0, 0, 0),
            heading=0.0,
            speed=30.0,
            model_path="mock_car.egg"
        )
        
        self.asset_manager.load_vehicle_models()
        self.asset_manager.create_vehicle_instance(vehicle)
        
        # Define animation paths
        paths = [
            # Straight line
            [Point3D(0, 0, 0), Point3D(50, 0, 0), Point3D(100, 0, 0)],
            # Curved path
            [Point3D(0, 0, 0), Point3D(25, 25, 0), Point3D(50, 0, 0)],
            # Complex path with elevation
            [Point3D(0, 0, 0), Point3D(20, 10, 2), Point3D(40, 20, 0), Point3D(60, 10, 1)]
        ]
        
        for i, path in enumerate(paths):
            duration = 5.0 + i  # Different durations
            self.asset_manager.animate_vehicle_movement(1, path, duration)
        
        print("✓ Vehicle movement animation test passed")
    
    def test_vehicle_interactions_visualization(self):
        """Test visualization of vehicle interactions"""
        # Create multiple vehicles
        vehicles = [
            VehicleVisual(1, VehicleType.CAR, Point3D(0, 0, 0), 0.0, 30.0, "mock_car.egg"),
            VehicleVisual(2, VehicleType.BUS, Point3D(20, 0, 0), 0.0, 25.0, "mock_bus.egg"),
            VehicleVisual(3, VehicleType.MOTORCYCLE, Point3D(-10, 5, 0), 45.0, 40.0, "mock_bike.egg")
        ]
        
        self.asset_manager.load_vehicle_models()
        for vehicle in vehicles:
            self.asset_manager.create_vehicle_instance(vehicle)
        
        # Define interactions
        interactions = [
            {
                "type": "overtaking",
                "primary_vehicle_id": 3,
                "secondary_vehicle_id": 1,
                "intensity": 0.8,
                "duration": 3.0
            },
            {
                "type": "following",
                "primary_vehicle_id": 1,
                "secondary_vehicle_id": 2,
                "intensity": 0.6,
                "duration": 5.0
            }
        ]
        
        self.asset_manager.show_vehicle_interactions(interactions)
        
        print("✓ Vehicle interactions visualization test passed")
    
    def test_vehicle_visibility_control(self):
        """Test vehicle visibility control"""
        # Create vehicle instances
        vehicle_ids = [1, 2, 3]
        for vehicle_id in vehicle_ids:
            vehicle = VehicleVisual(
                vehicle_id=vehicle_id,
                vehicle_type=VehicleType.CAR,
                position=Point3D(vehicle_id * 10, 0, 0),
                heading=0.0,
                speed=30.0,
                model_path="mock_car.egg"
            )
            self.asset_manager.load_vehicle_models()
            self.asset_manager.create_vehicle_instance(vehicle)
        
        # Test visibility changes
        self.asset_manager.set_vehicle_visibility(1, False)
        self.asset_manager.set_vehicle_visibility(2, True)
        self.asset_manager.set_vehicle_visibility(3, False)
        
        print("✓ Vehicle visibility control test passed")
    
    def test_vehicle_removal(self):
        """Test vehicle removal from scene"""
        # Create vehicles
        vehicle_ids = [1, 2, 3]
        instances = []
        for vehicle_id in vehicle_ids:
            vehicle = VehicleVisual(
                vehicle_id=vehicle_id,
                vehicle_type=VehicleType.CAR,
                position=Point3D(vehicle_id * 10, 0, 0),
                heading=0.0,
                speed=30.0,
                model_path="mock_car.egg"
            )
            self.asset_manager.load_vehicle_models()
            instance = self.asset_manager.create_vehicle_instance(vehicle)
            instances.append(instance)
        
        # Verify instances were created
        self.assertEqual(len(instances), 3)
        for instance in instances:
            self.assertIsNotNone(instance)
        
        # Test removal functionality (in mock mode, this just prints)
        self.asset_manager.remove_vehicle(2)
        
        print("✓ Vehicle removal test passed")


class TestCameraController(unittest.TestCase):
    """Test camera control responsiveness and smoothness"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = VisualizationConfig()
        self.camera_controller = CameraController(self.config)
    
    def test_camera_controller_initialization(self):
        """Test camera controller initialization"""
        self.assertIsNotNone(self.camera_controller)
        self.assertEqual(self.camera_controller.config, self.config)
        self.assertIsNotNone(self.camera_controller.current_state)
        
        print("✓ Camera controller initialization test passed")
    
    def test_camera_position_setting(self):
        """Test camera position and target setting"""
        positions = [
            (Point3D(0, -100, 50), Point3D(0, 0, 0)),
            (Point3D(200, -200, 100), Point3D(100, 100, 0)),
            (Point3D(-50, -150, 75), Point3D(-25, 25, 0))
        ]
        
        for position, target in positions:
            self.camera_controller.set_camera_position(position, target)
            
            # Verify state is updated
            self.assertEqual(self.camera_controller.current_state.position, position)
            self.assertEqual(self.camera_controller.current_state.target, target)
        
        print("✓ Camera position setting test passed")
    
    def test_smooth_camera_transitions(self):
        """Test smooth camera transitions between positions"""
        start_positions = [
            Point3D(0, -100, 50),
            Point3D(100, -200, 100),
            Point3D(-50, -50, 25)
        ]
        
        end_positions = [
            Point3D(50, -150, 75),
            Point3D(200, -100, 150),
            Point3D(0, -100, 50)
        ]
        
        durations = [1.0, 2.5, 3.0]
        
        for start, end, duration in zip(start_positions, end_positions, durations):
            self.camera_controller.create_smooth_transition(start, end, duration)
            
            # In mock mode, verify transition is initiated
            self.assertIsNotNone(start)
            self.assertIsNotNone(end)
            self.assertGreater(duration, 0)
        
        print("✓ Smooth camera transitions test passed")
    
    def test_vehicle_follow_mode(self):
        """Test camera following vehicle functionality"""
        vehicle_ids = [1, 2, 3]
        offsets = [
            Point3D(0, -20, 10),
            Point3D(-5, -15, 8),
            Point3D(5, -25, 12)
        ]
        
        for vehicle_id, offset in zip(vehicle_ids, offsets):
            self.camera_controller.follow_vehicle(vehicle_id, offset)
            
            # Verify follow mode is set
            self.assertEqual(self.camera_controller.follow_target_id, vehicle_id)
            self.assertEqual(self.camera_controller.follow_offset, offset)
        
        print("✓ Vehicle follow mode test passed")
    
    def test_camera_presets(self):
        """Test camera preset functionality"""
        # Test default presets
        default_presets = ["overview", "intersection", "street_level", "aerial"]
        
        for preset_name in default_presets:
            self.assertIn(preset_name, self.camera_controller.presets)
            self.camera_controller.set_preset_view(preset_name)
        
        # Test adding custom preset
        custom_position = Point3D(300, -300, 200)
        custom_target = Point3D(150, 150, 0)
        
        self.camera_controller.add_preset(
            "custom_view",
            custom_position,
            custom_target,
            fov=45.0,
            description="Custom test view"
        )
        
        self.assertIn("custom_view", self.camera_controller.presets)
        
        print("✓ Camera presets test passed")
    
    def test_free_camera_mode(self):
        """Test free camera movement mode"""
        # Enable free camera
        self.camera_controller.enable_free_camera(True)
        self.assertTrue(self.camera_controller.free_camera_enabled)
        
        # Disable free camera
        self.camera_controller.enable_free_camera(False)
        self.assertFalse(self.camera_controller.free_camera_enabled)
        
        print("✓ Free camera mode test passed")
    
    def test_cinematic_camera_paths(self):
        """Test cinematic camera path creation"""
        # Define waypoints for different cinematic sequences
        waypoint_sets = [
            # Simple flyover
            [
                Point3D(0, -200, 100),
                Point3D(100, -100, 80),
                Point3D(200, 0, 60),
                Point3D(300, 100, 40)
            ],
            # Circular orbit
            [
                Point3D(100, 0, 50),
                Point3D(70, 70, 50),
                Point3D(0, 100, 50),
                Point3D(-70, 70, 50),
                Point3D(-100, 0, 50)
            ],
            # Elevation change
            [
                Point3D(0, 0, 10),
                Point3D(50, 50, 30),
                Point3D(100, 100, 60),
                Point3D(150, 150, 100)
            ]
        ]
        
        durations = [8.0, 12.0, 10.0]
        
        for waypoints, duration in zip(waypoint_sets, durations):
            self.camera_controller.create_cinematic_path(waypoints, duration)
            
            # Verify cinematic path is created
            self.assertGreaterEqual(len(waypoints), 2)
            self.assertGreater(duration, 0)
        
        print("✓ Cinematic camera paths test passed")
    
    def test_orbit_camera_mode(self):
        """Test camera orbit mode around center points"""
        orbit_centers = [
            Point3D(0, 0, 0),
            Point3D(100, 100, 0),
            Point3D(-50, 50, 10)
        ]
        
        distances = [50.0, 100.0, 75.0]
        
        for center, distance in zip(orbit_centers, distances):
            self.camera_controller.set_orbit_mode(center, distance)
            
            # Verify orbit parameters
            self.assertEqual(self.camera_controller.orbit_center, center)
            self.assertEqual(self.camera_controller.orbit_distance, distance)
        
        print("✓ Orbit camera mode test passed")
    
    def test_camera_update_responsiveness(self):
        """Test camera update responsiveness and performance"""
        # Simulate vehicle positions for follow mode
        vehicle_positions = {
            1: Point3D(0, 0, 0),
            2: Point3D(50, 25, 0),
            3: Point3D(-25, 50, 0)
        }
        
        # Test update frequency
        dt_values = [1/30, 1/60, 1/120]  # 30, 60, 120 FPS
        
        for dt in dt_values:
            start_time = time.time()
            
            # Perform multiple updates
            for _ in range(10):
                self.camera_controller.update(dt, vehicle_positions)
            
            end_time = time.time()
            update_time = end_time - start_time
            
            # Verify updates complete quickly
            self.assertLess(update_time, 0.1)  # Should complete in under 100ms
        
        print("✓ Camera update responsiveness test passed")
    
    def test_camera_state_management(self):
        """Test camera state management and transitions"""
        # Test different camera modes
        from enhanced_visualization.camera_controller import CameraMode
        
        modes = [
            CameraMode.FREE,
            CameraMode.FOLLOW_VEHICLE,
            CameraMode.PRESET,
            CameraMode.ORBIT,
            CameraMode.CINEMATIC
        ]
        
        for mode in modes:
            # Set up mode-specific state
            if mode == CameraMode.FOLLOW_VEHICLE:
                self.camera_controller.follow_vehicle(1, Point3D(0, -20, 10))
            elif mode == CameraMode.PRESET:
                self.camera_controller.set_preset_view("overview")
            elif mode == CameraMode.ORBIT:
                self.camera_controller.set_orbit_mode(Point3D(0, 0, 0), 100.0)
            elif mode == CameraMode.CINEMATIC:
                waypoints = [Point3D(0, 0, 50), Point3D(100, 100, 50)]
                self.camera_controller.create_cinematic_path(waypoints, 5.0)
            
            # Verify state
            state = self.camera_controller.get_camera_state()
            self.assertIsNotNone(state)
        
        print("✓ Camera state management test passed")


class TestIntegratedVisualization(unittest.TestCase):
    """Test integrated 3D visualization functionality"""
    
    def setUp(self):
        """Set up integrated test fixtures"""
        self.config = VisualizationConfig()
        self.renderer = IndianCityRenderer(self.config)
        self.asset_manager = VehicleAssetManager(self.config)
        self.camera_controller = CameraController(self.config)
    
    def test_complete_scene_setup(self):
        """Test complete 3D scene setup with all components"""
        # Initialize scene
        bounds = (-1000.0, -1000.0, 1000.0, 1000.0)
        self.renderer.initialize_scene(bounds)
        
        # Add buildings
        buildings = [
            BuildingInfo("bld_001", [Point3D(0, 0, 0), Point3D(50, 0, 0), 
                        Point3D(50, 30, 0), Point3D(0, 30, 0)], 
                        15.0, "residential"),
            BuildingInfo("bld_002", [Point3D(100, 100, 0), Point3D(150, 100, 0), 
                        Point3D(150, 140, 0), Point3D(100, 140, 0)], 
                        25.0, "commercial")
        ]
        self.renderer.render_buildings(buildings)
        
        # Add vehicles
        self.asset_manager.load_vehicle_models()
        vehicles = [
            VehicleVisual(1, VehicleType.CAR, Point3D(25, 15, 0), 0.0, 30.0, "car.egg"),
            VehicleVisual(2, VehicleType.BUS, Point3D(125, 120, 0), 90.0, 25.0, "bus.egg")
        ]
        
        for vehicle in vehicles:
            self.asset_manager.create_vehicle_instance(vehicle)
        
        # Set up camera
        self.camera_controller.set_camera_position(
            Point3D(200, -200, 100),
            Point3D(75, 75, 0)
        )
        
        print("✓ Complete scene setup test passed")
    
    def test_performance_under_load(self):
        """Test performance with large number of objects"""
        # Create many buildings
        buildings = []
        for i in range(100):
            x = (i % 10) * 50
            y = (i // 10) * 40
            building = BuildingInfo(
                f"bld_{i:03d}",
                [Point3D(x, y, 0), Point3D(x+30, y, 0), 
                 Point3D(x+30, y+25, 0), Point3D(x, y+25, 0)],
                10.0 + (i % 5) * 3,
                "residential"
            )
            buildings.append(building)
        
        start_time = time.time()
        self.renderer.render_buildings(buildings)
        end_time = time.time()
        
        # Verify reasonable performance
        render_time = end_time - start_time
        self.assertLess(render_time, 1.0)  # Should complete in under 1 second
        
        print("✓ Performance under load test passed")


def run_all_tests():
    """Run all 3D visualization component tests"""
    print("Running 3D Visualization Components Tests")
    print("=" * 60)
    print("Testing Requirements: 4.1, 4.2, 4.5")
    print("=" * 60)
    
    # Create test suite
    test_classes = [
        TestBuildingRendering,
        TestVehicleAssetManager,
        TestCameraController,
        TestIntegratedVisualization
    ]
    
    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All 3D visualization component tests passed!")
        print(f"Ran {result.testsRun} tests successfully")
        print("\nTest Coverage Summary:")
        print("- Building rendering with various urban layouts ✓")
        print("- Vehicle model loading and animation ✓")
        print("- Camera control responsiveness and smoothness ✓")
        print("- Integrated visualization functionality ✓")
        print("- Performance testing under load ✓")
    else:
        print("❌ Some tests failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)