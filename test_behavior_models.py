"""
Unit Tests for Indian Driver Behavior Models

This module contains comprehensive unit tests for the IndianBehaviorModel class,
testing lane discipline calculations, overtaking behavior, and intersection behavior
with various scenarios and mixed vehicle types.
"""

import unittest
import random
from unittest.mock import Mock, patch
from typing import Dict, Any

from indian_features.behavior_model import (
    IndianBehaviorModel, TrafficState, OvertakeDecision, 
    IntersectionBehavior, LaneDisciplineResult
)
from indian_features.enums import (
    VehicleType, WeatherType, RoadQuality, BehaviorProfile, 
    LaneDiscipline, IntersectionType, SeverityLevel
)
from indian_features.config import BehaviorConfig


class TestLaneDisciplineCalculations(unittest.TestCase):
    """Test lane discipline calculations with various scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.behavior_model = IndianBehaviorModel()
        
        # Standard road conditions for baseline testing
        self.standard_conditions = {
            'quality': RoadQuality.GOOD,
            'lane_count': 2,
            'width': 7.0,
            'traffic_density': 0.5
        }
    
    def test_lane_discipline_by_vehicle_type(self):
        """Test that different vehicle types have appropriate lane discipline"""
        
        # Test each vehicle type
        vehicle_types = [
            VehicleType.CAR, VehicleType.BUS, VehicleType.TRUCK,
            VehicleType.MOTORCYCLE, VehicleType.AUTO_RICKSHAW, VehicleType.BICYCLE
        ]
        
        results = {}
        for vehicle_type in vehicle_types:
            result = self.behavior_model.calculate_lane_discipline(
                vehicle_type, self.standard_conditions
            )
            results[vehicle_type] = result
            
            # Verify result structure
            self.assertIsInstance(result, LaneDisciplineResult)
            self.assertIsInstance(result.discipline_level, LaneDiscipline)
            self.assertGreaterEqual(result.lane_change_probability, 0.0)
            self.assertGreaterEqual(result.lateral_deviation, 0.0)
            self.assertGreaterEqual(result.speed_variance, 0.0)
        
        # Verify relative discipline levels
        # Buses and trucks should be more disciplined than motorcycles and auto-rickshaws
        bus_discipline = results[VehicleType.BUS].discipline_level.value
        motorcycle_discipline = results[VehicleType.MOTORCYCLE].discipline_level.value
        auto_discipline = results[VehicleType.AUTO_RICKSHAW].discipline_level.value
        
        self.assertLessEqual(bus_discipline, motorcycle_discipline)
        self.assertLessEqual(bus_discipline, auto_discipline)
    
    def test_lane_discipline_road_quality_impact(self):
        """Test impact of road quality on lane discipline"""
        
        road_qualities = [RoadQuality.EXCELLENT, RoadQuality.GOOD, 
                         RoadQuality.POOR, RoadQuality.VERY_POOR]
        
        results = {}
        for quality in road_qualities:
            conditions = self.standard_conditions.copy()
            conditions['quality'] = quality
            
            result = self.behavior_model.calculate_lane_discipline(
                VehicleType.CAR, conditions
            )
            results[quality] = result
        
        # Better road quality should lead to better discipline
        excellent_discipline = results[RoadQuality.EXCELLENT].lateral_deviation
        poor_discipline = results[RoadQuality.VERY_POOR].lateral_deviation
        
        self.assertLess(excellent_discipline, poor_discipline)
    
    def test_lane_discipline_traffic_density_impact(self):
        """Test impact of traffic density on lane discipline"""
        
        densities = [0.1, 0.3, 0.5, 0.7, 0.9]
        results = {}
        
        for density in densities:
            conditions = self.standard_conditions.copy()
            conditions['traffic_density'] = density
            
            result = self.behavior_model.calculate_lane_discipline(
                VehicleType.CAR, conditions
            )
            results[density] = result
        
        # Higher density should increase lane change probability
        low_density_changes = results[0.1].lane_change_probability
        high_density_changes = results[0.9].lane_change_probability
        
        self.assertLess(low_density_changes, high_density_changes)
    
    def test_lane_discipline_lane_count_impact(self):
        """Test impact of lane count on discipline"""
        
        lane_counts = [1, 2, 3, 4, 6]
        results = {}
        
        for lane_count in lane_counts:
            conditions = self.standard_conditions.copy()
            conditions['lane_count'] = lane_count
            
            result = self.behavior_model.calculate_lane_discipline(
                VehicleType.CAR, conditions
            )
            results[lane_count] = result
        
        # More lanes should generally reduce discipline
        two_lane_deviation = results[2].lateral_deviation
        six_lane_deviation = results[6].lateral_deviation
        
        self.assertLessEqual(two_lane_deviation, six_lane_deviation)
    
    def test_lane_discipline_road_width_impact(self):
        """Test impact of road width on discipline"""
        
        road_widths = [4.0, 6.0, 7.0, 10.0, 12.0]  # meters
        results = {}
        
        for width in road_widths:
            conditions = self.standard_conditions.copy()
            conditions['width'] = width
            
            result = self.behavior_model.calculate_lane_discipline(
                VehicleType.CAR, conditions
            )
            results[width] = result
        
        # Narrow roads should have worse discipline
        narrow_road_deviation = results[4.0].lateral_deviation
        wide_road_deviation = results[12.0].lateral_deviation
        
        self.assertGreater(narrow_road_deviation, wide_road_deviation)
    
    def test_motorcycle_specific_behavior(self):
        """Test motorcycle-specific lane discipline behavior"""
        
        motorcycle_result = self.behavior_model.calculate_lane_discipline(
            VehicleType.MOTORCYCLE, self.standard_conditions
        )
        
        car_result = self.behavior_model.calculate_lane_discipline(
            VehicleType.CAR, self.standard_conditions
        )
        
        # Motorcycles should have higher lateral deviation and lane change probability
        self.assertGreater(motorcycle_result.lateral_deviation, car_result.lateral_deviation)
        self.assertGreater(motorcycle_result.lane_change_probability, car_result.lane_change_probability)
    
    def test_auto_rickshaw_specific_behavior(self):
        """Test auto-rickshaw-specific lane discipline behavior"""
        
        auto_result = self.behavior_model.calculate_lane_discipline(
            VehicleType.AUTO_RICKSHAW, self.standard_conditions
        )
        
        car_result = self.behavior_model.calculate_lane_discipline(
            VehicleType.CAR, self.standard_conditions
        )
        
        # Auto-rickshaws should be less disciplined than cars
        self.assertGreater(auto_result.lateral_deviation, car_result.lateral_deviation)
        self.assertGreaterEqual(auto_result.lane_change_probability, car_result.lane_change_probability)


class TestOvertakingBehavior(unittest.TestCase):
    """Test overtaking behavior under different traffic conditions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.behavior_model = IndianBehaviorModel()
        
        # Standard traffic state for baseline testing
        self.standard_traffic_state = TrafficState(
            density=0.5,
            average_speed=40.0,
            congestion_level=0.3,
            lane_count=2,
            road_width=7.0
        )
    
    def test_overtaking_probability_by_vehicle_type(self):
        """Test overtaking probability varies by vehicle type"""
        
        vehicle_types = [
            VehicleType.MOTORCYCLE, VehicleType.AUTO_RICKSHAW, VehicleType.CAR,
            VehicleType.BUS, VehicleType.TRUCK, VehicleType.BICYCLE
        ]
        
        probabilities = {}
        for vehicle_type in vehicle_types:
            prob = self.behavior_model.determine_overtaking_probability(
                vehicle_type, self.standard_traffic_state.density
            )
            probabilities[vehicle_type] = prob
            
            # Probability should be between 0 and 1
            self.assertGreaterEqual(prob, 0.0)
            self.assertLessEqual(prob, 1.0)
        
        # Motorcycles should be most aggressive, trucks least aggressive
        self.assertGreater(probabilities[VehicleType.MOTORCYCLE], 
                          probabilities[VehicleType.TRUCK])
        self.assertGreater(probabilities[VehicleType.AUTO_RICKSHAW], 
                          probabilities[VehicleType.BUS])
    
    def test_overtaking_probability_traffic_density_impact(self):
        """Test impact of traffic density on overtaking probability"""
        
        densities = [0.1, 0.3, 0.5, 0.7, 0.9]
        probabilities = {}
        
        for density in densities:
            prob = self.behavior_model.determine_overtaking_probability(
                VehicleType.CAR, density
            )
            probabilities[density] = prob
        
        # Higher density should reduce overtaking probability
        self.assertGreater(probabilities[0.1], probabilities[0.9])
    
    def test_overtaking_decision_speed_differential(self):
        """Test overtaking decision based on speed differential"""
        
        # Test with different speed differentials
        own_speeds = [30, 40, 50, 60]
        leading_speed = 30
        
        for own_speed in own_speeds:
            decision = self.behavior_model.determine_overtaking_behavior(
                VehicleType.CAR, self.standard_traffic_state, leading_speed, own_speed
            )
            
            self.assertIsInstance(decision, OvertakeDecision)
            
            speed_diff = own_speed - leading_speed
            
            if speed_diff <= 5:
                # Small speed difference should not trigger overtaking
                self.assertFalse(decision.should_overtake)
            else:
                # Larger speed difference should increase overtaking likelihood
                self.assertGreaterEqual(decision.confidence, 0.0)
                self.assertLessEqual(decision.confidence, 1.0)
    
    def test_overtaking_decision_traffic_conditions(self):
        """Test overtaking decision under various traffic conditions"""
        
        # Test with different congestion levels
        congestion_levels = [0.1, 0.3, 0.5, 0.7, 0.9]
        
        for congestion in congestion_levels:
            traffic_state = TrafficState(
                density=0.5,
                average_speed=40.0,
                congestion_level=congestion,
                lane_count=2,
                road_width=7.0
            )
            
            decision = self.behavior_model.determine_overtaking_behavior(
                VehicleType.CAR, traffic_state, 30, 50  # 20 km/h speed difference
            )
            
            # Higher congestion should reduce overtaking likelihood
            if congestion > 0.7:
                self.assertLessEqual(decision.confidence, 0.5)
    
    def test_overtaking_required_gap_calculation(self):
        """Test calculation of required gap for overtaking"""
        
        vehicle_types = [VehicleType.MOTORCYCLE, VehicleType.CAR, 
                        VehicleType.BUS, VehicleType.TRUCK]
        
        gaps = {}
        for vehicle_type in vehicle_types:
            decision = self.behavior_model.determine_overtaking_behavior(
                vehicle_type, self.standard_traffic_state, 30, 50
            )
            
            if decision.should_overtake:
                gaps[vehicle_type] = decision.required_gap
        
        # Larger vehicles should require larger gaps
        if VehicleType.MOTORCYCLE in gaps and VehicleType.TRUCK in gaps:
            self.assertLess(gaps[VehicleType.MOTORCYCLE], gaps[VehicleType.TRUCK])
    
    def test_overtaking_risk_assessment(self):
        """Test risk assessment for overtaking maneuvers"""
        
        # Test with high-risk conditions
        high_risk_state = TrafficState(
            density=0.8,
            average_speed=20.0,
            congestion_level=0.7,
            lane_count=1,
            road_width=5.0
        )
        
        # Test with low-risk conditions
        low_risk_state = TrafficState(
            density=0.2,
            average_speed=60.0,
            congestion_level=0.1,
            lane_count=3,
            road_width=10.0
        )
        
        high_risk_decision = self.behavior_model.determine_overtaking_behavior(
            VehicleType.CAR, high_risk_state, 30, 50
        )
        
        low_risk_decision = self.behavior_model.determine_overtaking_behavior(
            VehicleType.CAR, low_risk_state, 30, 50
        )
        
        # High-risk conditions should result in higher risk assessment
        if high_risk_decision.should_overtake and low_risk_decision.should_overtake:
            self.assertGreater(high_risk_decision.risk_level, low_risk_decision.risk_level)
    
    def test_overtaking_time_savings_estimation(self):
        """Test estimation of time savings from overtaking"""
        
        speed_differentials = [10, 20, 30, 40]
        
        for speed_diff in speed_differentials:
            decision = self.behavior_model.determine_overtaking_behavior(
                VehicleType.CAR, self.standard_traffic_state, 30, 30 + speed_diff
            )
            
            if decision.should_overtake:
                # Higher speed differential should result in more time savings
                self.assertGreaterEqual(decision.estimated_time_savings, 0.0)


class TestIntersectionBehavior(unittest.TestCase):
    """Test intersection behavior with mixed vehicle types"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.behavior_model = IndianBehaviorModel()
    
    def test_intersection_behavior_by_type(self):
        """Test behavior varies by intersection type"""
        
        intersection_types = [
            IntersectionType.SIGNALIZED, IntersectionType.ROUNDABOUT,
            IntersectionType.T_JUNCTION, IntersectionType.UNCONTROLLED
        ]
        
        behaviors = {}
        for intersection_type in intersection_types:
            behavior = self.behavior_model.model_intersection_behavior(
                VehicleType.CAR, intersection_type
            )
            behaviors[intersection_type] = behavior
            
            # Verify behavior structure
            self.assertIsInstance(behavior, IntersectionBehavior)
            self.assertGreaterEqual(behavior.approach_speed_factor, 0.0)
            self.assertLessEqual(behavior.approach_speed_factor, 2.0)
            self.assertGreaterEqual(behavior.stopping_probability, 0.0)
            self.assertLessEqual(behavior.stopping_probability, 1.0)
        
        # Signalized intersections should have higher stopping probability
        signalized_stopping = behaviors[IntersectionType.SIGNALIZED].stopping_probability
        uncontrolled_stopping = behaviors[IntersectionType.UNCONTROLLED].stopping_probability
        
        self.assertGreaterEqual(signalized_stopping, uncontrolled_stopping)
    
    def test_intersection_behavior_by_vehicle_type(self):
        """Test intersection behavior varies by vehicle type"""
        
        vehicle_types = [
            VehicleType.MOTORCYCLE, VehicleType.AUTO_RICKSHAW, VehicleType.CAR,
            VehicleType.BUS, VehicleType.TRUCK
        ]
        
        behaviors = {}
        for vehicle_type in vehicle_types:
            behavior = self.behavior_model.model_intersection_behavior(
                vehicle_type, IntersectionType.SIGNALIZED
            )
            behaviors[vehicle_type] = behavior
        
        # Motorcycles and auto-rickshaws should be more aggressive
        motorcycle_aggressiveness = behaviors[VehicleType.MOTORCYCLE].right_turn_aggressiveness
        car_aggressiveness = behaviors[VehicleType.CAR].right_turn_aggressiveness
        
        self.assertGreaterEqual(motorcycle_aggressiveness, car_aggressiveness)
        
        # Larger vehicles should have larger gap acceptance thresholds
        truck_gap = behaviors[VehicleType.TRUCK].gap_acceptance_threshold
        motorcycle_gap = behaviors[VehicleType.MOTORCYCLE].gap_acceptance_threshold
        
        self.assertGreater(truck_gap, motorcycle_gap)
    
    def test_motorcycle_intersection_behavior(self):
        """Test motorcycle-specific intersection behavior"""
        
        motorcycle_behavior = self.behavior_model.model_intersection_behavior(
            VehicleType.MOTORCYCLE, IntersectionType.SIGNALIZED
        )
        
        car_behavior = self.behavior_model.model_intersection_behavior(
            VehicleType.CAR, IntersectionType.SIGNALIZED
        )
        
        # Motorcycles should be more aggressive and use horn more
        self.assertGreaterEqual(motorcycle_behavior.right_turn_aggressiveness, 
                               car_behavior.right_turn_aggressiveness)
        self.assertGreaterEqual(motorcycle_behavior.horn_usage_probability, 
                               car_behavior.horn_usage_probability)
        
        # Motorcycles should accept smaller gaps
        self.assertLessEqual(motorcycle_behavior.gap_acceptance_threshold, 
                            car_behavior.gap_acceptance_threshold)
    
    def test_auto_rickshaw_intersection_behavior(self):
        """Test auto-rickshaw-specific intersection behavior"""
        
        auto_behavior = self.behavior_model.model_intersection_behavior(
            VehicleType.AUTO_RICKSHAW, IntersectionType.T_JUNCTION
        )
        
        car_behavior = self.behavior_model.model_intersection_behavior(
            VehicleType.CAR, IntersectionType.T_JUNCTION
        )
        
        # Auto-rickshaws should be aggressive and use horn frequently
        self.assertGreaterEqual(auto_behavior.right_turn_aggressiveness, 
                               car_behavior.right_turn_aggressiveness)
        self.assertGreater(auto_behavior.horn_usage_probability, 
                          car_behavior.horn_usage_probability)
    
    def test_bus_intersection_behavior(self):
        """Test bus-specific intersection behavior"""
        
        bus_behavior = self.behavior_model.model_intersection_behavior(
            VehicleType.BUS, IntersectionType.ROUNDABOUT
        )
        
        car_behavior = self.behavior_model.model_intersection_behavior(
            VehicleType.CAR, IntersectionType.ROUNDABOUT
        )
        
        # Buses should be less aggressive and need larger gaps
        self.assertLessEqual(bus_behavior.right_turn_aggressiveness, 
                            car_behavior.right_turn_aggressiveness)
        self.assertGreater(bus_behavior.gap_acceptance_threshold, 
                          car_behavior.gap_acceptance_threshold)
    
    def test_truck_intersection_behavior(self):
        """Test truck-specific intersection behavior"""
        
        truck_behavior = self.behavior_model.model_intersection_behavior(
            VehicleType.TRUCK, IntersectionType.UNCONTROLLED
        )
        
        motorcycle_behavior = self.behavior_model.model_intersection_behavior(
            VehicleType.MOTORCYCLE, IntersectionType.UNCONTROLLED
        )
        
        # Trucks should be more conservative
        self.assertLessEqual(truck_behavior.right_turn_aggressiveness, 
                            motorcycle_behavior.right_turn_aggressiveness)
        self.assertGreater(truck_behavior.gap_acceptance_threshold, 
                          motorcycle_behavior.gap_acceptance_threshold)
    
    def test_roundabout_specific_behavior(self):
        """Test roundabout-specific behavior patterns"""
        
        vehicle_types = [VehicleType.CAR, VehicleType.MOTORCYCLE, VehicleType.BUS]
        
        for vehicle_type in vehicle_types:
            behavior = self.behavior_model.model_intersection_behavior(
                vehicle_type, IntersectionType.ROUNDABOUT
            )
            
            # Approach speed factor should be reasonable (some aggressive vehicles may exceed 1.0)
            self.assertGreater(behavior.approach_speed_factor, 0.0)
            self.assertLess(behavior.approach_speed_factor, 2.0)
            
            # Gap acceptance should be reasonable for roundabouts
            self.assertGreater(behavior.gap_acceptance_threshold, 1.0)
            self.assertLess(behavior.gap_acceptance_threshold, 10.0)
    
    def test_uncontrolled_intersection_behavior(self):
        """Test behavior at uncontrolled intersections"""
        
        behavior = self.behavior_model.model_intersection_behavior(
            VehicleType.AUTO_RICKSHAW, IntersectionType.UNCONTROLLED
        )
        
        # Uncontrolled intersections should have high horn usage
        self.assertGreater(behavior.horn_usage_probability, 0.5)
        
        # Should have aggressive entry behavior
        self.assertGreater(behavior.right_turn_aggressiveness, 0.5)


class TestWeatherEffects(unittest.TestCase):
    """Test weather effects on behavior parameters"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.behavior_model = IndianBehaviorModel()
        
        self.base_behavior = {
            'speed': 50.0,
            'following_distance': 30.0,
            'lane_discipline': 0.8,
            'overtaking_aggressiveness': 0.6
        }
    
    def test_clear_weather_no_effect(self):
        """Test that clear weather has no negative effects"""
        
        modified_behavior = self.behavior_model.apply_weather_effects(
            self.base_behavior, WeatherType.CLEAR
        )
        
        # Clear weather should not reduce any parameters
        for key, value in self.base_behavior.items():
            self.assertEqual(modified_behavior[key], value)
    
    def test_rain_effects(self):
        """Test effects of rain on behavior"""
        
        light_rain_behavior = self.behavior_model.apply_weather_effects(
            self.base_behavior, WeatherType.LIGHT_RAIN
        )
        
        heavy_rain_behavior = self.behavior_model.apply_weather_effects(
            self.base_behavior, WeatherType.HEAVY_RAIN
        )
        
        # Rain should reduce speed and overtaking, increase following distance
        self.assertLess(light_rain_behavior['speed'], self.base_behavior['speed'])
        self.assertLess(heavy_rain_behavior['speed'], light_rain_behavior['speed'])
        
        self.assertGreater(light_rain_behavior['following_distance'], 
                          self.base_behavior['following_distance'])
        self.assertGreater(heavy_rain_behavior['following_distance'], 
                          light_rain_behavior['following_distance'])
    
    def test_fog_effects(self):
        """Test effects of fog on behavior"""
        
        fog_behavior = self.behavior_model.apply_weather_effects(
            self.base_behavior, WeatherType.FOG
        )
        
        # Fog should significantly reduce speed and overtaking
        self.assertLess(fog_behavior['speed'], self.base_behavior['speed'] * 0.7)
        self.assertLess(fog_behavior['overtaking_aggressiveness'], 
                       self.base_behavior['overtaking_aggressiveness'] * 0.5)
    
    def test_dust_storm_effects(self):
        """Test effects of dust storm on behavior"""
        
        dust_storm_behavior = self.behavior_model.apply_weather_effects(
            self.base_behavior, WeatherType.DUST_STORM
        )
        
        # Dust storm should have the most severe effects
        self.assertLess(dust_storm_behavior['speed'], self.base_behavior['speed'] * 0.6)
        self.assertGreater(dust_storm_behavior['following_distance'], 
                          self.base_behavior['following_distance'] * 1.8)


class TestStressLevelCalculation(unittest.TestCase):
    """Test driver stress level calculations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.behavior_model = IndianBehaviorModel()
        
        self.base_conditions = {
            'density': 0.5,
            'current_speed': 30,
            'desired_speed': 50,
            'weather': WeatherType.CLEAR
        }
    
    def test_stress_level_bounds(self):
        """Test that stress level is within valid bounds"""
        
        vehicle_types = [VehicleType.CAR, VehicleType.MOTORCYCLE, VehicleType.BUS]
        
        for vehicle_type in vehicle_types:
            stress = self.behavior_model.calculate_stress_level(
                vehicle_type, self.base_conditions
            )
            
            # Stress should be between 0 and 1
            self.assertGreaterEqual(stress, 0.0)
            self.assertLessEqual(stress, 1.0)
    
    def test_traffic_density_stress(self):
        """Test impact of traffic density on stress"""
        
        low_density_conditions = self.base_conditions.copy()
        low_density_conditions['density'] = 0.1
        
        high_density_conditions = self.base_conditions.copy()
        high_density_conditions['density'] = 0.9
        
        low_stress = self.behavior_model.calculate_stress_level(
            VehicleType.CAR, low_density_conditions
        )
        
        high_stress = self.behavior_model.calculate_stress_level(
            VehicleType.CAR, high_density_conditions
        )
        
        # Higher density should increase stress
        self.assertLess(low_stress, high_stress)
    
    def test_speed_frustration_stress(self):
        """Test impact of speed frustration on stress"""
        
        satisfied_conditions = self.base_conditions.copy()
        satisfied_conditions['current_speed'] = 50
        satisfied_conditions['desired_speed'] = 50
        
        frustrated_conditions = self.base_conditions.copy()
        frustrated_conditions['current_speed'] = 20
        frustrated_conditions['desired_speed'] = 60
        
        satisfied_stress = self.behavior_model.calculate_stress_level(
            VehicleType.CAR, satisfied_conditions
        )
        
        frustrated_stress = self.behavior_model.calculate_stress_level(
            VehicleType.CAR, frustrated_conditions
        )
        
        # Speed frustration should increase stress
        self.assertLess(satisfied_stress, frustrated_stress)
    
    def test_weather_stress(self):
        """Test impact of weather on stress levels"""
        
        clear_conditions = self.base_conditions.copy()
        clear_conditions['weather'] = WeatherType.CLEAR
        
        storm_conditions = self.base_conditions.copy()
        storm_conditions['weather'] = WeatherType.DUST_STORM
        
        clear_stress = self.behavior_model.calculate_stress_level(
            VehicleType.CAR, clear_conditions
        )
        
        storm_stress = self.behavior_model.calculate_stress_level(
            VehicleType.CAR, storm_conditions
        )
        
        # Bad weather should increase stress
        self.assertLess(clear_stress, storm_stress)
    
    def test_vehicle_type_stress_tolerance(self):
        """Test different stress tolerance by vehicle type"""
        
        motorcycle_stress = self.behavior_model.calculate_stress_level(
            VehicleType.MOTORCYCLE, self.base_conditions
        )
        
        bus_stress = self.behavior_model.calculate_stress_level(
            VehicleType.BUS, self.base_conditions
        )
        
        # Motorcycles should have higher stress (lower tolerance)
        self.assertGreater(motorcycle_stress, bus_stress)


if __name__ == '__main__':
    # Set random seed for reproducible tests
    random.seed(42)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestLaneDisciplineCalculations,
        TestOvertakingBehavior,
        TestIntersectionBehavior,
        TestWeatherEffects,
        TestStressLevelCalculation
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")