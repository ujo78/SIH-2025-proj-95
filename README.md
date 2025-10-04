# 🚗 Indian Traffic Digital Twin

> A comprehensive 3D traffic simulation platform designed specifically for Indian road conditions, vehicle types, and driving behaviors.

![Traffic Simulation Screenshot](https://img.shields.io/badge/Status-Active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 What Makes This Special

This isn't just another traffic simulator. It's a **digital twin** of Indian traffic that captures the unique chaos, patterns, and behaviors that make Indian roads distinctive:

- **Mixed Traffic Reality**: Cars sharing lanes with auto-rickshaws, motorcycles weaving through traffic, and buses dominating intersections
- **Authentic Behaviors**: Lane discipline variations, aggressive overtaking, and the famous Indian "gap acceptance" patterns  
- **Real Indian Conditions**: Monsoon effects, dust storms, road quality variations, and emergency scenarios
- **MATLAB Integration**: Export data for advanced analysis in MATLAB, Simulink, and RoadRunner

## 🎯 Key Features

### 🚙 Authentic Indian Vehicle Mix
- **Cars** (35%): Various passenger vehicles with realistic Indian driving patterns
- **Motorcycles** (30%): Highly maneuverable two-wheelers with aggressive lane-changing
- **Auto-rickshaws** (15%): Three-wheelers with erratic but predictable behavior patterns
- **Buses** (10%): Large public transport with right-of-way dominance
- **Trucks** (8%): Heavy vehicles with conservative driving patterns
- **Bicycles** (2%): Eco-friendly transport with minimal lane discipline

### 🌦️ Dynamic Environmental Conditions
- **Weather Systems**: Clear, light rain, heavy rain, fog, and dust storms
- **Road Quality**: From excellent highways to poorly maintained rural roads
- **Time-of-Day Effects**: Rush hour patterns, night-time behaviors
- **Seasonal Variations**: Monsoon impacts, winter fog effects

### 🚨 Emergency Scenario Simulation
- **Traffic Accidents**: Multi-vehicle collision scenarios with realistic response
- **Road Flooding**: Monsoon-induced waterlogging with traffic rerouting
- **Construction Zones**: Lane closures and speed restrictions
- **Emergency Vehicles**: Ambulance and fire truck priority handling

### 📊 Advanced Analytics & Export
- **Real-time Metrics**: Speed, density, throughput, and congestion analysis
- **MATLAB Integration**: Export trajectories, road networks, and metrics
- **Simulink Connectivity**: Real-time data streaming for control system testing
- **RoadRunner Import**: Convert and use professional road scene files

## 🚀 Quick Start

### Prerequisites
```bash
# Core dependencies
pip install networkx

# For 3D visualization (recommended)
pip install panda3d

# For real road networks (optional)
pip install osmnx geopandas

# For MATLAB integration (optional)
# Requires MATLAB with Automated Driving Toolbox
```

### Basic Usage

**Run the full 3D simulation:**
```bash
python full_traffic_simulation.py
```

**Run with demo scenarios:**
```bash
python run_full_simulation.py
```

**Generate MATLAB analysis scripts:**
```bash
python matlab_demo.py
```

**Test specific components:**
```bash
python test_enhanced_traffic_model.py
python test_emergency_scenarios.py
python test_matlab_integration.py
```

## 🎮 Interactive Controls

### Camera Navigation
- **WASD**: Move camera (forward/back/left/right)
- **Q/E**: Move camera up/down
- **Mouse Wheel**: Zoom in/out
- **Right-Click + Drag**: Rotate camera view

### Simulation Control
- **Space**: Pause/Resume simulation
- **Speed Slider**: Adjust simulation speed (0.1x to 3.0x)
- **Accident Button**: Trigger emergency accident scenario
- **Flooding Button**: Simulate monsoon flooding

## 🏗️ Architecture Overview

```
indian-traffic-digital-twin/
├── 🎯 Core Simulation
│   ├── full_traffic_simulation.py    # Main 3D simulation engine
│   ├── traffic_model.py              # Core traffic flow model
│   └── main.py                       # Basic 2D visualization
│
├── 🇮🇳 Indian Features
│   ├── behavior_model.py             # Indian driving behaviors
│   ├── mixed_traffic_manager.py      # Multi-vehicle type handling
│   ├── vehicle_factory.py            # Indian vehicle creation
│   ├── emergency_scenarios.py        # Accident & flooding simulation
│   ├── weather_conditions.py         # Monsoon & seasonal effects
│   └── scenario_templates.py         # Pre-built Indian scenarios
│
├── 🎨 Enhanced Visualization
│   ├── traffic_flow_visualizer.py    # Advanced 3D rendering
│   ├── camera_controller.py          # Interactive camera system
│   ├── ui_overlay.py                 # Real-time statistics display
│   └── vehicle_asset_manager.py      # 3D model management
│
├── 🔬 MATLAB Integration
│   ├── matlab_data_exporter.py       # Export simulation data
│   ├── script_generator.py           # Auto-generate analysis scripts
│   ├── simulink_connector.py         # Real-time data streaming
│   └── roadrunner_importer.py        # Import professional scenes
│
└── 📊 Analysis & Testing
    ├── test_*.py                     # Comprehensive test suite
    └── logs/                         # Simulation logs & metrics
```

## 🌍 Scenario Library

### Mumbai Busy Intersection
- **Vehicle Mix**: High auto-rickshaw density (20%)
- **Conditions**: Extended peak hours, monsoon patterns
- **Challenges**: Dense urban traffic, frequent lane changes

### Bangalore Tech Corridor  
- **Vehicle Mix**: Higher car usage (45%), organized bus services
- **Conditions**: Office timing patterns, IT corridor characteristics
- **Challenges**: Rush hour congestion, mixed development areas

### Delhi Roundabout
- **Vehicle Mix**: Heavy truck presence, diverse vehicle types
- **Conditions**: Dust storms, winter fog, major roundabout dynamics
- **Challenges**: Complex merging patterns, weather adaptations

## 📈 Performance & Scalability

- **Real-time Performance**: Maintains 30+ FPS with 1000+ vehicles
- **Memory Efficient**: Optimized data structures for large-scale simulations
- **Parallel Processing**: Multi-threaded vehicle behavior calculations
- **Adaptive Quality**: Dynamic LOD system for smooth performance

## 🔧 Customization

### Create Custom Vehicle Types
```python
from indian_features.vehicle_factory import IndianVehicleFactory
from indian_features.enums import VehicleType

# Define custom vehicle behavior
custom_config = VehicleConfig(
    length=3.5, width=1.6, height=1.4,
    max_speed=90, acceleration=2.5,
    lane_discipline_base=0.6,
    overtaking_aggressiveness=0.7
)
```

### Design Custom Scenarios
```python
from indian_features.scenario_templates import ScenarioTemplate

# Create scenario for specific Indian city
custom_scenario = ScenarioTemplate(
    template_id="hyderabad_hitec_city",
    name="Hyderabad HITEC City",
    vehicle_mix_ratios={
        VehicleType.CAR: 0.5,
        VehicleType.MOTORCYCLE: 0.25,
        VehicleType.AUTO_RICKSHAW: 0.15,
        VehicleType.BUS: 0.1
    }
)
```

## 📊 MATLAB Integration Highlights

### Automated Analysis Scripts
The system generates comprehensive MATLAB scripts for:
- **Traffic Flow Analysis**: Speed-density relationships, capacity calculations
- **Congestion Studies**: Bottleneck identification, queue length analysis  
- **Safety Metrics**: Conflict analysis, near-miss detection
- **Environmental Impact**: Emission calculations, fuel consumption

### RoadRunner Compatibility
- Import professional road scenes from RoadRunner
- Convert simulation data to RoadRunner format
- Seamless integration with Automated Driving Toolbox

### Simulink Real-time Streaming
- Live data feed for control system testing
- Traffic signal optimization experiments
- Autonomous vehicle algorithm validation

## 🧪 Testing & Validation

Comprehensive test suite covering:
- **Behavior Models**: Validation against real Indian traffic data
- **Emergency Scenarios**: Response time and rerouting effectiveness
- **Weather Effects**: Speed and behavior adaptations
- **MATLAB Integration**: Data export accuracy and script generation
- **System Robustness**: Performance under various load conditions

## 🤝 Contributing

We welcome contributions! Areas where you can help:

1. **New Vehicle Types**: Add electric vehicles, commercial variants
2. **Regional Scenarios**: Create templates for different Indian cities
3. **Behavior Refinement**: Improve driving behavior models with real data
4. **Visualization Enhancements**: Better 3D models, lighting, effects
5. **Analysis Tools**: New metrics, visualization methods

## 📚 Documentation

- **[Full Simulation Guide](FULL_SIMULATION_README.md)**: Detailed 3D simulation documentation
- **[MATLAB Integration Guide](MATLAB_INTEGRATION_GUIDE.md)**: Complete MATLAB workflow
- **[UI Overlay Guide](UI_OVERLAY_IMPLEMENTATION_SUMMARY.md)**: Interface customization
- **[Zoom Controls](ZOOM_CONTROLS_README.md)**: Camera control system

## 🎓 Research Applications

This platform is ideal for:
- **Urban Planning**: Test traffic management strategies
- **Policy Analysis**: Evaluate traffic rule changes
- **Infrastructure Design**: Optimize road layouts and signal timing
- **Autonomous Vehicle Research**: Test algorithms in Indian conditions
- **Environmental Studies**: Analyze emission patterns and reduction strategies

## 🏆 What Sets Us Apart

Unlike generic traffic simulators, this digital twin:
- **Captures Indian Chaos**: Models the beautiful complexity of Indian traffic
- **Validates with Reality**: Behavior patterns based on real Indian driving data
- **Scales Appropriately**: From narrow city lanes to wide highways
- **Integrates Professionally**: Works with industry-standard tools (MATLAB, RoadRunner)
- **Adapts Dynamically**: Weather, time, and emergency conditions affect everything

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenStreetMap contributors for road network data
- Panda3D community for 3D visualization framework
- Indian traffic research community for behavioral insights
- MATLAB and MathWorks for integration support

---

**Ready to dive into the fascinating world of Indian traffic simulation?** 

Start with `python full_traffic_simulation.py` and watch the magic unfold! 🚗💨