"""
UIOverlay Implementation

This module implements the UIOverlayInterface for user interface overlays
and simulation controls, including play/pause controls, information panels,
vehicle details, and scenario selection interfaces.
"""

import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    from panda3d.core import (
        NodePath, CardMaker, TextNode, Vec3, Vec4, Point3,
        TransparencyAttrib, BillboardEffect, TextureStage,
        PGButton, PGSliderBar, PGEntry, PGFrameStyle,
        MouseButton, KeyboardButton
    )
    from direct.gui.DirectGui import (
        DirectFrame, DirectButton, DirectLabel, DirectSlider,
        DirectEntry, DirectCheckButton, DirectOptionMenu,
        DirectScrolledList, DirectDialog
    )
    from direct.showbase.DirectObject import DirectObject
    PANDA3D_AVAILABLE = True
except ImportError:
    PANDA3D_AVAILABLE = False
    # Mock classes for development without Panda3D
    class DirectObject:
        def accept(self, *args): pass
        def ignore(self, *args): pass

    class DirectFrame:
        def __init__(self, **kwargs): pass
        def destroy(self): pass
        def show(self): pass
        def hide(self): pass

    DirectButton = DirectLabel = DirectSlider = DirectEntry = DirectFrame
    DirectCheckButton = DirectOptionMenu = DirectScrolledList = DirectDialog = DirectFrame

try:
    # Try relative imports first (when used as package)
    from .interfaces import UIOverlayInterface
    from .config import VisualizationConfig, UIConfig
except ImportError:
    # Fall back to absolute imports (when run directly)
    from enhanced_visualization.interfaces import UIOverlayInterface
    from enhanced_visualization.config import VisualizationConfig, UIConfig
from indian_features.enums import WeatherType, EmergencyType, VehicleType


class SimulationState(Enum):
    """Simulation control states"""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    STEP = "step"


@dataclass
class UIPanel:
    """Represents a UI panel"""
    panel_id: str
    title: str
    position: Tuple[float, float]
    size: Tuple[float, float]
    visible: bool = True
    collapsible: bool = True
    collapsed: bool = False
    frame: Optional[Any] = None
    elements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationControls:
    """Simulation control state"""
    state: SimulationState = SimulationState.STOPPED
    speed_multiplier: float = 1.0
    step_size: float = 0.1
    auto_step: bool = False


class UIOverlay(UIOverlayInterface, DirectObject if PANDA3D_AVAILABLE else object):
    """
    User interface overlay system for simulation controls.

    This class provides comprehensive UI elements including simulation controls,
    information panels, vehicle details, scenario selection, and weather controls
    for enhanced interaction with the Indian traffic simulation.
    """

    def __init__(self, config: VisualizationConfig, aspect2d: Optional[NodePath] = None):
        """
        Initialize the UI overlay system.

        Args:
            config: Visualization configuration
            aspect2d: Panda3D aspect2d node for UI rendering (optional, for testing)
        """
        if PANDA3D_AVAILABLE:
            DirectObject.__init__(self)

        self.config = config
        self.ui_config = config.ui_config

        # UI root node
        if PANDA3D_AVAILABLE and aspect2d is not None:
            self.aspect2d = aspect2d
        else:
            self.aspect2d = None

        # UI panels management
        self.panels: Dict[str, UIPanel] = {}
        self.active_panels: List[str] = []

        # Simulation controls
        self.simulation_controls = SimulationControls()
        self.control_callbacks: Dict[str, Callable] = {}

        # Information displays
        self.info_panels: Dict[str, Dict[str, Any]] = {}
        self.vehicle_details: Dict[int, Dict[str, Any]] = {}

        # UI elements
        self.ui_elements: Dict[str, Any] = {}
        self.dialogs: Dict[str, Any] = {}

        # Event handling
        self.mouse_watcher = None
        self.selected_vehicle_id: Optional[int] = None
        self.hovered_element: Optional[str] = None

        # Performance tracking
        self.fps_counter = None
        self.stats_display = None

        # Initialize UI system
        self._initialize_ui_system()
        self._setup_event_handling()

    def create_simulation_controls(self) -> None:
        """Create simulation control UI (play, pause, speed, etc.)."""
        if not PANDA3D_AVAILABLE:
            print("Creating simulation controls (mock)")
            return

        # Create main control panel
        control_panel = self._create_panel(
            "simulation_controls",
            "Simulation Controls",
            (-0.95, 0.95),
            (0.3, 0.2)
        )

        if not control_panel:
            return

        # Play/Pause button
        play_button = DirectButton(
            parent=control_panel.frame,
            text="Play",
            scale=0.05,
            pos=(0.05, 0, 0.12),
            command=self._on_play_pause_clicked
        )
        control_panel.elements["play_button"] = play_button

        # Stop button
        stop_button = DirectButton(
            parent=control_panel.frame,
            text="Stop",
            scale=0.05,
            pos=(0.15, 0, 0.12),
            command=self._on_stop_clicked
        )
        control_panel.elements["stop_button"] = stop_button

        # Step button
        step_button = DirectButton(
            parent=control_panel.frame,
            text="Step",
            scale=0.05,
            pos=(0.25, 0, 0.12),
            command=self._on_step_clicked
        )
        control_panel.elements["step_button"] = step_button

        # Speed slider
        speed_label = DirectLabel(
            parent=control_panel.frame,
            text="Speed:",
            scale=0.04,
            pos=(0.05, 0, 0.06)
        )
        control_panel.elements["speed_label"] = speed_label

        speed_slider = DirectSlider(
            parent=control_panel.frame,
            range=(0.1, 5.0),
            value=1.0,
            scale=0.15,
            pos=(0.15, 0, 0.06),
            command=self._on_speed_changed
        )
        control_panel.elements["speed_slider"] = speed_slider

        # Speed display
        speed_display = DirectLabel(
            parent=control_panel.frame,
            text="1.0x",
            scale=0.04,
            pos=(0.25, 0, 0.06)
        )
        control_panel.elements["speed_display"] = speed_display

        print("Created simulation controls")

    def add_information_panel(self, panel_data: Dict[str, Any]) -> None:
        """
        Add information panel with simulation statistics.

        Args:
            panel_data: Panel configuration and data
        """
        panel_id = panel_data.get("id", "info_panel")
        title = panel_data.get("title", "Information")

        if not PANDA3D_AVAILABLE:
            print(f"Adding information panel '{title}' (mock)")
            return

        # Create info panel
        info_panel = self._create_panel(
            panel_id,
            title,
            (0.65, 0.95),
            (0.3, 0.4)
        )

        if not info_panel:
            return

        # Add statistics display
        stats_text = self._format_statistics(panel_data.get("stats", {}))

        stats_label = DirectLabel(
            parent=info_panel.frame,
            text=stats_text,
            scale=0.035,
            pos=(0.05, 0, 0.3),
            text_align=TextNode.ALeft if PANDA3D_AVAILABLE else None
        )
        info_panel.elements["stats_label"] = stats_label

        # Store panel data
        self.info_panels[panel_id] = panel_data

        print(f"Added information panel: {title}")

    def show_vehicle_details(self, vehicle_id: int, details: Dict[str, Any]) -> None:
        """
        Show detailed information about a selected vehicle.

        Args:
            vehicle_id: ID of the vehicle
            details: Vehicle details dictionary
        """
        if not PANDA3D_AVAILABLE:
            print(f"Showing details for vehicle {vehicle_id} (mock)")
            return

        # Create or update vehicle details panel
        panel_id = "vehicle_details"

        if panel_id in self.panels:
            # Update existing panel
            self._update_vehicle_details_panel(vehicle_id, details)
        else:
            # Create new panel
            self._create_vehicle_details_panel(vehicle_id, details)

        self.selected_vehicle_id = vehicle_id
        self.vehicle_details[vehicle_id] = details

        print(f"Showing details for vehicle {vehicle_id}")

    def display_road_conditions(self, segment_id: str, conditions: Dict[str, Any]) -> None:
        """
        Display road condition information for a segment.

        Args:
            segment_id: ID of the road segment
            conditions: Road condition data
        """
        if not PANDA3D_AVAILABLE:
            print(f"Displaying road conditions for segment {segment_id} (mock)")
            return

        # Create temporary tooltip or popup
        self._show_road_conditions_tooltip(segment_id, conditions)

        print(f"Displayed road conditions for segment {segment_id}")

    def create_scenario_selector(self, scenarios: List[str]) -> None:
        """
        Create UI for selecting simulation scenarios.

        Args:
            scenarios: List of available scenario names
        """
        if not PANDA3D_AVAILABLE:
            print(f"Creating scenario selector with {len(scenarios)} scenarios (mock)")
            return

        # Create scenario selection panel
        scenario_panel = self._create_panel(
            "scenario_selector",
            "Scenario Selection",
            (-0.95, 0.7),
            (0.3, 0.2)
        )

        if not scenario_panel:
            return

        # Scenario dropdown
        scenario_label = DirectLabel(
            parent=scenario_panel.frame,
            text="Scenario:",
            scale=0.04,
            pos=(0.05, 0, 0.12)
        )
        scenario_panel.elements["scenario_label"] = scenario_label

        scenario_menu = DirectOptionMenu(
            parent=scenario_panel.frame,
            text="Select Scenario",
            scale=0.04,
            pos=(0.05, 0, 0.08),
            items=scenarios,
            command=self._on_scenario_selected
        )
        scenario_panel.elements["scenario_menu"] = scenario_menu

        # Load scenario button
        load_button = DirectButton(
            parent=scenario_panel.frame,
            text="Load",
            scale=0.04,
            pos=(0.2, 0, 0.08),
            command=self._on_load_scenario_clicked
        )
        scenario_panel.elements["load_button"] = load_button

        print(f"Created scenario selector with {len(scenarios)} scenarios")

    def add_weather_controls(self, weather_options: List[WeatherType]) -> None:
        """
        Add weather control interface.

        Args:
            weather_options: List of available weather types
        """
        if not PANDA3D_AVAILABLE:
            print(f"Adding weather controls with {len(weather_options)} options (mock)")
            return

        # Create weather control panel
        weather_panel = self._create_panel(
            "weather_controls",
            "Weather Controls",
            (-0.95, 0.45),
            (0.3, 0.2)
        )

        if not weather_panel:
            return

        # Weather type selector
        weather_label = DirectLabel(
            parent=weather_panel.frame,
            text="Weather:",
            scale=0.04,
            pos=(0.05, 0, 0.12)
        )
        weather_panel.elements["weather_label"] = weather_label

        weather_options_str = [w.name if hasattr(w, 'name') else str(w) for w in weather_options]

        weather_menu = DirectOptionMenu(
            parent=weather_panel.frame,
            text="Clear",
            scale=0.04,
            pos=(0.05, 0, 0.08),
            items=weather_options_str,
            command=self._on_weather_changed
        )
        weather_panel.elements["weather_menu"] = weather_menu

        # Weather intensity slider
        intensity_label = DirectLabel(
            parent=weather_panel.frame,
            text="Intensity:",
            scale=0.04,
            pos=(0.05, 0, 0.04)
        )
        weather_panel.elements["intensity_label"] = intensity_label

        intensity_slider = DirectSlider(
            parent=weather_panel.frame,
            range=(0.0, 1.0),
            value=0.5,
            scale=0.1,
            pos=(0.15, 0, 0.04),
            command=self._on_weather_intensity_changed
        )
        weather_panel.elements["intensity_slider"] = intensity_slider

        print(f"Added weather controls with {len(weather_options)} options")

    def show_emergency_controls(self, emergency_types: List[EmergencyType]) -> None:
        """
        Show controls for triggering emergency scenarios.

        Args:
            emergency_types: List of available emergency types
        """
        if not PANDA3D_AVAILABLE:
            print(f"Showing emergency controls with {len(emergency_types)} types (mock)")
            return

        # Create emergency control panel
        emergency_panel = self._create_panel(
            "emergency_controls",
            "Emergency Controls",
            (-0.95, 0.2),
            (0.3, 0.25)
        )

        if not emergency_panel:
            return

        # Emergency type buttons
        y_pos = 0.15
        for i, emergency_type in enumerate(emergency_types):
            type_name = emergency_type.name if hasattr(emergency_type, 'name') else str(emergency_type)

            emergency_button = DirectButton(
                parent=emergency_panel.frame,
                text=type_name.title(),
                scale=0.035,
                pos=(0.05, 0, y_pos),
                command=self._on_emergency_triggered,
                extraArgs=[emergency_type]
            )
            emergency_panel.elements[f"emergency_{type_name}"] = emergency_button

            y_pos -= 0.04

        print(f"Created emergency controls with {len(emergency_types)} types")

    def update_fps_counter(self, fps: float) -> None:
        """Update FPS counter display."""
        if not self.ui_config.show_fps_counter:
            return

        if not PANDA3D_AVAILABLE:
            return

        if not self.fps_counter:
            self.fps_counter = DirectLabel(
                text=f"FPS: {fps:.1f}",
                scale=0.05,
                pos=(0.8, 0, 0.9),
                text_fg=(1, 1, 1, 1)
            )
        else:
            self.fps_counter['text'] = f"FPS: {fps:.1f}"

    def update_simulation_stats(self, stats: Dict[str, Any]) -> None:
        """Update simulation statistics display."""
        if "simulation_controls" in self.panels:
            panel = self.panels["simulation_controls"]

            # Update any stats displays in the control panel
            # Implementation would update specific stat elements

    def _initialize_ui_system(self) -> None:
        """Initialize the UI system."""
        if not PANDA3D_AVAILABLE:
            return

        # Initialize FPS counter if enabled
        if self.ui_config.show_fps_counter:
            self.fps_counter = DirectLabel(
                text="FPS: --",
                scale=0.05,
                pos=(0.8, 0, 0.9),
                text_fg=(1, 1, 1, 1)
            )

    def _setup_event_handling(self) -> None:
        """Setup UI event handling."""
        if not PANDA3D_AVAILABLE:
            return

        # Mouse events
        self.accept("mouse1", self._on_mouse_click)
        self.accept("mouse3", self._on_right_click)

        # Keyboard shortcuts
        self.accept("space", self._on_play_pause_clicked)
        self.accept("escape", self._on_escape_pressed)

        # UI toggle keys
        self.accept("tab", self._toggle_ui_visibility)
        self.accept("f12", self._toggle_debug_info)

    def _create_panel(self, panel_id: str, title: str, position: Tuple[float, float],
                     size: Tuple[float, float]) -> Optional[UIPanel]:
        """Create a UI panel."""
        if not PANDA3D_AVAILABLE:
            return None

        # Create frame
        frame = DirectFrame(
            frameSize=(0, size[0], 0, size[1]),
            pos=(position[0], 0, position[1]),
            frameColor=(0.2, 0.2, 0.2, 0.8)
        )

        # Add title bar
        title_label = DirectLabel(
            parent=frame,
            text=title,
            scale=0.04,
            pos=(0.02, 0, size[1] - 0.03),
            text_fg=(1, 1, 1, 1)
        )

        # Create panel object
        panel = UIPanel(
            panel_id=panel_id,
            title=title,
            position=position,
            size=size,
            frame=frame
        )

        panel.elements["title"] = title_label
        self.panels[panel_id] = panel
        self.active_panels.append(panel_id)

        return panel

    def _create_vehicle_details_panel(self, vehicle_id: int, details: Dict[str, Any]) -> None:
        """Create vehicle details panel."""
        panel = self._create_panel(
            "vehicle_details",
            f"Vehicle {vehicle_id}",
            (0.65, 0.5),
            (0.3, 0.3)
        )

        if not panel:
            return

        self._update_vehicle_details_panel(vehicle_id, details)

    def _update_vehicle_details_panel(self, vehicle_id: int, details: Dict[str, Any]) -> None:
        """Update vehicle details panel content."""
        if "vehicle_details" not in self.panels:
            return

        panel = self.panels["vehicle_details"]

        # Clear existing detail elements
        for key in list(panel.elements.keys()):
            if key.startswith("detail_"):
                panel.elements[key].destroy()
                del panel.elements[key]

        # Add vehicle details
        y_pos = 0.25
        for key, value in details.items():
            detail_text = f"{key}: {value}"

            detail_label = DirectLabel(
                parent=panel.frame,
                text=detail_text,
                scale=0.03,
                pos=(0.02, 0, y_pos),
                text_align=TextNode.ALeft if PANDA3D_AVAILABLE else None
            )

            panel.elements[f"detail_{key}"] = detail_label
            y_pos -= 0.04

    def _show_road_conditions_tooltip(self, segment_id: str, conditions: Dict[str, Any]) -> None:
        """Show road conditions tooltip."""
        # Create temporary tooltip
        # Implementation would show tooltip near mouse cursor
        pass

    def _format_statistics(self, stats: Dict[str, Any]) -> str:
        """Format statistics for display."""
        lines = []
        for key, value in stats.items():
            if isinstance(value, float):
                lines.append(f"{key}: {value:.2f}")
            else:
                lines.append(f"{key}: {value}")

        return "\n".join(lines)

    # Event handlers
    def _on_play_pause_clicked(self) -> None:
        """Handle play/pause button click."""
        if self.simulation_controls.state == SimulationState.PLAYING:
            self.simulation_controls.state = SimulationState.PAUSED
            self._update_play_button_text("Play")
        else:
            self.simulation_controls.state = SimulationState.PLAYING
            self._update_play_button_text("Pause")

        # Call callback if registered
        if "play_pause" in self.control_callbacks:
            self.control_callbacks["play_pause"](self.simulation_controls.state)

        print(f"Simulation state: {self.simulation_controls.state}")

    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        self.simulation_controls.state = SimulationState.STOPPED
        self._update_play_button_text("Play")

        if "stop" in self.control_callbacks:
            self.control_callbacks["stop"]()

        print("Simulation stopped")

    def _on_step_clicked(self) -> None:
        """Handle step button click."""
        self.simulation_controls.state = SimulationState.STEP

        if "step" in self.control_callbacks:
            self.control_callbacks["step"](self.simulation_controls.step_size)

        print("Simulation step")

    def _on_speed_changed(self) -> None:
        """Handle speed slider change."""
        if "simulation_controls" not in self.panels:
            return

        panel = self.panels["simulation_controls"]
        if "speed_slider" not in panel.elements:
            return

        speed = panel.elements["speed_slider"]["value"]
        self.simulation_controls.speed_multiplier = speed

        # Update speed display
        if "speed_display" in panel.elements:
            panel.elements["speed_display"]["text"] = f"{speed:.1f}x"

        if "speed_change" in self.control_callbacks:
            self.control_callbacks["speed_change"](speed)

        print(f"Simulation speed: {speed:.1f}x")

    def _on_scenario_selected(self, scenario_name: str) -> None:
        """Handle scenario selection."""
        print(f"Selected scenario: {scenario_name}")

    def _on_load_scenario_clicked(self) -> None:
        """Handle load scenario button click."""
        if "load_scenario" in self.control_callbacks:
            # Get selected scenario from menu
            # Implementation would get actual selection
            self.control_callbacks["load_scenario"]("default_scenario")

        print("Loading scenario")

    def _on_weather_changed(self, weather_type: str) -> None:
        """Handle weather type change."""
        if "weather_change" in self.control_callbacks:
            self.control_callbacks["weather_change"](weather_type)

        print(f"Weather changed to: {weather_type}")

    def _on_weather_intensity_changed(self) -> None:
        """Handle weather intensity change."""
        if "weather_controls" not in self.panels:
            return

        panel = self.panels["weather_controls"]
        if "intensity_slider" not in panel.elements:
            return

        intensity = panel.elements["intensity_slider"]["value"]

        if "weather_intensity_change" in self.control_callbacks:
            self.control_callbacks["weather_intensity_change"](intensity)

        print(f"Weather intensity: {intensity:.2f}")

    def _on_emergency_triggered(self, emergency_type: EmergencyType) -> None:
        """Handle emergency scenario trigger."""
        if "emergency_trigger" in self.control_callbacks:
            self.control_callbacks["emergency_trigger"](emergency_type)

        print(f"Triggered emergency: {emergency_type}")

    def _on_mouse_click(self) -> None:
        """Handle mouse click."""
        # Implementation would handle object selection
        pass

    def _on_right_click(self) -> None:
        """Handle right mouse click."""
        # Implementation would show context menu
        pass

    def _on_escape_pressed(self) -> None:
        """Handle escape key press."""
        # Close dialogs or return to main view
        pass

    def _toggle_ui_visibility(self) -> None:
        """Toggle UI visibility."""
        for panel in self.panels.values():
            if panel.visible:
                panel.frame.hide()
                panel.visible = False
            else:
                panel.frame.show()
                panel.visible = True

    def _toggle_debug_info(self) -> None:
        """Toggle debug information display."""
        # Implementation would toggle debug overlays
        pass

    def _update_play_button_text(self, text: str) -> None:
        """Update play button text."""
        if "simulation_controls" not in self.panels:
            return

        panel = self.panels["simulation_controls"]
        if "play_button" in panel.elements:
            panel.elements["play_button"]["text"] = text

    def register_callback(self, event_name: str, callback: Callable) -> None:
        """Register callback for UI events."""
        self.control_callbacks[event_name] = callback
        print(f"Registered callback for: {event_name}")

    def cleanup(self) -> None:
        """Cleanup UI resources."""
        if PANDA3D_AVAILABLE:
            self.ignoreAll()

        # Destroy all panels
        for panel in self.panels.values():
            if panel.frame:
                panel.frame.destroy()

        # Destroy other UI elements
        if self.fps_counter:
            self.fps_counter.destroy()

        for dialog in self.dialogs.values():
            if dialog:
                dialog.destroy()

        print("UI overlay cleaned up")