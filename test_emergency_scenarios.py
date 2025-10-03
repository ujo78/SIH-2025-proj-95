#!/usr/bin/env python3
"""
Test script for emergency scenario handling in enhanced TrafficModel
"""

import networkx as nx
from traffic_model import TrafficModel
from indian_features.enums import WeatherType, VehicleType, EmergencyType, SeverityLevel
from indian_features.config import IndianTrafficConfig
from indian_features.emergency_scenarios import EmergencyManager
from indian_features.interfaces import Point3D

def create_test_graph():
    """Create a simple test graph for testing"""
    G = nx.MultiDiGraph()
    
    # Add nodes with coordinates
    nodes = [
        (1, {'x': 0.0, 'y': 0.0}),
        (2, {'x': 100.0, 'y': 0.0}),
        (3, {'x': 200.0, 'y': 0.0}),
        (4, {'x': 0.0, 'y': 100.0}),
        (5, {'x': 100.0, 'y': 100.0}),
        (6, {'x': 200.0, 'y': 100.0}),
        (7, {'x': 300.0, 'y': 0.0}),
        (8, {'x': 300.0, 'y': 100.0})
    ]
    
    for node_id, attrs in nodes:
        G.add_node(node_id, **attrs)
    
    # Add edges with travel times in OSMnx format
    edges = [
        (1, 2, {'travel_time': 10.0, 'length': 100.0, 'highway': 'primary'}),
        (2, 3, {'travel_time': 10.0, 'length': 100.0, 'highway': 'secondary'}),
        (3, 7, {'travel_time': 10.0, 'length': 100.0, 'highway': 'primary'}),
        (1, 4, {'travel_time': 15.0, 'length': 100.0, 'highway': 'tertiary'}),
        (2, 5, {'travel_time': 8.0, 'length': 100.0, 'highway': 'primary'}),
        (3, 6, {'travel_time': 12.0, 'length': 100.0, 'highway': 'residential'}),
        (4, 5, {'travel_time': 10.0, 'length': 100.0, 'highway': 'secondary'}),
        (5, 6, {'travel_time': 10.0, 'length': 100.0, 'highway': 'primary'}),
        (6, 8, {'travel_time': 15.0, 'length': 100.0, 'highway': 'tertiary'}),
        (7, 8, {'travel_time': 10.0, 'length': 100.0, 'highway': 'primary'}),
        # Add reverse edges for bidirectional roads
        (2, 1, {'travel_time': 10.0, 'length': 100.0, 'highway': 'primary'}),
        (3, 2, {'travel_time': 10.0, 'length': 100.0, 'highway': 'secondary'}),
        (7, 3, {'travel_time': 10.0, 'length': 100.0, 'highway': 'primary'}),
        (4, 1, {'travel_time': 15.0, 'length': 100.0, 'highway': 'tertiary'}),
        (5, 2, {'travel_time': 8.0, 'length': 100.0, 'highway': 'primary'}),
        (6, 3, {'travel_time': 12.0, 'length': 100.0, 'highway': 'residential'}),
        (5, 4, {'travel_time': 10.0, 'length': 100.0, 'highway': 'secondary'}),
        (6, 5, {'travel_time': 10.0, 'length': 100.0, 'highway': 'primary'}),
        (8, 6, {'travel_time': 15.0, 'length': 100.0, 'highway': 'tertiary'}),
        (8, 7, {'travel_time': 10.0, 'length': 100.0, 'highway': 'primary'})
    ]
    
    for u, v, attrs in edges:
        G.add_edge(u, v, **attrs)
    
    return G

def test_emergency_manager():
    """Test EmergencyManager functionality"""
    print("=== Testing EmergencyManager ===")
    
    G = create_test_graph()
    from indian_features.mixed_traffic_manager import MixedTrafficManager
    from indian_features.behavior_model import IndianBehaviorModel
    
    behavior_model = IndianBehaviorModel()
    traffic_manager = MixedTrafficManager(behavior_model)
    emergency_manager = EmergencyManager(G, traffic_manager)
    
    print(f"Created emergency manager for graph with {len(G.nodes)} nodes and {len(G.edges)} edges")
    
    # Test creating different types of emergencies
    emergency_types = [
        (EmergencyType.ACCIDENT, SeverityLevel.MEDIUM),
        (EmergencyType.FLOODING, SeverityLevel.HIGH),
        (EmergencyType.ROAD_CLOSURE, SeverityLevel.CRITICAL),
        (EmergencyType.VEHICLE_BREAKDOWN, SeverityLevel.LOW)
    ]
    
    created_emergencies = []
    
    for emergency_type, severity in emergency_types:
        location = Point3D(x=100.0, y=50.0, z=0.0)  # Central location
        scenario = emergency_manager.create_emergency_scenario(
            emergency_type, location=location, severity=severity
        )
        created_emergencies.append(scenario)
        
        print(f"\nCreated {emergency_type.name} emergency:")
        print(f"  ID: {scenario.scenario_id}")
        print(f"  Severity: {scenario.severity.name}")
        print(f"  Description: {scenario.description}")
        print(f"  Affected edges: {len(scenario.affected_edges)}")
        print(f"  Lanes blocked: {scenario.lanes_blocked}")
        print(f"  Speed reduction: {scenario.speed_reduction_factor:.2f}")
        print(f"  Accessibility: {scenario.accessibility:.2f}")
        print(f"  Congestion radius: {scenario.congestion_radius:.1f}m")
    
    # Test emergency statistics
    stats = emergency_manager.get_emergency_statistics()
    print(f"\nEmergency statistics: {stats}")
    
    # Test alternative routing
    print(f"\n--- Testing Alternative Routing ---")
    origin, destination = 1, 8
    
    # Find routes without emergencies
    normal_routes = emergency_manager.find_alternative_routes(origin, destination, set())
    print(f"Normal routes from {origin} to {destination}: {len(normal_routes)}")
    for i, route in enumerate(normal_routes):
        print(f"  Route {i+1}: {route}")
    
    # Find routes with blocked edges
    blocked_edges = {(2, 3), (3, 6)}  # Block some edges
    emergency_routes = emergency_manager.find_alternative_routes(origin, destination, blocked_edges)
    print(f"\nEmergency routes (avoiding {blocked_edges}): {len(emergency_routes)}")
    for i, route in enumerate(emergency_routes):
        print(f"  Route {i+1}: {route}")
    
    print("EmergencyManager test completed!\n")

def test_emergency_integration():
    """Test emergency integration in TrafficModel"""
    print("=== Testing Emergency Integration ===")
    
    G = create_test_graph()
    config = IndianTrafficConfig()
    
    # Create model with Indian features
    model = TrafficModel(
        G, 
        max_vehicles=6, 
        spawn_rate_per_s=1.0, 
        sim_seconds=50,
        use_indian_features=True,
        indian_config=config
    )
    
    print(f"Created model with emergency management")
    
    # Create some emergency scenarios
    print("\n--- Creating Emergency Scenarios ---")
    
    # Create accident
    accident_location = Point3D(x=150.0, y=0.0, z=0.0)
    accident_id = model.create_emergency_scenario(
        EmergencyType.ACCIDENT, 
        location=accident_location, 
        severity=SeverityLevel.HIGH
    )
    print(f"Created accident: {accident_id}")
    
    # Create flooding
    flood_location = Point3D(x=100.0, y=100.0, z=0.0)
    flood_id = model.create_emergency_scenario(
        EmergencyType.FLOODING, 
        location=flood_location, 
        severity=SeverityLevel.CRITICAL
    )
    print(f"Created flooding: {flood_id}")
    
    # Get active emergencies
    active_emergencies = model.get_active_emergencies()
    print(f"\nActive emergencies: {len(active_emergencies)}")
    for emergency in active_emergencies:
        print(f"  {emergency['type']} ({emergency['severity']}) - {emergency['description']}")
        print(f"    Affected edges: {emergency['affected_edges']}")
        print(f"    Accessibility: {emergency['accessibility']:.2f}")
    
    # Run simulation with emergencies
    print(f"\n--- Running Simulation with Emergencies ---")
    model.run()
    
    # Get final statistics
    stats = model.get_simulation_statistics()
    
    print(f"\nSimulation completed:")
    print(f"Total vehicles: {stats['total_vehicles']}")
    print(f"Emergency statistics: {stats['emergency_statistics']}")
    print(f"Emergency affected vehicles: {stats['emergency_affected_vehicles']}")
    print(f"Vehicles needing rerouting: {stats['vehicles_needing_rerouting']}")
    
    # Check final active emergencies
    final_emergencies = model.get_active_emergencies()
    print(f"Final active emergencies: {len(final_emergencies)}")
    
    print("Emergency integration test completed!\n")

def test_dynamic_emergency_creation():
    """Test dynamic emergency creation during simulation"""
    print("=== Testing Dynamic Emergency Creation ===")
    
    G = create_test_graph()
    config = IndianTrafficConfig()
    
    # Create model with shorter emergency update interval
    model = TrafficModel(
        G, 
        max_vehicles=8, 
        spawn_rate_per_s=1.5, 
        sim_seconds=80,
        use_indian_features=True,
        indian_config=config
    )
    
    # Set shorter update interval for testing
    model.emergency_update_interval = 20.0  # Update every 20 sim seconds
    
    # Set weather to increase emergency probability
    model.update_weather_conditions(WeatherType.HEAVY_RAIN, intensity=0.8)
    
    print("Running simulation with dynamic emergency creation...")
    print("Weather set to HEAVY_RAIN to increase emergency probability")
    
    # Run simulation
    model.run()
    
    # Get final statistics
    stats = model.get_simulation_statistics()
    
    print(f"\nDynamic emergency simulation completed:")
    print(f"Total simulation time: {stats['simulation_time']:.1f} seconds")
    print(f"Weather: {stats['current_weather']}")
    print(f"Total vehicles: {stats['total_vehicles']}")
    print(f"Vehicle distribution: {stats['vehicle_type_distribution']}")
    
    emergency_stats = stats['emergency_statistics']
    print(f"\nEmergency Statistics:")
    print(f"  Active emergencies: {emergency_stats['active_emergencies']}")
    print(f"  Total emergencies created: {emergency_stats['total_emergencies_created']}")
    print(f"  Total vehicles rerouted: {emergency_stats['total_vehicles_rerouted']}")
    print(f"  Blocked edges: {emergency_stats['blocked_edges']}")
    print(f"  Emergency history: {emergency_stats['emergency_history_count']}")
    
    if emergency_stats['active_by_type']:
        print(f"  Active by type: {emergency_stats['active_by_type']}")
    
    print(f"Emergency affected vehicles: {stats['emergency_affected_vehicles']}")
    print(f"Vehicles needing rerouting: {stats['vehicles_needing_rerouting']}")
    
    print("Dynamic emergency creation test completed!\n")

def test_emergency_resolution():
    """Test manual emergency resolution"""
    print("=== Testing Emergency Resolution ===")
    
    G = create_test_graph()
    config = IndianTrafficConfig()
    
    model = TrafficModel(
        G, 
        max_vehicles=4, 
        spawn_rate_per_s=2.0, 
        sim_seconds=30,
        use_indian_features=True,
        indian_config=config
    )
    
    # Create emergency
    emergency_id = model.create_emergency_scenario(
        EmergencyType.ROAD_CLOSURE, 
        severity=SeverityLevel.HIGH
    )
    
    print(f"Created emergency: {emergency_id}")
    
    # Check active emergencies
    active_before = model.get_active_emergencies()
    print(f"Active emergencies before resolution: {len(active_before)}")
    
    # Run partial simulation
    model.env.process(model.vehicle_source())
    model.env.run(until=15)  # Run for 15 seconds
    
    mid_stats = model.get_simulation_statistics()
    print(f"Mid-simulation emergency stats: {mid_stats['emergency_statistics']}")
    
    # Resolve emergency
    resolved = model.resolve_emergency_scenario(emergency_id)
    print(f"Emergency resolution successful: {resolved}")
    
    # Check active emergencies after resolution
    active_after = model.get_active_emergencies()
    print(f"Active emergencies after resolution: {len(active_after)}")
    
    # Continue simulation
    model.env.run(until=30)  # Complete simulation
    
    final_stats = model.get_simulation_statistics()
    print(f"Final emergency stats: {final_stats['emergency_statistics']}")
    
    print("Emergency resolution test completed!\n")

if __name__ == "__main__":
    print("=== Emergency Scenario Handling Tests ===\n")
    
    try:
        # Test individual components
        test_emergency_manager()
        
        # Test integration
        test_emergency_integration()
        
        # Test dynamic creation
        test_dynamic_emergency_creation()
        
        # Test resolution
        test_emergency_resolution()
        
        print("=== All emergency scenario tests completed successfully! ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()