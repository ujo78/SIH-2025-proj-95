"""
Test Suite for Scenario Management

This module contains tests for scenario template handling, validation,
and configuration management functionality.
"""

import unittest
import tempfile
import json
import os
from pathlib import Path

from indian_features.scenario_manager import ScenarioManager, ScenarioTemplate, ScenarioValidator
from indian_features.scenario_templates import IndianScenarioTemplates, create_all_default_templates
from indian_features.enums import VehicleType, WeatherType, EmergencyType, SeverityLevel
from indian_features.config import IndianTrafficConfig


class TestScenarioTemplate(unittest.TestCase):
    """Test ScenarioTemplate functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.traffic_config = IndianTrafficConfig()
        
        self.template = ScenarioTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test scenario template",
            category="test",
            traffic_config=self.traffic_config
        )
    
    def test_template_creation(self):
        """Test basic template creation"""
        self.assertEqual(self.template.template_id, "test_template")
        self.assertEqual(self.template.name, "Test Template")
        self.assertEqual(self.template.category, "test")
        self.assertIsInstance(self.template.traffic_config, IndianTrafficConfig)
    
    def test_template_to_dict(self):
        """Test template serialization to dictionary"""
        template_dict = self.template.to_dict()
        
        self.assertIsInstance(template_dict, dict)
        self.assertEqual(template_dict['template_id'], "test_template")
        self.assertEqual(template_dict['name'], "Test Template")
        self.assertIn('traffic_config', template_dict)
    
    def test_template_from_dict(self):
        """Test template deserialization from dictionary"""
        template_dict = self.template.to_dict()
        restored_template = ScenarioTemplate.from_dict(template_dict)
        
        self.assertEqual(restored_template.template_id, self.template.template_id)
        self.assertEqual(restored_template.name, self.template.name)
        self.assertEqual(restored_template.category, self.template.category)


class TestScenarioValidator(unittest.TestCase):
    """Test ScenarioValidator functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = ScenarioValidator()
        
        # Create valid template
        self.valid_template = ScenarioTemplate(
            template_id="valid_test",
            name="Valid Test Template",
            description="A valid test template",
            category="test",
            traffic_config=IndianTrafficConfig(),
            simulation_duration=3600.0,
            time_of_day=12,
            day_of_week=1,
            weather_intensity=0.8
        )
    
    def test_valid_template_validation(self):
        """Test validation of a valid template"""
        errors = self.validator.validate_template(self.valid_template)
        self.assertEqual(len(errors), 0)
    
    def test_invalid_simulation_duration(self):
        """Test validation with invalid simulation duration"""
        invalid_template = ScenarioTemplate(
            template_id="invalid_duration",
            name="Invalid Duration",
            description="Template with invalid duration",
            category="test",
            traffic_config=IndianTrafficConfig(),
            simulation_duration=-100.0  # Invalid negative duration
        )
        
        errors = self.validator.validate_template(invalid_template)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("duration must be positive" in error.lower() for error in errors))
    
    def test_invalid_time_parameters(self):
        """Test validation with invalid time parameters"""
        invalid_template = ScenarioTemplate(
            template_id="invalid_time",
            name="Invalid Time",
            description="Template with invalid time",
            category="test",
            traffic_config=IndianTrafficConfig(),
            time_of_day=25,  # Invalid hour
            day_of_week=8    # Invalid day
        )
        
        errors = self.validator.validate_template(invalid_template)
        self.assertGreater(len(errors), 0)
    
    def test_invalid_weather_intensity(self):
        """Test validation with invalid weather intensity"""
        invalid_template = ScenarioTemplate(
            template_id="invalid_weather",
            name="Invalid Weather",
            description="Template with invalid weather",
            category="test",
            traffic_config=IndianTrafficConfig(),
            weather_intensity=1.5  # Invalid intensity > 1.0
        )
        
        errors = self.validator.validate_template(invalid_template)
        self.assertGreater(len(errors), 0)


class TestScenarioManager(unittest.TestCase):
    """Test ScenarioManager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        self.scenario_manager = ScenarioManager(self.temp_dir)
        
        # Create test template
        self.test_template = ScenarioTemplate(
            template_id="manager_test",
            name="Manager Test Template",
            description="Template for testing manager",
            category="test",
            traffic_config=IndianTrafficConfig()
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_template(self):
        """Test template creation through manager"""
        template = self.scenario_manager.create_template(
            template_id="new_test",
            name="New Test Template",
            description="A new test template",
            category="test"
        )
        
        self.assertIsInstance(template, ScenarioTemplate)
        self.assertEqual(template.template_id, "new_test")
        self.assertIn("new_test", self.scenario_manager.templates)
    
    def test_save_and_load_template(self):
        """Test template saving and loading"""
        # Save template
        success = self.scenario_manager.save_template(self.test_template)
        self.assertTrue(success)
        
        # Clear memory and reload
        self.scenario_manager.templates.clear()
        loaded_template = self.scenario_manager.load_template("manager_test")
        
        self.assertIsNotNone(loaded_template)
        self.assertEqual(loaded_template.template_id, "manager_test")
        self.assertEqual(loaded_template.name, "Manager Test Template")
    
    def test_list_templates(self):
        """Test template listing functionality"""
        # Add test template
        self.scenario_manager.templates["manager_test"] = self.test_template
        
        # Test listing all templates
        all_templates = self.scenario_manager.list_templates()
        self.assertIn("manager_test", all_templates)
        
        # Test listing by category
        test_templates = self.scenario_manager.list_templates("test")
        self.assertIn("manager_test", test_templates)
    
    def test_delete_template(self):
        """Test template deletion"""
        # Add and save template
        self.scenario_manager.templates["manager_test"] = self.test_template
        self.scenario_manager.save_template(self.test_template)
        
        # Delete template
        success = self.scenario_manager.delete_template("manager_test", delete_file=True)
        self.assertTrue(success)
        
        # Verify deletion
        self.assertNotIn("manager_test", self.scenario_manager.templates)
        template_file = Path(self.temp_dir) / "manager_test.json"
        self.assertFalse(template_file.exists())
    
    def test_clone_template(self):
        """Test template cloning"""
        # Add original template
        self.scenario_manager.templates["manager_test"] = self.test_template
        
        # Clone template
        cloned_template = self.scenario_manager.clone_template(
            "manager_test", 
            "cloned_test", 
            "Cloned Test Template"
        )
        
        self.assertIsNotNone(cloned_template)
        self.assertEqual(cloned_template.template_id, "cloned_test")
        self.assertEqual(cloned_template.name, "Cloned Test Template")
        self.assertIn("cloned_test", self.scenario_manager.templates)
    
    def test_search_templates(self):
        """Test template search functionality"""
        # Add test templates
        self.scenario_manager.templates["manager_test"] = self.test_template
        
        # Search by name
        results = self.scenario_manager.search_templates("Manager")
        self.assertIn("manager_test", results)
        
        # Search by description
        results = self.scenario_manager.search_templates("testing")
        self.assertIn("manager_test", results)


class TestDefaultTemplates(unittest.TestCase):
    """Test default template creation"""
    
    def test_create_all_default_templates(self):
        """Test creation of all default templates"""
        templates = create_all_default_templates()
        
        self.assertIsInstance(templates, dict)
        self.assertGreater(len(templates), 0)
        
        # Check for expected templates
        expected_templates = [
            "mumbai_intersection",
            "bangalore_tech_corridor", 
            "delhi_roundabout",
            "accident_emergency",
            "monsoon_flooding"
        ]
        
        for template_id in expected_templates:
            self.assertIn(template_id, templates)
            self.assertIsInstance(templates[template_id], ScenarioTemplate)
    
    def test_mumbai_intersection_template(self):
        """Test Mumbai intersection template creation"""
        template = IndianScenarioTemplates.create_mumbai_intersection_template()
        
        self.assertEqual(template.template_id, "mumbai_intersection")
        self.assertEqual(template.category, "intersection")
        self.assertIsInstance(template.traffic_config, IndianTrafficConfig)
        
        # Check Mumbai-specific vehicle mix
        vehicle_mix = template.traffic_config.vehicle_mix_ratios
        self.assertGreater(vehicle_mix[VehicleType.AUTO_RICKSHAW], 0.15)  # High auto-rickshaw ratio
    
    def test_emergency_template_validation(self):
        """Test emergency template validation"""
        template = IndianScenarioTemplates.create_accident_emergency_template()
        
        self.assertEqual(template.template_id, "accident_emergency")
        self.assertEqual(template.category, "emergency")
        self.assertGreater(len(template.emergency_scenarios), 0)
        
        # Validate emergency scenario structure
        emergency = template.emergency_scenarios[0]
        self.assertIn("scenario_type", emergency)
        self.assertIn("severity", emergency)
        self.assertIn("location", emergency)


class TestScenarioExportImport(unittest.TestCase):
    """Test scenario export and import functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_scenario.json")
        
        self.test_template = ScenarioTemplate(
            template_id="export_test",
            name="Export Test Template",
            description="Template for testing export/import",
            category="test",
            traffic_config=IndianTrafficConfig()
        )
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_json_export_import(self):
        """Test JSON export and import"""
        # Export template to JSON
        template_dict = self.test_template.to_dict()
        
        with open(self.test_file, 'w') as f:
            json.dump(template_dict, f, indent=2)
        
        # Import template from JSON
        with open(self.test_file, 'r') as f:
            imported_dict = json.load(f)
        
        imported_template = ScenarioTemplate.from_dict(imported_dict)
        
        # Verify import
        self.assertEqual(imported_template.template_id, self.test_template.template_id)
        self.assertEqual(imported_template.name, self.test_template.name)
        self.assertEqual(imported_template.category, self.test_template.category)
    
    def test_parameter_range_validation(self):
        """Test validation of parameter ranges"""
        validator = ScenarioValidator()
        
        # Test with out-of-range parameters
        invalid_template = ScenarioTemplate(
            template_id="range_test",
            name="Range Test",
            description="Testing parameter ranges",
            category="test",
            traffic_config=IndianTrafficConfig(),
            simulation_duration=100000.0,  # Too long
            time_of_day=30,  # Invalid hour
            weather_intensity=2.0  # Invalid intensity
        )
        
        errors = validator.validate_template(invalid_template)
        self.assertGreater(len(errors), 0)
        
        # Check specific error types
        error_text = " ".join(errors).lower()
        self.assertTrue("duration" in error_text or "time" in error_text or "intensity" in error_text)


def run_scenario_management_tests():
    """Run all scenario management tests"""
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestScenarioTemplate,
        TestScenarioValidator,
        TestScenarioManager,
        TestDefaultTemplates,
        TestScenarioExportImport
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Scenario Management Tests...")
    print("=" * 50)
    
    success = run_scenario_management_tests()
    
    if success:
        print("\n" + "=" * 50)
        print("All scenario management tests passed!")
    else:
        print("\n" + "=" * 50)
        print("Some tests failed. Check output above for details.")