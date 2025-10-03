#!/usr/bin/env python3
"""
Test script for TrafficFlowVisualizer implementation

This script tests the TrafficFlowVisualizer functionality including:
- Traffic density visualization
- Congestion hotspot display
- Emergency alert visualization
- Route visualization
- Integration with MixedTrafficManager data
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
import networkx as nx

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_visualization.traffic_flow_visualizer import TrafficFlowVisualizer
from enhanced_visualization.config import VisualizationConfig, UIConfig
from indian_features.enums import EmergencyType, VehicleType
from indian_features.interfaces import Point3D
from indian_features.mixed_traffic_manager import CongestionZone


class TestTrafficFlowVisualizer(unittest.TestCase):
    """Test cases for TrafficFlowVisualizer"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test configuration
        ui_config = UIConfig()
        self.config = VisualizationConfig(ui_config=ui_config)
        
        # Create visualizer instance (without Panda3D for testing)
        self.visualizer = TrafficFlowVisualizer(self.config)
        
        # Create test road network
        self.road_network = nx.Graph()
        self.road_network.add_node(1, x=0, y=0)
        self.road_network.add_node(2, x=100, y=0)
        self.road_network.add_node(3, x=100, y=100)
        self.road_network.add_edge(1, 2)
        self.road_network.add_edge(2, 3)
    
    def test_initialize_traffic_overlay(self):
        """Test traffic overlay initialization"""
        self.visualizer.initialize_traffic_overlay(self.road_network)
        
        # Check that road network is stored
        self.assertEqual(self.visualizer.road_network, self.road_network)
        
        # Check that edge geometries are extracted
        self.assertIn((1, 2), self.visualizer.edge_geometries)
        self.assertIn((2, 3), self.visualizer.edge_geometries)
        
        print("✓ Traffic overlay initialization test passed")
    
    def test_update_traffic_density(self):
        """Test traffic density updates"""
        self.visualizer.initialize_traffic_overlay(self.road_network)
        
        # Test density updates
        edge_densities = {
            (1, 2): 0.3,  # Light traffic
            (2, 3): 0.8   # Heavy traffic
        }
        
        self.visualizer.update_traffic_density(edge_densities)
        
        # Check that densities are stored
        self.assertEqual(self.visualizer.edge_densities[(1, 2)], 0.3)
        self.assertEqual(self.visualizer.edge_densities[(2, 3)], 0.8)
        
        print("✓ Traffic density update test passed")
    
    def test_show_congestion_hotspots(self):
        """Test congestion hotspot visualization"""
        hotspots = [
            {
                'id': 'hotspot_1',
                'x': 50,
                'y': 50,
                'z': 0,
                'radius': 25.0,
                'intensity': 0.9,
                'affected_edges': [(1, 2)]
            },
            {
                'id': 'hotspot_2',
                'x': 75,
                'y': 25,
                'z': 0,
                'radius': 15.0,
                'intensity': 0.6,
                'affected_edges': [(2, 3)]
            }
        ]
        
        self.visualizer.show_congestion_hotspots(hotspots)
        
        # Check that hotspots are stored
        self.assertEqual(len(self.visualizer.congestion_hotspots), 2)
        self.assertIn('hotspot_1', self.visualizer.congestion_hotspots)
        self.assertIn('hotspot_2', self.visualizer.congestion_hotspots)
        
        print("✓ Congestion hotspots test passed")
    
    def test_display_emergency_alerts(self):
        """Test emergency alert visualization"""
        emergencies = [
            {
                'id': 'accident_1',
                'type': EmergencyType.ACCIDENT,
                'x': 30,
                'y': 40,
                'z': 0,
                'severity': 0.8,
                'affected_area': []
            },
            {
                'id': 'flooding_1',
                'type': EmergencyType.FLOODING,
                'x': 80,
                'y': 60,
                'z': 0,
                'severity': 0.6,
                'affected_area': []
            }
        ]
        
        self.visualizer.display_emergency_alerts(emergencies)
        
        # Check that alerts are stored
        self.assertEqual(len(self.visualizer.emergency_alerts), 2)
        self.assertIn('accident_1', self.visualizer.emergency_alerts)
        self.assertIn('flooding_1', self.visualizer.emergency_alerts)
        
        print("✓ Emergency alerts test passed")
    
    def test_show_route_alternatives(self):
        """Test route visualization"""
        self.visualizer.initialize_traffic_overlay(self.road_network)
        
        original_route = [1, 2, 3]
        alternatives = [
            [1, 3],  # Direct route
        ]
        
        self.visualizer.show_route_alternatives(original_route, alternatives)
        
        # Check that routes are stored
        self.assertIn('original', self.visualizer.route_visualizations)
        self.assertIn('alternative_0', self.visualizer.route_visualizations)
        
        print("✓ Route alternatives test passed")
    
    def test_create_traffic_flow_animation(self):
        """Test traffic flow animation creation"""
        self.visualizer.initialize_traffic_overlay(self.road_network)
        
        # Set up some traffic density first
        edge_densities = {(1, 2): 0.6, (2, 3): 0.4}
        self.visualizer.update_traffic_density(edge_densities)
        
        flow_data = {
            'animation_speed': 1.0,
            'particle_count': 5
        }
        
        self.visualizer.create_traffic_flow_animation(flow_data)
        
        # Check that flow particles are created for high-density edges
        self.assertIn((1, 2), self.visualizer.flow_particles)
        
        print("✓ Traffic flow animation test passed")
    
    def test_add_performance_indicators(self):
        """Test performance indicators"""
        metrics = {
            'fps': 45.0,
            'congestion_level': 0.3,
            'vehicle_count': 150
        }
        
        self.visualizer.add_performance_indicators(metrics)
        
        # In mock mode, this should just print the metrics
        # In full implementation, would check for UI elements
        
        print("✓ Performance indicators test passed")
    
    def test_update_from_mixed_traffic_manager(self):
        """Test integration with MixedTrafficManager data"""
        self.visualizer.initialize_traffic_overlay(self.road_network)
        
        # Create mock traffic manager data
        congestion_zone = CongestionZone(
            center_point=Point3D(50, 50, 0),
            radius=25.0,
            severity=0.8,
            vehicle_count=15,
            average_speed=10.0,
            density=0.9,
            formation_time=100.0
        )
        
        traffic_data = {
            'congestion_zones': [congestion_zone],
            'interactions': [
                {'primary_vehicle_id': 'v1', 'secondary_vehicle_id': 'v2'}
            ],
            'statistics': {
                'total_vehicles': 20,
                'emergency_vehicles': 1
            }
        }
        
        self.visualizer.update_from_mixed_traffic_manager(traffic_data)
        
        # Check that congestion zones are processed
        self.assertEqual(len(self.visualizer.congestion_hotspots), 1)
        
        print("✓ MixedTrafficManager integration test passed")
    
    def test_real_time_congestion_indicators(self):
        """Test real-time congestion indicators"""
        self.visualizer.initialize_traffic_overlay(self.road_network)
        
        edge_speeds = {
            (1, 2): 15.0,  # Slow - congested
            (2, 3): 45.0   # Normal speed
        }
        
        self.visualizer.create_real_time_congestion_indicators(edge_speeds)
        
        # Check that densities are calculated correctly
        # Slow speed should result in high density
        self.assertGreater(self.visualizer.edge_densities[(1, 2)], 0.5)
        self.assertLess(self.visualizer.edge_densities[(2, 3)], 0.3)
        
        print("✓ Real-time congestion indicators test passed")
    
    def test_density_level_calculation(self):
        """Test density level calculation"""
        # Test different density levels
        self.assertEqual(self.visualizer._get_density_level(0.1), "free_flow")
        self.assertEqual(self.visualizer._get_density_level(0.3), "light_traffic")
        self.assertEqual(self.visualizer._get_density_level(0.5), "moderate_traffic")
        self.assertEqual(self.visualizer._get_density_level(0.7), "heavy_traffic")
        self.assertEqual(self.visualizer._get_density_level(0.9), "congested")
        
        print("✓ Density level calculation test passed")
    
    def test_clear_visualizations(self):
        """Test clearing of visualizations"""
        self.visualizer.initialize_traffic_overlay(self.road_network)
        
        # Add some visualizations
        self.visualizer.show_congestion_hotspots([{
            'id': 'test_hotspot',
            'x': 50, 'y': 50, 'z': 0,
            'radius': 25.0, 'intensity': 0.8
        }])
        
        self.visualizer.display_emergency_alerts([{
            'id': 'test_alert',
            'type': EmergencyType.ACCIDENT,
            'x': 30, 'y': 40, 'z': 0,
            'severity': 0.7
        }])
        
        # Clear visualizations
        self.visualizer._clear_congestion_hotspots()
        self.visualizer._clear_emergency_alerts()
        
        # Check that visualizations are cleared
        self.assertEqual(len(self.visualizer.congestion_hotspots), 0)
        self.assertEqual(len(self.visualizer.emergency_alerts), 0)
        
        print("✓ Clear visualizations test passed")


def run_tests():
    """Run all tests"""
    print("Running TrafficFlowVisualizer tests...")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTrafficFlowVisualizer)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All TrafficFlowVisualizer tests passed!")
        print(f"Ran {result.testsRun} tests successfully")
    else:
        print("❌ Some tests failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)