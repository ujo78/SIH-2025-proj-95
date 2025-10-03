# Full Indian Traffic Simulation

A comprehensive 3D traffic simulation featuring Indian traffic patterns, vehicle types, and road conditions.

## Features

### 3D Visualization
- **Roads and Intersections**: Realistic road network with lane markings
- **Traffic Lights**: Functional traffic lights with red/yellow/green cycling
- **Ground Plane**: Textured ground surface for context

### Vehicle Types
- **Cars**: Various colored passenger vehicles
- **Buses**: Large yellow public transport buses
- **Trucks**: Brown cargo trucks with cargo areas
- **Motorcycles**: Small black two-wheelers
- **Auto-rickshaws**: Yellow three-wheelers with canopies
- **Bicycles**: Eco-friendly two-wheelers

### Indian Traffic Features
- **Mumbai Intersection Scenario**: High-density mixed traffic with frequent auto-rickshaws
- **Vehicle Mix Ratios**: Realistic proportions based on Indian cities
- **Behavior Models**: Indian-specific driving patterns and lane discipline
- **Emergency Scenarios**: Accidents, flooding, construction zones
- **Weather Effects**: Monsoon, dust storms, fog conditions

### Interactive Controls
- **Camera Movement**: WASD keys for navigation
- **Zoom**: Mouse wheel or Q/E keys
- **Simulation Control**: Space bar to pause/resume
- **Speed Control**: Slider to adjust simulation speed
- **Emergency Triggers**: Buttons to create accidents or flooding

## Requirements

### Required Dependencies
```bash
pip install networkx
```

### Optional Dependencies (for enhanced features)
```bash
# For 3D visualization (recommended)
pip install panda3d

# For real road networks (optional)
pip install osmnx geopandas
```

## Usage

### Basic Usage
```bash
python full_traffic_simulation.py
```

### Using the Demo Script
```bash
python run_full_simulation.py
```

### Console Mode (without Panda3D)
If Panda3D is not installed, the simulation will run in console mode with text output:
```
Running traffic simulation in console mode...
==================================================
Loaded scenario: Mumbai Busy Intersection
Time: 0s | Vehicles: 0 | Emergencies: 0
Spawned AUTO_RICKSHAW (ID: console_vehicle_0)
Spawned CAR (ID: console_vehicle_1)
Time: 10s | Vehicles: 5 | Emergencies: 0
```

## Controls

### Camera Controls
- **W**: Move camera forward
- **S**: Move camera backward
- **A**: Move camera left
- **D**: Move camera right
- **Q**: Move camera up
- **E**: Move camera down
- **Mouse Wheel**: Zoom in/out

### Simulation Controls
- **Space**: Pause/Resume simulation
- **Speed Slider**: Adjust simulation speed (0.1x to 3.0x)

### Emergency Controls
- **Accident Button**: Trigger a traffic accident
- **Flooding Button**: Trigger road flooding

## Scenarios

The simulation includes several pre-built Indian traffic scenarios:

### Mumbai Intersection
- High auto-rickshaw density (20%)
- Extended peak hours
- Monsoon weather patterns
- Dense urban traffic

### Bangalore Tech Corridor
- Higher car usage (45%)
- Office timing patterns
- Organized bus services
- IT corridor characteristics

### Delhi Roundabout
- Heavy truck presence
- Dust storm conditions
- Winter fog effects
- Major roundabout traffic

## Architecture

### Core Components

1. **Vehicle3D**: 3D vehicle representations with different models for each type
2. **Road3D**: Road segments with lane markings and realistic appearance
3. **TrafficLight3D**: Functional traffic lights with state management
4. **FullTrafficSimulation**: Main simulation class managing all components

### Indian Traffic Integration

- **ScenarioManager**: Loads and manages traffic scenarios
- **IndianTrafficConfig**: Configuration for vehicle mixes and behaviors
- **EmergencyManager**: Handles accidents, flooding, and other emergencies
- **WeatherManager**: Manages weather effects and seasonal patterns

### Simulation Loop

1. **Vehicle Spawning**: Creates vehicles based on scenario parameters
2. **Path Planning**: Uses NetworkX for route calculation
3. **Movement Update**: Smooth vehicle animation along roads
4. **Emergency Handling**: Dynamic scenario management
5. **UI Updates**: Real-time statistics and controls

## Customization

### Adding New Vehicle Types
```python
def _create_custom_vehicle_model(self):
    """Create a custom vehicle model"""
    cm = CardMaker("custom_vehicle")
    cm.setFrame(-1.0, 1.0, -0.5, 0.5)
    vehicle_body = self.render_root.attachNewNode(cm.generate())
    vehicle_body.setColor(1, 0, 1, 1)  # Magenta color
    return vehicle_body
```

### Creating Custom Scenarios
```python
from indian_features.scenario_templates import ScenarioTemplate
from indian_features.config import IndianTrafficConfig

# Create custom vehicle mix
custom_mix = {
    VehicleType.CAR: 0.6,
    VehicleType.MOTORCYCLE: 0.3,
    VehicleType.BUS: 0.1
}

# Create custom scenario
custom_scenario = ScenarioTemplate(
    template_id="custom_scenario",
    name="Custom Traffic Scenario",
    description="A custom traffic scenario",
    category="custom",
    traffic_config=IndianTrafficConfig(vehicle_mix_ratios=custom_mix)
)
```

### Modifying Road Networks
The simulation can use either:
- **Mock Network**: Simple grid-based road network (default)
- **OSMnx Network**: Real-world road data from OpenStreetMap

To use a different location:
```python
# In setup_road_network method
center_point = (28.6139, 77.2090)  # Delhi coordinates
self.road_graph = ox.graph_from_point(center_point, dist=1000, network_type="drive")
```

## Performance Tips

1. **Reduce Vehicle Count**: Lower `max_vehicles` in traffic config
2. **Simplify Road Network**: Use smaller `dist` parameter for OSMnx
3. **Adjust Update Frequency**: Modify task intervals for better performance
4. **Disable Features**: Turn off traffic lights or emergency scenarios if needed

## Troubleshooting

### Common Issues

**Panda3D Import Error**
```
ImportError: No module named 'panda3d'
```
Solution: Install Panda3D with `pip install panda3d`

**OSMnx Network Loading Fails**
```
Failed to load OSMnx network: [error]
```
Solution: The simulation will fall back to mock network automatically

**Low Frame Rate**
- Reduce number of vehicles
- Simplify road network
- Lower simulation speed

### Debug Mode
Enable debug output by modifying the print statements in the simulation:
```python
# Add to simulation_task method
if int(self.current_time) % 5 == 0:  # Every 5 seconds
    print(f"Debug: {len(self.active_vehicles)} vehicles, {self.current_time:.1f}s")
```

## Contributing

To extend the simulation:

1. **Add New Vehicle Types**: Extend the `VehicleType` enum and create corresponding 3D models
2. **Create New Scenarios**: Use the scenario template system
3. **Implement New Features**: Add weather effects, road conditions, or traffic rules
4. **Improve Visualization**: Enhance 3D models, lighting, or UI elements

## License

This simulation is part of the Indian Traffic Digital Twin project and follows the same licensing terms.