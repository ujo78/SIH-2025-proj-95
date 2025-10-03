#!/usr/bin/env python3
"""
Test script for CameraController

This script demonstrates how to properly import and use the CameraController
from the enhanced_visualization package.
"""

import sys
import os

# Add the current directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from enhanced_visualization import (
        CameraController, VisualizationConfig, PANDA3D_AVAILABLE
    )
    from indian_features.interfaces import Point3D
    
    def test_camera_controller():
        """Test the camera controller functionality."""
        print("Testing CameraController...")
        
        # Create configuration
        config = VisualizationConfig()
        
        # Create camera controller (without Panda3D node for testing)
        camera_controller = CameraController(config, camera_node=None)
        
        print(f"Panda3D available: {PANDA3D_AVAILABLE}")
        print(f"Camera controller created successfully")
        
        # Test setting camera position
        position = Point3D(100, 200, 50)
        target = Point3D(0, 0, 0)
        
        camera_controller.set_camera_position(position, target)
        print(f"Set camera position to: ({position.x}, {position.y}, {position.z})")
        
        # Test presets
        print(f"Available presets: {list(camera_controller.presets.keys())}")
        
        # Test follow mode
        camera_controller.follow_vehicle(1, Point3D(0, -20, 10))
        print("Set camera to follow vehicle 1")
        
        # Test smooth transition
        new_position = Point3D(200, 300, 100)
        camera_controller.create_smooth_transition(position, new_position, 2.0)
        print("Created smooth transition")
        
        # Test cinematic path
        waypoints = [
            Point3D(0, 0, 50),
            Point3D(100, 0, 50),
            Point3D(100, 100, 50),
            Point3D(0, 100, 50)
        ]
        camera_controller.create_cinematic_path(waypoints, 10.0)
        print("Created cinematic path")
        
        # Get current state
        state = camera_controller.get_camera_state()
        print(f"Current camera mode: {state.mode}")
        
        print("CameraController test completed successfully!")
        
        return camera_controller
    
    if __name__ == "__main__":
        controller = test_camera_controller()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this script from the correct directory")
    print("and that all required modules are available.")
    
except Exception as e:
    print(f"Error testing camera controller: {e}")
    import traceback
    traceback.print_exc()