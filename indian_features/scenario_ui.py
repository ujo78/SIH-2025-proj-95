"""
Scenario Configuration UI Integration

This module extends the existing Folium-based interface to support scenario selection,
parameter adjustment, and configuration management for Indian traffic scenarios.
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import folium
from folium import plugins

from .scenario_manager import ScenarioManager, ScenarioTemplate
from .scenario_templates import create_all_default_templates, initialize_default_templates
from .enums import VehicleType, WeatherType, EmergencyType, SeverityLevel
from .config import IndianTrafficConfig


class ScenarioUIManager:
    """Manages UI integration for scenario configuration"""
    
    def __init__(self, scenario_manager: Optional[ScenarioManager] = None):
        """Initialize scenario UI manager"""
        
        if scenario_manager is None:
            scenario_manager = ScenarioManager()
            # Initialize with default templates if none exist
            if len(scenario_manager.templates) == 0:
                initialize_default_templates(scenario_manager)
        
        self.scenario_manager = scenario_manager
        self.current_template: Optional[ScenarioTemplate] = None
        self.custom_parameters: Dict[str, Any] = {}
    
    def create_scenario_selection_control(self, folium_map: folium.Map) -> None:
        """Add scenario selection control to Folium map"""
        
        # Get available templates grouped by category
        categories = self.scenario_manager.get_categories()
        
        # Create HTML for scenario selection
        scenario_options_html = self._generate_scenario_options_html(categories)
        
        # Create the control HTML
        control_html = f"""
        <div id="scenario-control" class="scenario-control">
            <div class="control-header">
                <h3>Scenario Configuration</h3>
                <button id="toggle-control" class="toggle-btn">−</button>
            </div>
            <div id="control-content" class="control-content">
                <div class="section">
                    <label for="scenario-select">Select Scenario Template:</label>
                    <select id="scenario-select" onchange="loadScenarioTemplate()">
                        <option value="">-- Select Template --</option>
                        {scenario_options_html}
                    </select>
                </div>
                
                <div class="section" id="scenario-details" style="display: none;">
                    <h4 id="scenario-name"></h4>
                    <p id="scenario-description"></p>
                    
                    <div class="parameter-group">
                        <h5>Basic Parameters</h5>
                        <div class="param-row">
                            <label for="simulation-duration">Duration (seconds):</label>
                            <input type="number" id="simulation-duration" min="60" max="86400" step="60">
                        </div>
                        <div class="param-row">
                            <label for="time-of-day">Time of Day (0-23):</label>
                            <input type="number" id="time-of-day" min="0" max="23" step="1">
                        </div>
                        <div class="param-row">
                            <label for="day-of-week">Day of Week:</label>
                            <select id="day-of-week">
                                <option value="0">Monday</option>
                                <option value="1">Tuesday</option>
                                <option value="2">Wednesday</option>
                                <option value="3">Thursday</option>
                                <option value="4">Friday</option>
                                <option value="5">Saturday</option>
                                <option value="6">Sunday</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="parameter-group">
                        <h5>Weather Conditions</h5>
                        <div class="param-row">
                            <label for="weather-type">Weather:</label>
                            <select id="weather-type">
                                <option value="CLEAR">Clear</option>
                                <option value="LIGHT_RAIN">Light Rain</option>
                                <option value="HEAVY_RAIN">Heavy Rain</option>
                                <option value="FOG">Fog</option>
                                <option value="DUST_STORM">Dust Storm</option>
                            </select>
                        </div>
                        <div class="param-row">
                            <label for="weather-intensity">Intensity (0.0-1.0):</label>
                            <input type="range" id="weather-intensity" min="0" max="1" step="0.1" value="1.0">
                            <span id="weather-intensity-value">1.0</span>
                        </div>
                    </div>
                    
                    <div class="parameter-group">
                        <h5>Vehicle Mix</h5>
                        <div id="vehicle-mix-controls"></div>
                        <div class="param-row">
                            <small>Total: <span id="vehicle-mix-total">1.00</span></small>
                        </div>
                    </div>
                    
                    <div class="parameter-group">
                        <h5>Emergency Scenarios</h5>
                        <div id="emergency-controls">
                            <button onclick="addEmergencyScenario()" class="add-btn">Add Emergency</button>
                            <div id="emergency-list"></div>
                        </div>
                    </div>
                    
                    <div class="action-buttons">
                        <button onclick="previewScenario()" class="preview-btn">Preview</button>
                        <button onclick="saveScenario()" class="save-btn">Save Configuration</button>
                        <button onclick="exportScenario()" class="export-btn">Export JSON</button>
                        <button onclick="runSimulation()" class="run-btn">Run Simulation</button>
                    </div>
                </div>
            </div>
        </div>
        """
        
        # Add CSS styles
        css_styles = self._generate_css_styles()
        
        # Add JavaScript functions
        js_functions = self._generate_javascript_functions()
        
        # Combine HTML, CSS, and JS
        full_html = f"""
        <style>
        {css_styles}
        </style>
        
        {control_html}
        
        <script>
        {js_functions}
        </script>
        """
        
        # Add to map
        folium_map.get_root().html.add_child(folium.Element(full_html))
    
    def _generate_scenario_options_html(self, categories: List[str]) -> str:
        """Generate HTML options for scenario selection"""
        
        options_html = ""
        
        for category in sorted(categories):
            template_ids = self.scenario_manager.list_templates(category)
            
            if template_ids:
                options_html += f'<optgroup label="{category.title()}">\n'
                
                for template_id in sorted(template_ids):
                    template = self.scenario_manager.get_template(template_id)
                    if template:
                        options_html += f'<option value="{template_id}">{template.name}</option>\n'
                
                options_html += '</optgroup>\n'
        
        return options_html
    
    def _generate_css_styles(self) -> str:
        """Generate CSS styles for the scenario control"""
        
        return """
        .scenario-control {
            position: fixed;
            top: 10px;
            right: 10px;
            width: 350px;
            max-height: 80vh;
            background: white;
            border: 2px solid #333;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            z-index: 1000;
            font-family: Arial, sans-serif;
            font-size: 12px;
        }
        
        .control-header {
            background: #2c3e50;
            color: white;
            padding: 10px;
            border-radius: 6px 6px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .control-header h3 {
            margin: 0;
            font-size: 14px;
        }
        
        .toggle-btn {
            background: none;
            border: none;
            color: white;
            font-size: 16px;
            cursor: pointer;
            padding: 0;
            width: 20px;
            height: 20px;
        }
        
        .control-content {
            padding: 15px;
            max-height: 70vh;
            overflow-y: auto;
        }
        
        .section {
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        
        .section:last-child {
            border-bottom: none;
        }
        
        .parameter-group {
            margin: 10px 0;
        }
        
        .parameter-group h5 {
            margin: 0 0 8px 0;
            color: #34495e;
            font-size: 12px;
            font-weight: bold;
        }
        
        .param-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 5px 0;
        }
        
        .param-row label {
            flex: 1;
            margin-right: 10px;
            font-size: 11px;
        }
        
        .param-row input, .param-row select {
            flex: 1;
            padding: 3px 5px;
            border: 1px solid #ddd;
            border-radius: 3px;
            font-size: 11px;
        }
        
        .param-row input[type="range"] {
            flex: 0.7;
        }
        
        .param-row span {
            flex: 0.3;
            text-align: center;
            font-size: 10px;
        }
        
        .vehicle-mix-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 3px 0;
        }
        
        .vehicle-mix-item label {
            flex: 1;
            font-size: 10px;
        }
        
        .vehicle-mix-item input {
            flex: 0.4;
            padding: 2px 4px;
            font-size: 10px;
        }
        
        .emergency-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 8px;
            margin: 5px 0;
        }
        
        .emergency-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }
        
        .emergency-item-header strong {
            font-size: 11px;
        }
        
        .remove-btn {
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 3px;
            padding: 2px 6px;
            font-size: 10px;
            cursor: pointer;
        }
        
        .action-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 5px;
            margin-top: 15px;
        }
        
        .action-buttons button {
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            font-weight: bold;
        }
        
        .preview-btn {
            background: #17a2b8;
            color: white;
        }
        
        .save-btn {
            background: #28a745;
            color: white;
        }
        
        .export-btn {
            background: #6c757d;
            color: white;
        }
        
        .run-btn {
            background: #007bff;
            color: white;
        }
        
        .add-btn {
            background: #ffc107;
            color: #212529;
            border: none;
            border-radius: 3px;
            padding: 5px 10px;
            font-size: 10px;
            cursor: pointer;
            margin-bottom: 10px;
        }
        
        #scenario-name {
            color: #2c3e50;
            margin: 0 0 5px 0;
            font-size: 13px;
        }
        
        #scenario-description {
            color: #6c757d;
            margin: 0 0 10px 0;
            font-size: 11px;
            line-height: 1.4;
        }
        
        .collapsed .control-content {
            display: none;
        }
        """
    
    def _generate_javascript_functions(self) -> str:
        """Generate JavaScript functions for scenario control"""
        
        # Get template data for JavaScript
        templates_data = {}
        for template_id in self.scenario_manager.list_templates():
            template = self.scenario_manager.get_template(template_id)
            if template:
                templates_data[template_id] = template.to_dict()
        
        templates_json = json.dumps(templates_data, indent=2)
        
        return f"""
        // Template data
        const scenarioTemplates = {templates_json};
        
        // Current template state
        let currentTemplate = null;
        let emergencyCounter = 0;
        
        // Toggle control visibility
        function toggleControl() {{
            const control = document.getElementById('scenario-control');
            const toggleBtn = document.getElementById('toggle-control');
            
            if (control.classList.contains('collapsed')) {{
                control.classList.remove('collapsed');
                toggleBtn.textContent = '−';
            }} else {{
                control.classList.add('collapsed');
                toggleBtn.textContent = '+';
            }}
        }}
        
        // Load scenario template
        function loadScenarioTemplate() {{
            const select = document.getElementById('scenario-select');
            const templateId = select.value;
            
            if (!templateId) {{
                document.getElementById('scenario-details').style.display = 'none';
                return;
            }}
            
            currentTemplate = scenarioTemplates[templateId];
            if (!currentTemplate) return;
            
            // Show details section
            document.getElementById('scenario-details').style.display = 'block';
            
            // Update basic info
            document.getElementById('scenario-name').textContent = currentTemplate.name;
            document.getElementById('scenario-description').textContent = currentTemplate.description;
            
            // Update parameters
            document.getElementById('simulation-duration').value = currentTemplate.simulation_duration;
            document.getElementById('time-of-day').value = currentTemplate.time_of_day;
            document.getElementById('day-of-week').value = currentTemplate.day_of_week;
            document.getElementById('weather-type').value = currentTemplate.weather_type;
            document.getElementById('weather-intensity').value = currentTemplate.weather_intensity;
            document.getElementById('weather-intensity-value').textContent = currentTemplate.weather_intensity;
            
            // Update vehicle mix
            updateVehicleMixControls();
            
            // Update emergency scenarios
            updateEmergencyControls();
        }}
        
        // Update vehicle mix controls
        function updateVehicleMixControls() {{
            if (!currentTemplate) return;
            
            const container = document.getElementById('vehicle-mix-controls');
            container.innerHTML = '';
            
            const vehicleTypes = ['CAR', 'MOTORCYCLE', 'AUTO_RICKSHAW', 'BUS', 'TRUCK', 'BICYCLE'];
            const vehicleMix = currentTemplate.traffic_config.vehicle_mix_ratios;
            
            vehicleTypes.forEach(vehicleType => {{
                const ratio = vehicleMix[vehicleType] || 0;
                
                const div = document.createElement('div');
                div.className = 'vehicle-mix-item';
                div.innerHTML = `
                    <label>${{vehicleType.replace('_', ' ')}}:</label>
                    <input type="number" 
                           id="vehicle-${{vehicleType.toLowerCase()}}" 
                           min="0" max="1" step="0.01" 
                           value="${{ratio.toFixed(2)}}"
                           onchange="updateVehicleMixTotal()">
                `;
                container.appendChild(div);
            }});
            
            updateVehicleMixTotal();
        }}
        
        // Update vehicle mix total
        function updateVehicleMixTotal() {{
            const vehicleTypes = ['CAR', 'MOTORCYCLE', 'AUTO_RICKSHAW', 'BUS', 'TRUCK', 'BICYCLE'];
            let total = 0;
            
            vehicleTypes.forEach(vehicleType => {{
                const input = document.getElementById(`vehicle-${{vehicleType.toLowerCase()}}`);
                if (input) {{
                    total += parseFloat(input.value) || 0;
                }}
            }});
            
            document.getElementById('vehicle-mix-total').textContent = total.toFixed(2);
            
            // Highlight if total is not 1.0
            const totalElement = document.getElementById('vehicle-mix-total');
            if (Math.abs(total - 1.0) > 0.01) {{
                totalElement.style.color = '#dc3545';
                totalElement.style.fontWeight = 'bold';
            }} else {{
                totalElement.style.color = '#28a745';
                totalElement.style.fontWeight = 'bold';
            }}
        }}
        
        // Update emergency controls
        function updateEmergencyControls() {{
            if (!currentTemplate) return;
            
            const container = document.getElementById('emergency-list');
            container.innerHTML = '';
            emergencyCounter = 0;
            
            currentTemplate.emergency_scenarios.forEach((emergency, index) => {{
                addEmergencyItem(emergency, index);
            }});
        }}
        
        // Add emergency scenario
        function addEmergencyScenario() {{
            const emergency = {{
                scenario_type: 'ACCIDENT',
                severity: 'MEDIUM',
                location: {{x: 0, y: 0, z: 0}},
                estimated_duration_minutes: 30
            }};
            
            addEmergencyItem(emergency, emergencyCounter++);
        }}
        
        // Add emergency item to UI
        function addEmergencyItem(emergency, index) {{
            const container = document.getElementById('emergency-list');
            
            const div = document.createElement('div');
            div.className = 'emergency-item';
            div.id = `emergency-${{index}}`;
            
            div.innerHTML = `
                <div class="emergency-item-header">
                    <strong>${{emergency.scenario_type}} - ${{emergency.severity}}</strong>
                    <button class="remove-btn" onclick="removeEmergency(${{index}})">Remove</button>
                </div>
                <div class="param-row">
                    <label>Type:</label>
                    <select id="emergency-type-${{index}}" onchange="updateEmergency(${{index}})">
                        <option value="ACCIDENT" ${{emergency.scenario_type === 'ACCIDENT' ? 'selected' : ''}}>Accident</option>
                        <option value="FLOODING" ${{emergency.scenario_type === 'FLOODING' ? 'selected' : ''}}>Flooding</option>
                        <option value="CONSTRUCTION" ${{emergency.scenario_type === 'CONSTRUCTION' ? 'selected' : ''}}>Construction</option>
                        <option value="ROAD_CLOSURE" ${{emergency.scenario_type === 'ROAD_CLOSURE' ? 'selected' : ''}}>Road Closure</option>
                    </select>
                </div>
                <div class="param-row">
                    <label>Severity:</label>
                    <select id="emergency-severity-${{index}}" onchange="updateEmergency(${{index}})">
                        <option value="LOW" ${{emergency.severity === 'LOW' ? 'selected' : ''}}>Low</option>
                        <option value="MEDIUM" ${{emergency.severity === 'MEDIUM' ? 'selected' : ''}}>Medium</option>
                        <option value="HIGH" ${{emergency.severity === 'HIGH' ? 'selected' : ''}}>High</option>
                        <option value="CRITICAL" ${{emergency.severity === 'CRITICAL' ? 'selected' : ''}}>Critical</option>
                    </select>
                </div>
                <div class="param-row">
                    <label>Duration (min):</label>
                    <input type="number" id="emergency-duration-${{index}}" 
                           value="${{emergency.estimated_duration_minutes || 30}}" 
                           min="5" max="480" step="5"
                           onchange="updateEmergency(${{index}})">
                </div>
            `;
            
            container.appendChild(div);
        }}
        
        // Remove emergency scenario
        function removeEmergency(index) {{
            const element = document.getElementById(`emergency-${{index}}`);
            if (element) {{
                element.remove();
            }}
        }}
        
        // Update emergency scenario
        function updateEmergency(index) {{
            // Update emergency data based on form inputs
            console.log(`Emergency ${{index}} updated`);
        }}
        
        // Preview scenario
        function previewScenario() {{
            if (!currentTemplate) {{
                alert('Please select a scenario template first.');
                return;
            }}
            
            const config = getCurrentConfiguration();
            console.log('Preview configuration:', config);
            
            // Show preview information
            alert(`Preview: ${{config.name}}\\n\\nDuration: ${{config.simulation_duration}}s\\nWeather: ${{config.weather_type}}\\nVehicles: ${{config.max_vehicles}}`);
        }}
        
        // Save scenario configuration
        function saveScenario() {{
            if (!currentTemplate) {{
                alert('Please select a scenario template first.');
                return;
            }}
            
            const config = getCurrentConfiguration();
            const templateId = prompt('Enter template ID for saving:', `custom_${{Date.now()}}`);
            
            if (templateId) {{
                // Save configuration (would need backend integration)
                console.log('Saving configuration:', templateId, config);
                alert(`Configuration saved as: ${{templateId}}`);
            }}
        }}
        
        // Export scenario as JSON
        function exportScenario() {{
            if (!currentTemplate) {{
                alert('Please select a scenario template first.');
                return;
            }}
            
            const config = getCurrentConfiguration();
            const jsonStr = JSON.stringify(config, null, 2);
            
            // Create download link
            const blob = new Blob([jsonStr], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `scenario_${{config.template_id}}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }}
        
        // Run simulation with current configuration
        function runSimulation() {{
            if (!currentTemplate) {{
                alert('Please select a scenario template first.');
                return;
            }}
            
            const config = getCurrentConfiguration();
            console.log('Running simulation with config:', config);
            
            // This would trigger the actual simulation
            alert(`Starting simulation: ${{config.name}}\\n\\nCheck console for detailed configuration.`);
        }}
        
        // Get current configuration from UI
        function getCurrentConfiguration() {{
            if (!currentTemplate) return null;
            
            const config = JSON.parse(JSON.stringify(currentTemplate));
            
            // Update with current UI values
            config.simulation_duration = parseFloat(document.getElementById('simulation-duration').value);
            config.time_of_day = parseInt(document.getElementById('time-of-day').value);
            config.day_of_week = parseInt(document.getElementById('day-of-week').value);
            config.weather_type = document.getElementById('weather-type').value;
            config.weather_intensity = parseFloat(document.getElementById('weather-intensity').value);
            
            // Update vehicle mix
            const vehicleTypes = ['CAR', 'MOTORCYCLE', 'AUTO_RICKSHAW', 'BUS', 'TRUCK', 'BICYCLE'];
            vehicleTypes.forEach(vehicleType => {{
                const input = document.getElementById(`vehicle-${{vehicleType.toLowerCase()}}`);
                if (input) {{
                    config.traffic_config.vehicle_mix_ratios[vehicleType] = parseFloat(input.value);
                }}
            }});
            
            return config;
        }}
        
        // Update weather intensity display
        document.addEventListener('DOMContentLoaded', function() {{
            const weatherIntensity = document.getElementById('weather-intensity');
            if (weatherIntensity) {{
                weatherIntensity.addEventListener('input', function() {{
                    document.getElementById('weather-intensity-value').textContent = this.value;
                }});
            }}
            
            // Add toggle functionality
            const toggleBtn = document.getElementById('toggle-control');
            if (toggleBtn) {{
                toggleBtn.addEventListener('click', toggleControl);
            }}
        }});
        """
    
    def add_scenario_preview_layer(self, folium_map: folium.Map, 
                                 template: ScenarioTemplate) -> None:
        """Add scenario preview visualization to the map"""
        
        # Add markers for emergency scenarios
        for i, emergency_data in enumerate(template.emergency_scenarios):
            if 'location' in emergency_data:
                location = emergency_data['location']
                
                # Determine marker color based on emergency type
                color_map = {
                    'ACCIDENT': 'red',
                    'FLOODING': 'blue',
                    'CONSTRUCTION': 'orange',
                    'ROAD_CLOSURE': 'black'
                }
                
                emergency_type = emergency_data.get('scenario_type', 'ACCIDENT')
                color = color_map.get(emergency_type, 'gray')
                
                folium.Marker(
                    location=[location.get('y', 0), location.get('x', 0)],
                    popup=f"{emergency_type}: {emergency_data.get('severity', 'MEDIUM')}",
                    tooltip=f"Emergency {i+1}",
                    icon=folium.Icon(color=color, icon='warning-sign', prefix='fa')
                ).add_to(folium_map)
        
        # Add network bounds if specified
        if template.network_bounds:
            bounds = template.network_bounds
            
            # Create rectangle for network bounds
            folium.Rectangle(
                bounds=[[bounds['south'], bounds['west']], 
                       [bounds['north'], bounds['east']]],
                color='green',
                weight=2,
                fill=False,
                popup="Simulation Area"
            ).add_to(folium_map)
        
        # Add spawn and destination points if specified
        for i, spawn_point in enumerate(template.spawn_points):
            folium.CircleMarker(
                location=[spawn_point.get('y', 0), spawn_point.get('x', 0)],
                radius=5,
                color='green',
                fill=True,
                popup=f"Spawn Point {i+1}",
                tooltip="Vehicle Spawn"
            ).add_to(folium_map)
        
        for i, dest_point in enumerate(template.destination_points):
            folium.CircleMarker(
                location=[dest_point.get('y', 0), dest_point.get('x', 0)],
                radius=5,
                color='red',
                fill=True,
                popup=f"Destination {i+1}",
                tooltip="Vehicle Destination"
            ).add_to(folium_map)
    
    def create_enhanced_folium_map(self, center: Tuple[float, float], 
                                 zoom_start: int = 14) -> folium.Map:
        """Create enhanced Folium map with scenario controls"""
        
        # Create base map
        folium_map = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles="OpenStreetMap",
            prefer_canvas=True
        )
        
        # Add scenario selection control
        self.create_scenario_selection_control(folium_map)
        
        # Add additional map controls
        self._add_map_controls(folium_map)
        
        return folium_map
    
    def _add_map_controls(self, folium_map: folium.Map) -> None:
        """Add additional map controls and plugins"""
        
        # Add fullscreen control
        plugins.Fullscreen().add_to(folium_map)
        
        # Add measure control
        plugins.MeasureControl().add_to(folium_map)
        
        # Add draw control for custom areas
        draw = plugins.Draw(
            export=True,
            filename='scenario_areas.geojson',
            position='topleft'
        )
        draw.add_to(folium_map)
        
        # Add minimap
        minimap = plugins.MiniMap(toggle_display=True)
        folium_map.add_child(minimap)
    
    def export_scenario_configuration(self, template: ScenarioTemplate, 
                                    filepath: str) -> bool:
        """Export scenario configuration to JSON file"""
        
        try:
            config_data = template.to_dict()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error exporting scenario configuration: {str(e)}")
            return False
    
    def import_scenario_configuration(self, filepath: str) -> Optional[ScenarioTemplate]:
        """Import scenario configuration from JSON file"""
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            template = ScenarioTemplate.from_dict(config_data)
            
            # Validate imported template
            validation_errors = self.scenario_manager.validate_template(template)
            if validation_errors:
                print(f"Validation errors in imported template: {validation_errors}")
            
            return template
            
        except Exception as e:
            print(f"Error importing scenario configuration: {str(e)}")
            return None
    
    def get_scenario_statistics(self) -> Dict[str, Any]:
        """Get statistics about available scenarios"""
        
        return self.scenario_manager.get_statistics()


def create_scenario_enabled_map(center: Tuple[float, float], 
                              zoom_start: int = 14,
                              scenario_manager: Optional[ScenarioManager] = None) -> Tuple[folium.Map, ScenarioUIManager]:
    """Create a Folium map with scenario configuration capabilities"""
    
    # Create UI manager
    ui_manager = ScenarioUIManager(scenario_manager)
    
    # Create enhanced map
    folium_map = ui_manager.create_enhanced_folium_map(center, zoom_start)
    
    return folium_map, ui_manager