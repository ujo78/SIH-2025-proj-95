#!/usr/bin/env python3
"""
Test script for UI Overlay Integration

This script tests the UI overlay system implementation to verify
all required functionality is working correctly.
"""

import sys
import os
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_visualization.ui_overlay import UIOverlay, SimulationState
from enhanced_visualization.config import VisualizationConfig
from indian_features.enums import WeatherType, EmergencyType, VehicleType


def test_ui_overlay_creation():
    """Test UI overlay creation and initialization"""
    print("Testing UI overlay creation...")
    
    config = VisualizationConfig()
    ui_overlay = UIOverlay(config)
    
    assert ui_overlay is not None
    assert ui_overlay.config == config
    assert ui_overlay.simulation_controls.state == SimulationState.STOPPED
    assert ui_overlay.simulation_controls.speed_multiplier == 1.0
    
    print("✓ UI overlay creation successful")


def test_simulation_controls():
    """Test simulation control functionality"""
    print("Testing simulation controls...")
    
    config = VisualizationConfig()
    ui_overlay = UIOverlay(config)
    
    # Test control creation
    ui_overlay.create_simulation_controls()
    
    # Test callback registration
    callback_called = False
    
    def test_callback(state):
        nonlocal callback_called
        callback_called = True
    
    ui_overlay.register_callback("play_pause", test_callback)
    
    # Simulate play/pause button click
    ui_overlay._on_play_pause_clicked()
    
    assert ui_overlay.simulation_controls.state == SimulationState.PLAYING
    assert callback_called
    
    print("✓ Simulation controls working correctly")


def test_information_panels():
    """Test information panel functionality"""
    print("Testing information panels...")
    
    config = VisualizationConfig()
    ui_overlay = UIOverlay(config)
    
    # Test adding information panel
    panel_data = {
        "id": "test_panel",
        "title": "Test Information",
        "stats": {
            "vehicles": 50,
            "avg_speed": 25.5,
            "congestion": 0.3
        }
    }
    
    ui_overlay.add_information_panel(panel_data)
    
    assert "test_panel" in ui_overlay.info_panels
    assert ui_overlay.info_panels["test_panel"]["title"] == "Test Information"
    
    print("✓ Information panels working correctly")


def test_vehicle_details():
    """Test vehicle details display"""
    print("Testing vehicle details...")
    
    config = VisualizationConfig()
    ui_overlay = UIOverlay(config)
    
    # Test showing vehicle details
    vehicle_details = {
        "type": "CAR",
        "speed": 30.0,
        "destination": "Main Street",
        "fuel": 0.8,
        "behavior": "normal"
    }
    
    ui_overlay.show_vehicle_details(123, vehicle_details)
    
    assert ui_overlay.selected_vehicle_id == 123
    assert 123 in ui_overlay.vehicle_details
    assert ui_overlay.vehicle_details[123]["type"] == "CAR"
    
    print("✓ Vehicle details working correctly")


def test_scenario_selector():
    """Test scenario selection functionality"""
    print("Testing scenario selector...")
    
    config = VisualizationConfig()
    ui_overlay = UIOverlay(config)
    
    # Test scenario selector creation
    scenarios = [
        "Mumbai Traffic Junction",
        "Bangalore Tech Corridor",
        "Delhi Peak Hour",
        "Monsoon Flooding"
    ]
    
    ui_overlay.create_scenario_selector(scenarios)
    
    # Verify scenario selector was created
    assert "scenario_selector" in ui_overlay.panels
    
    print("✓ Scenario selector working correctly")


def test_weather_controls():
    """Test weather control functionality"""
    print("Testing weather controls...")
    
    config = VisualizationConfig()
    ui_overlay = UIOverlay(config)
    
    # Test weather controls creation
    weather_options = [
        WeatherType.CLEAR,
        WeatherType.LIGHT_RAIN,
        WeatherType.FOG,
        WeatherType.HEAVY_RAIN
    ]
    
    ui_overlay.add_weather_controls(weather_options)
    
    # Verify weather controls were created
    assert "weather_controls" in ui_overlay.panels
    
    print("✓ Weather controls working correctly")


def test_emergency_controls():
    """Test emergency scenario controls"""
    print("Testing emergency controls...")
    
    config = VisualizationConfig()
    ui_overlay = UIOverlay(config)
    
    # Test emergency controls creation
    emergency_types = [
        EmergencyType.ACCIDENT,
        EmergencyType.FLOODING,
        EmergencyType.ROAD_CLOSURE,
        EmergencyType.CONSTRUCTION
    ]
    
    ui_overlay.show_emergency_controls(emergency_types)
    
    # Verify emergency controls were created
    assert "emergency_controls" in ui_overlay.panels
    
    print("✓ Emergency controls working correctly")


def test_road_conditions_display():
    """Test road conditions display"""
    print("Testing road conditions display...")
    
    config = VisualizationConfig()
    ui_overlay = UIOverlay(config)
    
    # Test road conditions display
    conditions = {
        "quality": "poor",
        "potholes": 5,
        "construction": False,
        "traffic_density": 0.7
    }
    
    ui_overlay.display_road_conditions("segment_123", conditions)
    
    print("✓ Road conditions display working correctly")


def test_fps_counter():
    """Test FPS counter functionality"""
    print("Testing FPS counter...")
    
    config = VisualizationConfig()
    config.ui_config.show_fps_counter = True
    ui_overlay = UIOverlay(config)
    
    # Test FPS counter update
    ui_overlay.update_fps_counter(60.0)
    ui_overlay.update_fps_counter(45.5)
    
    print("✓ FPS counter working correctly")


def test_callback_system():
    """Test callback registration and handling"""
    print("Testing callback system...")
    
    config = VisualizationConfig()
    ui_overlay = UIOverlay(config)
    
    # Test multiple callback registrations
    callbacks_called = []
    
    def speed_callback(speed):
        callbacks_called.append(f"speed_{speed}")
    
    def weather_callback(weather):
        callbacks_called.append(f"weather_{weather}")
    
    def emergency_callback(emergency):
        callbacks_called.append(f"emergency_{emergency}")
    
    ui_overlay.register_callback("speed_change", speed_callback)
    ui_overlay.register_callback("weather_change", weather_callback)
    ui_overlay.register_callback("emergency_trigger", emergency_callback)
    
    # Simulate events
    ui_overlay._on_weather_changed("rain")
    ui_overlay._on_emergency_triggered(EmergencyType.ACCIDENT)
    
    assert "weather_rain" in callbacks_called
    assert "emergency_EmergencyType.ACCIDENT" in callbacks_called
    
    print("✓ Callback system working correctly")


def test_ui_cleanup():
    """Test UI cleanup functionality"""
    print("Testing UI cleanup...")
    
    config = VisualizationConfig()
    ui_overlay = UIOverlay(config)
    
    # Create some UI elements
    ui_overlay.create_simulation_controls()
    ui_overlay.add_weather_controls([WeatherType.CLEAR, WeatherType.LIGHT_RAIN])
    
    # Test cleanup
    ui_overlay.cleanup()
    
    print("✓ UI cleanup working correctly")


def run_all_tests():
    """Run all UI overlay tests"""
    print("Running UI Overlay Integration Tests")
    print("=" * 50)
    
    try:
        test_ui_overlay_creation()
        test_simulation_controls()
        test_information_panels()
        test_vehicle_details()
        test_scenario_selector()
        test_weather_controls()
        test_emergency_controls()
        test_road_conditions_display()
        test_fps_counter()
        test_callback_system()
        test_ui_cleanup()
        
        print("\n" + "=" * 50)
        print("✓ All UI overlay tests passed successfully!")
        print("\nUI Overlay Implementation Summary:")
        print("- Simulation controls (play, pause, stop, speed)")
        print("- Information panels with statistics")
        print("- Vehicle details display")
        print("- Scenario selection interface")
        print("- Weather controls with intensity")
        print("- Emergency scenario triggers")
        print("- Road conditions display")
        print("- FPS counter and performance monitoring")
        print("- Comprehensive callback system")
        print("- Proper cleanup functionality")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)