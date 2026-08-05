#!/usr/bin/env python3
"""
Mission layer for Optimus-class.
Simple sequential goals that the predictive-echo controller drives toward.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np


@dataclass
class Waypoint:
    position: np.ndarray
    label: str = ""
    tolerance: float = 0.35

    def reached(self, pose: np.ndarray) -> bool:
        return float(np.linalg.norm(np.asarray(self.position) - pose)) <= self.tolerance


@dataclass
class Mission:
    name: str
    waypoints: List[Waypoint] = field(default_factory=list)
    current_idx: int = 0
    complete: bool = False

    def current_goal(self) -> Optional[np.ndarray]:
        if self.complete or self.current_idx >= len(self.waypoints):
            return None
        return self.waypoints[self.current_idx].position

    def advance_if_reached(self, pose: np.ndarray) -> bool:
        if self.complete or not self.waypoints:
            return False
        wp = self.waypoints[self.current_idx]
        if wp.reached(pose):
            print(f"[Mission] reached waypoint {self.current_idx}: {wp.label or wp.position}")
            self.current_idx += 1
            if self.current_idx >= len(self.waypoints):
                self.complete = True
                print(f"[Mission] COMPLETE — {self.name}")
            return True
        return False

    def status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "current_idx": self.current_idx,
            "total": len(self.waypoints),
            "complete": self.complete,
            "current_label": (
                self.waypoints[self.current_idx].label
                if not self.complete and self.current_idx < len(self.waypoints)
                else None
            ),
        }


def default_patrol() -> Mission:
    """Simple 4-point patrol used by the Optimus demo."""
    return Mission(
        name="perimeter_patrol",
        waypoints=[
            Waypoint(np.array([2.0, 0.0]), "alpha"),
            Waypoint(np.array([3.5, 1.2]), "bravo"),
            Waypoint(np.array([2.5, -1.0]), "charlie"),
            Waypoint(np.array([0.5, 0.0]), "home"),
        ],
    )
