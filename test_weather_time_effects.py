#!/usr/bin/env python3
"""
Test script for weather and time-of-day effects in enhanced TrafficModel
"""

import networkx as nx
from traffic_model import TrafficModel
from indian_features.enums import WeatherType, VehicleType
from indian_features.config import IndianTrafficConfig
from indian_features.weather_conditions import WeatherManager, TimeOfDayManager

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
        (6, {'x': 200.0, 'y': 100.0})
    ]
    
    for node_id, attrs in nodes:
        G.add_node(node_id, **attrs)
    
    # Add edges with travel times in OSMnx format
    edges = [
        (1, 2, {'travel_time': 10.0, 'length': 100.0, 'highway': 'primary'}),
        (2, 3, {'travel_time': 10.0, 'length': 100.0, 'highway': 'secondary'}),
        (1, 4, {'travel_time': 15.0, 'length': 100.0, 'highway': 'tertiary'}),
        (2, 5, {'travel_time': 8.0, 'length': 100.0, 'highway': 'primary'}),
        (3, 6, {'travel_time': 12.0, 'length': 100.0, 'highway': 'residential'}),
        (4, 5, {'travel_time': 10.0, 'length': 100.0, 'highway': 'secondary'}),
        (5, 6, {'travel_time': 10.0, 'length': 100.0, 'highway': 'primary'}),
        # Add reverse edges for bidirectional roads
        (2, 1, {'travel_time': 10.0, 'length': 100.0, 'highway': 'primary'}),
        (3, 2, {'travel_time': 10.0, 'length': 100.0, 'highway': 'secondary'}),
        (4, 1, {'travel_time': 15.0, 'length': 100.0, 'highway': 'tertiary'}),
        (5, 2, {'travel_time': 8.0, 'length': 100.0, 'highway': 'primary'}),
        (6, 3, {'travel_time': 12.0, 'length': 100.0, 'highway': 'residential'}),
        (5, 4, {'travel_time': 10.0, 'length': 100.0, 'highway': 'secondary'}),
        (6, 5, {'travel_time': 10.0, 'length': 100.0, 'highway': 'primary'})
    ]
    
    for u, v, attrs in edges:
        G.add_edge(u, v, **attrs)
    
    return G

def test_weather_manager():
    """Test WeatherManager functionality"""
    print("=== Testing WeatherManager ===")
    
    weather_manager = WeatherManager()
    
    # Test initial weather
    print(f"Initial weather: {weather_manager.current_weather.condition_type.name}")
    print(f"Initial intensity: {weather_manager.current_weather.intensity}")
    print(f"Initial visibility: {weather_manager.current_weather.visibility:.2f}")
    
    # Test weather effects for different vehicle types
    for vehicle_type in [VehicleType.CAR, VehicleType.MOTORCYCLE, VehicleType.BUS]:
        effects = weather_manager.get_current_weather_effects(vehicle_type)
        print(f"\n{vehicle_type.name} weather effects:")
        print(f"  Speed factor: {effects['speed_factor']:.2f}")
        print(f"  Following distance factor: {effects['following_distance_factor']:.2f}")
        print(f"  Accident probability multiplier: {effects['accident_probability_multiplier']:.2f}")
    
    # Test weather transitions
    print("\n--- Testing weather transitions ---")
    from datetime import datetime
    current_time = datetime.now()
    
    for i in range(5):
        new_weather = weather_manager.update_weather(current_time, force_change=True)
        print(f"Weather {i+1}: {new_weather.condition_type.name} (intensity: {new_weather.intensity:.2f})")
    
    print("WeatherManager test completed!\n")

def test_time_manager():
    """Test TimeOfDayManager functionality"""
    print("=== Testing TimeOfDayManager ===")
    
    time_manager = TimeOfDayManager()
    
    # Test different hours
    test_hours = [6, 8, 12, 18, 22, 2]
    
    for hour in test_hours:
        effects = time_manager.get_time_effects_summary(hour)
        print(f"\nHour {hour}:00 ({effects['period']}):")
        print(f"  Is peak hour: {effects['is_peak_hour']}")
        print(f"  Traffic density multiplier: {effects['traffic_density_multiplier']:.2f}")
        print(f"  Speed adjustment: {effects['speed_adjustment']:.2f}")
        print(f"  Aggressiveness multiplier: {effects['aggressiveness_multiplier']:.2f}")
        
        # Test spawn rate adjustment
        base_spawn_rate = 1.0
        adjusted_rate = time_manager.get_spawn_rate_adjustment(hour, base_spawn_rate)
        print(f"  Spawn rate adjustment: {base_spawn_rate:.2f} -> {adjusted_rate:.2f}")
    
    print("\nTimeOfDayManager test completed!\n")

def test_weather_time_integration():
    """Test weather and time integration in TrafficModel"""
    print("=== Testing Weather and Time Integration ===")
    
    G = create_test_graph()
    config = IndianTrafficConfig()
    
    # Create model with Indian features
    model = TrafficModel(
        G, 
        max_vehicles=6, 
        spawn_rate_per_s=1.5, 
        sim_seconds=60,
        use_indian_features=True,
        indian_config=config
    )
    
    print(f"Created model with weather and time managers")
    
    # Test different weather conditions
    weather_conditions = [
        (WeatherType.CLEAR, 0.2),
        (WeatherType.LIGHT_RAIN, 0.5),
        (WeatherType.HEAVY_RAIN, 0.8),
        (WeatherType.FOG, 0.6)
    ]
    
    for weather_type, intensity in weather_conditions:
        print(f"\n--- Testing {weather_type.name} (intensity: {intensity}) ---")
        
        # Update weather
        model.update_weather_conditions(weather_type, intensity)
        
        # Update time to peak hour
        model.update_time_of_day(8)  # Morning rush
        
        # Run short simulation
        model.env = model.env.__class__()  # Reset environment
        model.env.process(model.vehicle_source())
        model.env.run(until=20)
        
        # Get statistics
        stats = model.get_simulation_statistics()
        
        print(f"Weather details: {stats['weather_details']}")
        print(f"Time effects: {stats['time_effects']}")
        print(f"Weather effects: {stats['weather_effects']}")
        print(f"Vehicles created: {stats['total_vehicles']}")
    
    print("\nWeather and time integration test completed!\n")

def test_dynamic_conditions():
    """Test dynamic weather and time updates during simulation"""
    print("=== Testing Dynamic Conditions ===")
    
    G = create_test_graph()
    config = IndianTrafficConfig()
    
    # Create model with shorter update intervals for testing
    model = TrafficModel(
        G, 
        max_vehicles=8, 
        spawn_rate_per_s=2.0, 
        sim_seconds=120,
        use_indian_features=True,
        indian_config=config
    )
    
    # Set shorter update intervals for testing
    model.weather_update_interval = 20.0  # Update every 20 sim seconds
    model.time_update_interval = 15.0     # Update every 15 sim seconds
    
    print("Running simulation with dynamic weather and time updates...")
    
    # Run simulation
    model.run()
    
    # Get final statistics
    stats = model.get_simulation_statistics()
    
    print(f"\nFinal simulation statistics:")
    print(f"Total simulation time: {stats['simulation_time']:.1f} seconds")
    print(f"Final weather: {stats['current_weather']}")
    print(f"Final hour: {stats['current_hour']}")
    print(f"Weather details: {stats['weather_details']}")
    print(f"Time effects: {stats['time_effects']}")
    print(f"Total vehicles: {stats['total_vehicles']}")
    print(f"Vehicle distribution: {stats['vehicle_type_distribution']}")
    print(f"Active interactions: {stats['active_interactions']}")
    print(f"Congestion zones: {stats['congestion_zones']}")
    
    print("\nDynamic conditions test completed!\n")

if __name__ == "__main__":
    print("=== Weather and Time-of-Day Effects Tests ===\n")
    
    try:
        # Test individual components
        test_weather_manager()
        test_time_manager()
        
        # Test integration
        test_weather_time_integration()
        
        # Test dynamic updates
        test_dynamic_conditions()
        
        print("=== All weather and time tests completed successfully! ===")
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()