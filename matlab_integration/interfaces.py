"""
Interfaces for MATLAB Integration Components

This module defines abstract interfaces for MATLAB/Simulink integration,
data export, and RoadRunner scene import functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import networkx as nx
from dataclasses import dataclass


@dataclass
class MATLABDataFormat:
    """Structure for MATLAB-compatible data"""
    variable_name: str
    data: Any
    data_type: str
    description: str


@dataclass
class RoadRunnerScene:
    """Structure for RoadRunner scene data"""
    scene_name: str
    road_network: Dict[str, Any]
    vehicle_paths: List[Dict[str, Any]]
    scenario_config: Dict[str, Any]
    metadata: Dict[str, Any]


class MATLABExporterInterface(ABC):
    """Interface for exporting simulation data to MATLAB formats"""
    
    @abstractmethod
    def export_vehicle_trajectories(self, trajectories: Dict[int, List[Dict[str, Any]]]) -> str:
        """Export vehicle trajectory data to .mat file format"""
        pass
    
    @abstractmethod
    def export_road_network(self, graph: nx.Graph) -> str:
        """Export road network data compatible with MATLAB"""
        pass
    
    @abstractmethod
    def export_traffic_metrics(self, metrics: Dict[str, Any]) -> str:
        """Export traffic analysis metrics"""
        pass
    
    @abstractmethod
    def generate_analysis_script(self, data_files: List[str], analysis_type: str) -> str:
        """Generate MATLAB analysis script for exported data"""
        pass
    
    @abstractmethod
    def create_matlab_workspace(self, simulation_results: Dict[str, Any]) -> Dict[str, MATLABDataFormat]:
        """Create MATLAB workspace variables from simulation results"""
        pass


class RoadRunnerImporterInterface(ABC):
    """Interface for importing RoadRunner scene files"""
    
    @abstractmethod
    def import_scene_file(self, filepath: str) -> RoadRunnerScene:
        """Import RoadRunner scene file"""
        pass
    
    @abstractmethod
    def convert_to_osmnx_graph(self, scene: RoadRunnerScene) -> nx.Graph:
        """Convert RoadRunner scene to OSMnx-compatible graph"""
        pass
    
    @abstractmethod
    def extract_vehicle_paths(self, scene: RoadRunnerScene) -> List[Dict[str, Any]]:
        """Extract predefined vehicle paths from scene"""
        pass
    
    @abstractmethod
    def parse_scenario_configuration(self, scene: RoadRunnerScene) -> Dict[str, Any]:
        """Parse scenario configuration from RoadRunner scene"""
        pass
    
    @abstractmethod
    def validate_scene_compatibility(self, scene: RoadRunnerScene) -> Tuple[bool, List[str]]:
        """Validate scene compatibility and return any issues"""
        pass


class SimulinkConnectorInterface(ABC):
    """Interface for real-time Simulink integration"""
    
    @abstractmethod
    def establish_connection(self, simulink_model: str) -> bool:
        """Establish connection with Simulink model"""
        pass
    
    @abstractmethod
    def send_real_time_data(self, data: Dict[str, Any]) -> bool:
        """Send real-time simulation data to Simulink"""
        pass
    
    @abstractmethod
    def receive_control_signals(self) -> Dict[str, Any]:
        """Receive control signals from Simulink model"""
        pass
    
    @abstractmethod
    def synchronize_simulation_time(self, simulation_time: float) -> None:
        """Synchronize simulation time with Simulink"""
        pass
    
    @abstractmethod
    def close_connection(self) -> None:
        """Close connection with Simulink model"""
        pass


class AutomatedDrivingToolboxInterface(ABC):
    """Interface for MATLAB Automated Driving Toolbox integration"""
    
    @abstractmethod
    def export_driving_scenario(self, scenario_data: Dict[str, Any]) -> str:
        """Export scenario compatible with Automated Driving Toolbox"""
        pass
    
    @abstractmethod
    def create_actor_definitions(self, vehicles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create actor definitions for MATLAB driving scenario"""
        pass
    
    @abstractmethod
    def generate_waypoint_data(self, vehicle_paths: Dict[int, List[Tuple[float, float]]]) -> Dict[str, Any]:
        """Generate waypoint data for vehicle trajectories"""
        pass
    
    @abstractmethod
    def export_sensor_configuration(self, sensor_config: Dict[str, Any]) -> str:
        """Export sensor configuration for autonomous vehicle testing"""
        pass