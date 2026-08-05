#!/usr/bin/env python3
"""
Optimus-class sensors.
Ears are wrapped so every real-echo acquisition restarts the virtual sound card.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

# Skill (read-only)
SKILL_ROOT = Path("/home/workdir/.grok/skills/axb-predictive-echo")
sys.path.insert(0, str(SKILL_ROOT))
from scripts.axb_robot import Ears as SkillEars

# Virtual sound card from the sim layer
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sim"))
from virtual_sound_card import VirtualSoundCard


class OptimusEars(SkillEars):
    """
    Optimus ears.
    On every listen() → restart virtual sound card, then call skill Ears.
    """

    def __init__(self, sound_card: VirtualSoundCard, hardware: bool = False):
        super().__init__(hardware=hardware)
        self.sound = sound_card
        self.last_wav: Optional[Path] = None

    def listen(self, pose: np.ndarray, true_obstacles: List[np.ndarray]) -> List[Dict]:
        self.last_wav = self.sound.restart()
        return super().listen(pose, true_obstacles)


class IMU:
    """Simple inertial state for Optimus body reporting."""

    def __init__(self):
        self.orientation = np.array([1.0, 0.0, 0.0, 0.0])  # quaternion wxyz
        self.angular_rate = np.zeros(3)
        self.linear_accel = np.array([0.0, 0.0, 9.81])

    def update(self, pose: np.ndarray, velocity: np.ndarray):
        # Minimal model — enough for telemetry
        heading = np.arctan2(pose[1], pose[0] + 1e-9)
        self.orientation = np.array([np.cos(heading / 2), 0.0, 0.0, np.sin(heading / 2)])
        self.linear_accel = np.array([velocity[0] * 0.1, velocity[1] * 0.1, 9.81])

    def as_dict(self) -> Dict[str, Any]:
        return {
            "orientation_wxyz": self.orientation.tolist(),
            "angular_rate": self.angular_rate.tolist(),
            "linear_accel": self.linear_accel.tolist(),
        }


class GroundScan:
    """Ground-plane scan consumer (variables only — no obstacle geometry to robot)."""

    def __init__(self):
        self.last = {}

    def update(self, station_vars: Dict, pose: np.ndarray) -> Dict:
        goal = np.asarray(station_vars["goal"])
        heading = goal - pose
        dist = float(np.linalg.norm(heading))
        self.last = {
            "clear_ahead": station_vars.get("ground_ok", True),
            "goal_dir": (heading / max(dist, 1e-9)).tolist(),
            "goal_dist": dist,
        }
        return self.last
