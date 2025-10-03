#!/usr/bin/env python3
"""
Demo script to run the full traffic simulation

This script demonstrates how to run the complete Indian traffic simulation
with 3D visualization, vehicles, roads, and interactive controls.
"""

from full_traffic_simulation import main
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":
    print("=" * 60)
    print("FULL INDIAN TRAFFIC SIMULATION DEMO")
    print("=" * 60)
    print()
    print("This simulation includes:")
    print("• 3D roads and intersections")
    print("• Moving vehicles (cars, buses, trucks, motorcycles, auto-rickshaws)")
    print("• Traffic lights with realistic cycling")
    print("• Indian traffic scenarios (Mumbai intersection by default)")
    print("• Interactive camera controls (WASD + Q/E)")
    print("• Emergency scenarios (accidents, flooding)")
    print("• Real-time statistics display")
    print()
    print("Controls:")
    print("• WASD: Move camera")
    print("• Q/E: Move camera up/down")
    print("• Mouse wheel: Zoom in/out")
    print("• Space: Pause/Resume simulation")
    print("• UI buttons: Trigger emergencies")
    print()
    print("Starting simulation...")
    print("=" * 60)

    # Run the main simulation
    main()
