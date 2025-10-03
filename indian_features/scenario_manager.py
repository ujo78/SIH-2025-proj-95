"""
Scenario Manager Module

This module implements scenario template handling for Indian traffic simulation,
including template creation, loading, saving, and validation functionality.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .enums import (
    VehicleType, EmergencyType, WeatherType, SeverityLevel,
    IntersectionType, RoadQuality
)
from .config import IndianTrafficConfig, VehicleConfig, BehaviorConfig, RoadConditionConfig
from .emergency_scenarios import EmergencyScenario
from .interfaces import Point3D


@dataclass
class ScenarioTemplate:
    """Template for Indian traffic scenarios"""
    
    # Basic information
    template_id: str
    name: str
    description: str
    category: str  # e.g., "intersection", "emergency", "regional", "peak_hour"
    version: str = "1.0"
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Traffic configuration
    traffic_config: IndianTrafficConfig = field(default_factory=IndianTrafficConfig)
    
    # Scenario-specific parameters
    simulation_duration: float = 3600.0  # seconds
    time_of_day: int = 12  # hour (0-23)
    day_of_week: int = 1  # 0=Monday, 6=Sunday
    
    # Weather conditions
    weather_type: WeatherType = WeatherType.CLEAR
    weather_intensity: float = 1.0  # 0.0 to 1.0
    
    # Emergency scenarios
    emergency_scenarios: List[Dict[str, Any]] = field(default_factory=list)
    
    # Road network parameters
    network_bounds: Optional[Dict[str, float]] = None  # {"north": lat, "south": lat, "east": lon, "west": lon}
    road_quality_override: Optional[Dict[str, RoadQuality]] = None
    
    # Spawn parameters
    spawn_points: List[Dict[str, Any]] = field(default_factory=list)
    destination_points: List[Dict[str, Any]] = field(default_factory=list)
    
    # Custom parameters for specific scenarios
    custom_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Validation metadata
    is_validated: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary for JSON serialization"""
        template_dict = asdict(self)
        
        # Convert enums to strings
        template_dict['weather_type'] = self.weather_type.name
        
        # Convert traffic config enums
        if 'traffic_config' in template_dict:
            config_dict = template_dict['traffic_config']
            
            # Convert vehicle mix ratios enum keys to strings
            if 'vehicle_mix_ratios' in config_dict:
                vehicle_mix = {}
                for vehicle_type, ratio in self.traffic_config.vehicle_mix_ratios.items():
                    vehicle_mix[vehicle_type.name] = ratio
                config_dict['vehicle_mix_ratios'] = vehicle_mix
            
            # Convert weather probabilities enum keys to strings
            if 'weather_probabilities' in config_dict:
                weather_probs = {}
                for weather_type, prob in self.traffic_config.weather_probabilities.items():
                    weather_probs[weather_type.name] = prob
                config_dict['weather_probabilities'] = weather_probs
            
            # Convert road quality distribution enum keys to strings
            if 'road_quality_distribution' in config_dict:
                road_quality = {}
                for quality, dist in self.traffic_config.road_quality_distribution.items():
                    road_quality[quality.name] = dist
                config_dict['road_quality_distribution'] = road_quality
        
        return template_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScenarioTemplate':
        """Create template from dictionary (JSON deserialization)"""
        
        # Convert weather type string back to enum
        if 'weather_type' in data and isinstance(data['weather_type'], str):
            data['weather_type'] = WeatherType[data['weather_type']]
        
        # Handle traffic config conversion
        if 'traffic_config' in data and isinstance(data['traffic_config'], dict):
            config_data = data['traffic_config']
            
            # Convert vehicle mix ratios string keys back to enums
            if 'vehicle_mix_ratios' in config_data:
                vehicle_mix = {}
                for vehicle_name, ratio in config_data['vehicle_mix_ratios'].items():
                    vehicle_mix[VehicleType[vehicle_name]] = ratio
                config_data['vehicle_mix_ratios'] = vehicle_mix
            
            # Convert weather probabilities string keys back to enums
            if 'weather_probabilities' in config_data:
                weather_probs = {}
                for weather_name, prob in config_data['weather_probabilities'].items():
                    weather_probs[WeatherType[weather_name]] = prob
                config_data['weather_probabilities'] = weather_probs
            
            # Convert road quality distribution string keys back to enums
            if 'road_quality_distribution' in config_data:
                road_quality = {}
                for quality_name, dist in config_data['road_quality_distribution'].items():
                    road_quality[RoadQuality[quality_name]] = dist
                config_data['road_quality_distribution'] = road_quality
            
            # Create IndianTrafficConfig object
            data['traffic_config'] = IndianTrafficConfig(**config_data)
        
        return cls(**data)


class ScenarioValidator:
    """Validates scenario templates for correctness and consistency"""
    
    def __init__(self):
        """Initialize validator with validation rules"""
        self.validation_rules = {
            'vehicle_mix_ratios_sum': self._validate_vehicle_mix_ratios,
            'simulation_duration': self._validate_simulation_duration,
            'time_parameters': self._validate_time_parameters,
            'weather_parameters': self._validate_weather_parameters,
            'emergency_scenarios': self._validate_emergency_scenarios,
            'spawn_destinations': self._validate_spawn_destinations,
            'network_bounds': self._validate_network_bounds
        }
    
    def validate_template(self, template: ScenarioTemplate) -> List[str]:
        """Validate a scenario template and return list of errors"""
        errors = []
        
        for rule_name, rule_func in self.validation_rules.items():
            try:
                rule_errors = rule_func(template)
                errors.extend(rule_errors)
            except Exception as e:
                errors.append(f"Validation rule '{rule_name}' failed: {str(e)}")
        
        return errors
    
    def _validate_vehicle_mix_ratios(self, template: ScenarioTemplate) -> List[str]:
        """Validate vehicle mix ratios sum to 1.0"""
        errors = []
        
        total_ratio = sum(template.traffic_config.vehicle_mix_ratios.values())
        if abs(total_ratio - 1.0) > 0.01:  # Allow small floating point errors
            errors.append(f"Vehicle mix ratios sum to {total_ratio:.3f}, should sum to 1.0")
        
        # Check for negative ratios
        for vehicle_type, ratio in template.traffic_config.vehicle_mix_ratios.items():
            if ratio < 0:
                errors.append(f"Negative ratio {ratio} for vehicle type {vehicle_type.name}")
        
        return errors
    
    def _validate_simulation_duration(self, template: ScenarioTemplate) -> List[str]:
        """Validate simulation duration is reasonable"""
        errors = []
        
        if template.simulation_duration <= 0:
            errors.append("Simulation duration must be positive")
        elif template.simulation_duration > 86400:  # 24 hours
            errors.append("Simulation duration exceeds 24 hours, may cause performance issues")
        
        return errors
    
    def _validate_time_parameters(self, template: ScenarioTemplate) -> List[str]:
        """Validate time-related parameters"""
        errors = []
        
        if not (0 <= template.time_of_day <= 23):
            errors.append(f"Time of day {template.time_of_day} must be between 0 and 23")
        
        if not (0 <= template.day_of_week <= 6):
            errors.append(f"Day of week {template.day_of_week} must be between 0 and 6")
        
        return errors
    
    def _validate_weather_parameters(self, template: ScenarioTemplate) -> List[str]:
        """Validate weather parameters"""
        errors = []
        
        if not (0.0 <= template.weather_intensity <= 1.0):
            errors.append(f"Weather intensity {template.weather_intensity} must be between 0.0 and 1.0")
        
        return errors
    
    def _validate_emergency_scenarios(self, template: ScenarioTemplate) -> List[str]:
        """Validate emergency scenarios"""
        errors = []
        
        for i, emergency_data in enumerate(template.emergency_scenarios):
            if not isinstance(emergency_data, dict):
                errors.append(f"Emergency scenario {i} must be a dictionary")
                continue
            
            # Check required fields
            required_fields = ['scenario_type', 'location', 'severity']
            for field in required_fields:
                if field not in emergency_data:
                    errors.append(f"Emergency scenario {i} missing required field '{field}'")
            
            # Validate scenario type
            if 'scenario_type' in emergency_data:
                try:
                    EmergencyType[emergency_data['scenario_type']]
                except KeyError:
                    errors.append(f"Invalid emergency type '{emergency_data['scenario_type']}' in scenario {i}")
            
            # Validate severity
            if 'severity' in emergency_data:
                try:
                    SeverityLevel[emergency_data['severity']]
                except KeyError:
                    errors.append(f"Invalid severity level '{emergency_data['severity']}' in scenario {i}")
        
        return errors
    
    def _validate_spawn_destinations(self, template: ScenarioTemplate) -> List[str]:
        """Validate spawn points and destinations"""
        errors = []
        
        # Check spawn points format
        for i, spawn_point in enumerate(template.spawn_points):
            if not isinstance(spawn_point, dict):
                errors.append(f"Spawn point {i} must be a dictionary")
                continue
            
            required_fields = ['x', 'y']
            for field in required_fields:
                if field not in spawn_point:
                    errors.append(f"Spawn point {i} missing coordinate '{field}'")
        
        # Check destination points format
        for i, dest_point in enumerate(template.destination_points):
            if not isinstance(dest_point, dict):
                errors.append(f"Destination point {i} must be a dictionary")
                continue
            
            required_fields = ['x', 'y']
            for field in required_fields:
                if field not in dest_point:
                    errors.append(f"Destination point {i} missing coordinate '{field}'")
        
        return errors
    
    def _validate_network_bounds(self, template: ScenarioTemplate) -> List[str]:
        """Validate network bounds if specified"""
        errors = []
        
        if template.network_bounds is not None:
            required_bounds = ['north', 'south', 'east', 'west']
            for bound in required_bounds:
                if bound not in template.network_bounds:
                    errors.append(f"Network bounds missing '{bound}' coordinate")
            
            # Check logical consistency
            if all(bound in template.network_bounds for bound in required_bounds):
                if template.network_bounds['north'] <= template.network_bounds['south']:
                    errors.append("North bound must be greater than south bound")
                if template.network_bounds['east'] <= template.network_bounds['west']:
                    errors.append("East bound must be greater than west bound")
        
        return errors


class ScenarioManager:
    """Manages scenario templates for Indian traffic simulation"""
    
    def __init__(self, templates_directory: str = "scenarios"):
        """Initialize scenario manager"""
        self.templates_directory = Path(templates_directory)
        self.templates_directory.mkdir(exist_ok=True)
        
        # Template storage
        self.templates: Dict[str, ScenarioTemplate] = {}
        self.template_categories: Dict[str, List[str]] = {}
        
        # Validator
        self.validator = ScenarioValidator()
        
        # Load existing templates
        self.load_all_templates()
    
    def create_template(self, template_id: str, name: str, description: str,
                       category: str, traffic_config: Optional[IndianTrafficConfig] = None,
                       **kwargs) -> ScenarioTemplate:
        """Create a new scenario template"""
        
        if template_id in self.templates:
            raise ValueError(f"Template with ID '{template_id}' already exists")
        
        # Use provided config or create default
        if traffic_config is None:
            traffic_config = IndianTrafficConfig()
        
        # Create template
        template = ScenarioTemplate(
            template_id=template_id,
            name=name,
            description=description,
            category=category,
            traffic_config=traffic_config,
            **kwargs
        )
        
        # Validate template
        validation_errors = self.validator.validate_template(template)
        template.validation_errors = validation_errors
        template.is_validated = len(validation_errors) == 0
        
        # Store template
        self.templates[template_id] = template
        
        # Update categories
        if category not in self.template_categories:
            self.template_categories[category] = []
        self.template_categories[category].append(template_id)
        
        return template
    
    def load_template(self, template_id: str) -> Optional[ScenarioTemplate]:
        """Load a specific template by ID"""
        
        if template_id in self.templates:
            return self.templates[template_id]
        
        # Try to load from file
        template_file = self.templates_directory / f"{template_id}.json"
        if template_file.exists():
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                template = ScenarioTemplate.from_dict(template_data)
                
                # Validate loaded template
                validation_errors = self.validator.validate_template(template)
                template.validation_errors = validation_errors
                template.is_validated = len(validation_errors) == 0
                
                # Store in memory
                self.templates[template_id] = template
                
                # Update categories
                if template.category not in self.template_categories:
                    self.template_categories[template.category] = []
                if template_id not in self.template_categories[template.category]:
                    self.template_categories[template.category].append(template_id)
                
                return template
                
            except Exception as e:
                print(f"Error loading template '{template_id}': {str(e)}")
                return None
        
        return None
    
    def save_template(self, template: ScenarioTemplate, overwrite: bool = False) -> bool:
        """Save a template to file"""
        
        template_file = self.templates_directory / f"{template.template_id}.json"
        
        if template_file.exists() and not overwrite:
            raise FileExistsError(f"Template file '{template_file}' already exists")
        
        try:
            # Re-validate before saving
            validation_errors = self.validator.validate_template(template)
            template.validation_errors = validation_errors
            template.is_validated = len(validation_errors) == 0
            
            # Convert to dictionary and save
            template_dict = template.to_dict()
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_dict, f, indent=2, ensure_ascii=False)
            
            # Update in-memory storage
            self.templates[template.template_id] = template
            
            # Update categories
            if template.category not in self.template_categories:
                self.template_categories[template.category] = []
            if template.template_id not in self.template_categories[template.category]:
                self.template_categories[template.category].append(template.template_id)
            
            return True
            
        except Exception as e:
            print(f"Error saving template '{template.template_id}': {str(e)}")
            return False
    
    def load_all_templates(self) -> int:
        """Load all templates from the templates directory"""
        
        loaded_count = 0
        
        if not self.templates_directory.exists():
            return loaded_count
        
        for template_file in self.templates_directory.glob("*.json"):
            template_id = template_file.stem
            
            if self.load_template(template_id) is not None:
                loaded_count += 1
        
        return loaded_count
    
    def get_template(self, template_id: str) -> Optional[ScenarioTemplate]:
        """Get a template by ID (load if not in memory)"""
        return self.load_template(template_id)
    
    def list_templates(self, category: Optional[str] = None) -> List[str]:
        """List available template IDs, optionally filtered by category"""
        
        if category is None:
            return list(self.templates.keys())
        else:
            return self.template_categories.get(category, [])
    
    def get_categories(self) -> List[str]:
        """Get list of available template categories"""
        return list(self.template_categories.keys())
    
    def delete_template(self, template_id: str, delete_file: bool = True) -> bool:
        """Delete a template from memory and optionally from file"""
        
        # Remove from memory
        if template_id in self.templates:
            template = self.templates[template_id]
            del self.templates[template_id]
            
            # Remove from categories
            if template.category in self.template_categories:
                if template_id in self.template_categories[template.category]:
                    self.template_categories[template.category].remove(template_id)
                
                # Remove empty categories
                if not self.template_categories[template.category]:
                    del self.template_categories[template.category]
        
        # Remove file if requested
        if delete_file:
            template_file = self.templates_directory / f"{template_id}.json"
            if template_file.exists():
                try:
                    template_file.unlink()
                    return True
                except Exception as e:
                    print(f"Error deleting template file '{template_file}': {str(e)}")
                    return False
        
        return True
    
    def validate_template(self, template: ScenarioTemplate) -> List[str]:
        """Validate a template and return validation errors"""
        return self.validator.validate_template(template)
    
    def get_template_summary(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a template without loading full details"""
        
        template = self.get_template(template_id)
        if template is None:
            return None
        
        return {
            'template_id': template.template_id,
            'name': template.name,
            'description': template.description,
            'category': template.category,
            'version': template.version,
            'created_date': template.created_date,
            'simulation_duration': template.simulation_duration,
            'weather_type': template.weather_type.name,
            'emergency_count': len(template.emergency_scenarios),
            'is_validated': template.is_validated,
            'validation_error_count': len(template.validation_errors)
        }
    
    def search_templates(self, query: str, search_fields: Optional[List[str]] = None) -> List[str]:
        """Search templates by query string in specified fields"""
        
        if search_fields is None:
            search_fields = ['name', 'description', 'category']
        
        query_lower = query.lower()
        matching_templates = []
        
        for template_id, template in self.templates.items():
            for field in search_fields:
                if hasattr(template, field):
                    field_value = str(getattr(template, field)).lower()
                    if query_lower in field_value:
                        matching_templates.append(template_id)
                        break
        
        return matching_templates
    
    def clone_template(self, source_template_id: str, new_template_id: str,
                      new_name: Optional[str] = None) -> Optional[ScenarioTemplate]:
        """Clone an existing template with a new ID"""
        
        source_template = self.get_template(source_template_id)
        if source_template is None:
            return None
        
        if new_template_id in self.templates:
            raise ValueError(f"Template with ID '{new_template_id}' already exists")
        
        # Create copy of template data
        template_dict = source_template.to_dict()
        template_dict['template_id'] = new_template_id
        template_dict['created_date'] = datetime.now().isoformat()
        
        if new_name is not None:
            template_dict['name'] = new_name
        else:
            template_dict['name'] = f"Copy of {source_template.name}"
        
        # Create new template
        new_template = ScenarioTemplate.from_dict(template_dict)
        
        # Validate and store
        validation_errors = self.validator.validate_template(new_template)
        new_template.validation_errors = validation_errors
        new_template.is_validated = len(validation_errors) == 0
        
        self.templates[new_template_id] = new_template
        
        # Update categories
        if new_template.category not in self.template_categories:
            self.template_categories[new_template.category] = []
        self.template_categories[new_template.category].append(new_template_id)
        
        return new_template
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded templates"""
        
        total_templates = len(self.templates)
        validated_templates = sum(1 for t in self.templates.values() if t.is_validated)
        
        category_counts = {cat: len(templates) for cat, templates in self.template_categories.items()}
        
        return {
            'total_templates': total_templates,
            'validated_templates': validated_templates,
            'invalid_templates': total_templates - validated_templates,
            'categories': len(self.template_categories),
            'category_counts': category_counts,
            'templates_directory': str(self.templates_directory)
        }