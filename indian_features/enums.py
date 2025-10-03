"""
Enums for Indian Traffic Characteristics

This module defines enumerations for various Indian traffic-specific attributes
including vehicle types, road conditions, weather patterns, and emergency scenarios.
"""

from enum import Enum, auto


class VehicleType(Enum):
    """Indian vehicle types with specific behavioral characteristics"""
    CAR = auto()
    BUS = auto()
    AUTO_RICKSHAW = auto()
    MOTORCYCLE = auto()
    TRUCK = auto()
    BICYCLE = auto()
    PEDESTRIAN = auto()


class RoadQuality(Enum):
    """Road quality levels affecting vehicle behavior"""
    EXCELLENT = auto()
    GOOD = auto()
    POOR = auto()
    VERY_POOR = auto()


class SurfaceType(Enum):
    """Road surface types common in Indian roads"""
    ASPHALT = auto()
    CONCRETE = auto()
    GRAVEL = auto()
    DIRT = auto()
    COBBLESTONE = auto()


class MaintenanceLevel(Enum):
    """Road maintenance status"""
    WELL_MAINTAINED = auto()
    MODERATELY_MAINTAINED = auto()
    POORLY_MAINTAINED = auto()
    UNMAINTAINED = auto()


class ConstructionStatus(Enum):
    """Construction and work zone status"""
    NO_CONSTRUCTION = auto()
    MINOR_WORK = auto()
    MAJOR_CONSTRUCTION = auto()
    ROAD_CLOSURE = auto()


class WeatherType(Enum):
    """Weather conditions affecting traffic"""
    CLEAR = auto()
    LIGHT_RAIN = auto()
    HEAVY_RAIN = auto()
    FOG = auto()
    DUST_STORM = auto()


class EmergencyType(Enum):
    """Emergency scenarios for simulation"""
    ACCIDENT = auto()
    FLOODING = auto()
    ROAD_CLOSURE = auto()
    CONSTRUCTION = auto()
    VEHICLE_BREAKDOWN = auto()


class SeverityLevel(Enum):
    """Severity levels for emergencies and conditions"""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class BehaviorProfile(Enum):
    """Driver behavior profiles"""
    CONSERVATIVE = auto()
    NORMAL = auto()
    AGGRESSIVE = auto()
    ERRATIC = auto()


class IntersectionType(Enum):
    """Types of intersections common in Indian traffic"""
    SIGNALIZED = auto()
    ROUNDABOUT = auto()
    T_JUNCTION = auto()
    FOUR_WAY_STOP = auto()
    UNCONTROLLED = auto()


class LaneDiscipline(Enum):
    """Lane discipline levels"""
    STRICT = auto()
    MODERATE = auto()
    LOOSE = auto()
    CHAOTIC = auto()