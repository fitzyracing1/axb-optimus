#!/usr/bin/env python3
"""
Optimus-class body & locomotion state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class JointState:
    """Simplified joint set for an Optimus-class biped."""
    hip_yaw: float = 0.0
    hip_pitch: float = 0.0
    knee: float = 0.0
    ankle: float = 0.0

    def as_dict(self) -> Dict[str, float]:
        return {
            "hip_yaw": self.hip_yaw,
            "hip_pitch": self.hip_pitch,
            "knee": self.knee,
            "ankle": self.ankle,
        }


@dataclass
class BodyState:
    pose: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0]))
    velocity: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0]))
    left_leg: JointState = field(default_factory=JointState)
    right_leg: JointState = field(default_factory=JointState)
    torso_height: float = 1.65  # meters
    battery_pct: float = 100.0
    thermal: float = 32.0       # °C

    def step_kinematics(self, delta: np.ndarray, dt: float = 0.2):
        """Very lightweight forward kinematics + simple gait approximation."""
        self.velocity = delta / max(dt, 1e-6)
        self.pose = self.pose + delta

        # Approximate leg swing for visual / telemetry interest
        stride = float(np.linalg.norm(delta))
        phase = (self.pose[0] * 3.0) % (2 * np.pi)
        self.left_leg.hip_pitch = 0.25 * np.sin(phase)
        self.right_leg.hip_pitch = 0.25 * np.sin(phase + np.pi)
        self.left_leg.knee = 0.4 * abs(np.sin(phase))
        self.right_leg.knee = 0.4 * abs(np.sin(phase + np.pi))
        self.left_leg.ankle = -0.15 * np.sin(phase)
        self.right_leg.ankle = -0.15 * np.sin(phase + np.pi)

        # Power draw
        self.battery_pct = max(0.0, self.battery_pct - 0.08 * stride - 0.01)
        self.thermal = min(65.0, self.thermal + 0.05 * stride)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "pose": self.pose.tolist(),
            "velocity": self.velocity.tolist(),
            "left_leg": self.left_leg.as_dict(),
            "right_leg": self.right_leg.as_dict(),
            "torso_height_m": self.torso_height,
            "battery_pct": round(self.battery_pct, 2),
            "thermal_c": round(self.thermal, 1),
        }
