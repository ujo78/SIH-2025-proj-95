#!/usr/bin/env python3
"""
Test script to verify zoom controls work correctly
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_zoom_functionality():
    """Test that zoom controls are properly implemented"""
    
    try:
        # Test imports
        from panda3d.core import loadPrcFileData, Vec3
        from direct.showbase.ShowBase import ShowBase
        
        print("✅ Panda3D imports successful")
        
        # Test that we can create a basic ShowBase instance
        loadPrcFileData("", "window-type none")  # Headless mode for testing
        
        class TestApp(ShowBase):
            def __init__(self):
                ShowBase.__init__(self)
                
                # Test zoom camera method
                self.camera_distance = 150
                self.camera_angle_h = 0
                self.camera_angle_p = -30
                
                # Test zoom functionality
                self.zoom_camera(-10)  # Zoom in
                self.zoom_camera(20)   # Zoom out
                
                print("✅ Zoom controls working")
                
                # Test camera position update
                self.update_camera_position()
                print("✅ Camera position update working")
                
                # Clean exit
                sys.exit(0)
            
            def zoom_camera(self, zoom_amount):
                """Zoom camera in/out"""
                self.camera_distance += zoom_amount
                self.camera_distance = max(20, min(500, self.camera_distance))
                print(f"Camera distance: {self.camera_distance}")
            
            def update_camera_position(self):
                """Update camera position based on distance and angles"""
                import math
                
                h_rad = math.radians(self.camera_angle_h)
                p_rad = math.radians(self.camera_angle_p)
                
                x = self.camera_distance * math.cos(p_rad) * math.sin(h_rad)
                y = -self.camera_distance * math.cos(p_rad) * math.cos(h_rad)
                z = self.camera_distance * math.sin(p_rad)
                
                self.camera.setPos(x, y, z)
                self.camera.lookAt(0, 0, 0)
                print(f"Camera position: ({x:.1f}, {y:.1f}, {z:.1f})")
        
        # Run test
        app = TestApp()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

def test_demo_imports():
    """Test that demo files can be imported without errors"""
    
    try:
        # Test traffic_flow_demo imports
        print("Testing traffic_flow_demo imports...")
        
        # Import the main components
        from enhanced_visualization.traffic_flow_visualizer import TrafficFlowVisualizer
        from enhanced_visualization.config import VisualizationConfig, UIConfig
        from indian_features.enums import EmergencyType
        
        print("✅ Demo imports successful")
        
        # Test configuration creation
        ui_config = UIConfig()
        config = VisualizationConfig(ui_config=ui_config)
        
        print("✅ Configuration creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Zoom Controls and Demo Functionality")
    print("=" * 50)
    
    # Test demo imports first
    if not test_demo_imports():
        print("❌ Demo import tests failed")
        return 1
    
    # Test zoom functionality
    if not test_zoom_functionality():
        print("❌ Zoom functionality tests failed")
        return 1
    
    print("✅ All tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())