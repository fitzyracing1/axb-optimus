#!/usr/bin/env python3
"""
OptimusClass — full Optimus-class humanoid
Built around the axb-predictive-echo skill (skill never modified).

Core rule owned by this layer:
  Every time the cycle hits echo → restart the virtual sound card.
"""

from __future__ import annotations

import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import urllib.request

# ---------------------------------------------------------------------------
# Skill (read-only)
# ---------------------------------------------------------------------------
SKILL_ROOT = Path("/home/workdir/.grok/skills/axb-predictive-echo")
sys.path.insert(0, str(SKILL_ROOT))
from scripts.axb_robot import AxbRobot as SkillAxbRobot, GroundStation

# ---------------------------------------------------------------------------
# Local layers
# ---------------------------------------------------------------------------
from .body import BodyState
from .sensors import OptimusEars, IMU, GroundScan
from .telemetry import Telemetry
from .mission import Mission, default_patrol

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sim"))
from virtual_sound_card import VirtualSoundCard


def probe_internet(timeout: float = 3.0) -> Dict[str, Any]:
    url = "https://httpbin.org/get?robot=OptimusClass"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            return {"ok": True, "origin": data.get("origin"), "status": resp.status}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class OptimusClass:
    """
    Full Optimus-class humanoid.

    Architecture:
      - Predictive-echo control (skill library)
      - Virtual sound card restarted on every echo hit
      - Body + joint state
      - IMU + ground scan
      - Mission / waypoint layer
      - Telemetry log + internet proof
    """

    def __init__(
        self,
        name: str = "Optimus-01",
        goal: Optional[List[float]] = None,
        mission: Optional[Mission] = None,
    ):
        self.name = name
        self.station = GroundStation(goal=goal or [4.0, 0.0])
        self.sound = VirtualSoundCard(
            out_dir=Path("/home/workdir/artifacts/axb-robot/optimus/audio")
        )
        self.body = BodyState()
        self.imu = IMU()
        self.ground = GroundScan()
        self.telemetry = Telemetry()
        self.mission = mission or default_patrol()

        # Skill robot — we replace its ears with OptimusEars
        self._skill = SkillAxbRobot(self.station, name=name)
        self._skill.ears = OptimusEars(self.sound)

        # Keep body pose in sync with skill pose
        self._skill._pose = self.body.pose.copy()

        self.cycle = 0
        self.internet_ok_count = 0

    # ------------------------------------------------------------------ API
    def restart(self, reset_mission: bool = True, reset_body: bool = True) -> Dict[str, Any]:
        """
        Full Optimus restart.
        Always restarts the sound card first, then resets robot state.

        Args:
            reset_mission: if True, mission index returns to waypoint 0
            reset_body:    if True, pose/joints/battery/thermal return to defaults
        """
        print(f"\n[Optimus] RESTART — {self.name}")

        # 1. Always restart the sound card
        wav = self.sound.restart()

        # 2. Reset body state
        if reset_body:
            self.body = BodyState()
            self.imu = IMU()
            self._skill._pose = self.body.pose.copy()

        # 3. Reset mission progress
        if reset_mission:
            self.mission.current_idx = 0
            self.mission.complete = False

        # 4. Reset counters and start a fresh telemetry session
        self.cycle = 0
        self.internet_ok_count = 0
        self.telemetry = Telemetry()

        # 5. Re-bind ears so they still point at the same (now restarted) sound card
        self._skill.ears = OptimusEars(self.sound)

        result = {
            "action": "restart",
            "name": self.name,
            "sound_hits": self.sound.hits,
            "wav": str(wav),
            "body_reset": reset_body,
            "mission_reset": reset_mission,
            "pose": self.body.pose.tolist(),
            "mission": self.mission.status(),
        }
        print(f"[Optimus] sound card restarted → {Path(wav).name}")
        print(f"[Optimus] body reset={reset_body}  mission reset={reset_mission}")
        return result

    def step(self) -> Dict[str, Any]:
        """One full Optimus cycle."""
        self.cycle += 1
        t0 = time.time()

        # 0. Update mission goal into ground station
        goal = self.mission.current_goal()
        if goal is not None:
            self.station.vars["goal"] = np.asarray(goal, dtype=float)

        # 1. Internet proof
        net = probe_internet()
        if net["ok"]:
            self.internet_ok_count += 1

        # 2. Ground scan (variables only)
        scan = self.ground.update(self.station.pull(), self.body.pose)

        # 3. Predictive-echo cycle (skill) — ears will restart sound card
        pose_before = self.body.pose.copy()
        status = self._skill.step()
        pose_after = np.asarray(status.pose) if hasattr(status, "pose") else self._skill._pose
        delta = pose_after - pose_before
        self.body.step_kinematics(delta)
        self.imu.update(self.body.pose, self.body.velocity)

        # 4. Mission progress
        self.mission.advance_if_reached(self.body.pose)

        # 5. Telemetry frame
        frame = {
            "cycle": self.cycle,
            "name": self.name,
            "status_msg": getattr(status, "status_msg", str(status)),
            "last_d": getattr(status, "last_d", None),
            "last_surprise": getattr(status, "last_surprise", None),
            "last_heard_range": getattr(status, "last_heard_range", None),
            "body": self.body.as_dict(),
            "imu": self.imu.as_dict(),
            "ground_scan": scan,
            "mission": self.mission.status(),
            "sound_hits": self.sound.hits,
            "last_wav": str(self._skill.ears.last_wav) if self._skill.ears.last_wav else None,
            "internet": net,
            "dt_s": round(time.time() - t0, 3),
        }
        self.telemetry.record(frame)
        return frame

    def run(self, max_cycles: int = 12, stop_on_mission_complete: bool = True) -> List[Dict]:
        results = []
        for _ in range(max_cycles):
            frame = self.step()
            results.append(frame)
            self._print_cycle(frame)
            if stop_on_mission_complete and self.mission.complete:
                break
            time.sleep(0.15)
        return results

    def wait_and_see(self, topic: str) -> str:
        """Language mode still restarts the sound card on the HEAR step."""
        self.sound.restart()
        return self._skill.wait_and_see(topic)

    # ------------------------------------------------------------------ reporting
    def _print_cycle(self, frame: Dict[str, Any]) -> None:
        print(f"\n{'\u2500'*58}")
        print(f"  {self.name}  cycle {frame['cycle']}")
        print(f"{'\u2500'*58}")
        body = frame["body"]
        print(f"  pose          {np.round(body['pose'], 3)}")
        print(f"  battery       {body['battery_pct']}%   thermal {body['thermal_c']}\u00b0C")
        print(f"  d / surprise  {frame['last_d']} / {frame['last_surprise']}")
        print(f"  sound hits    {frame['sound_hits']}   wav \u2192 {Path(frame['last_wav']).name if frame['last_wav'] else '\u2014'}")
        print(f"  internet      {'OK' if frame['internet'].get('ok') else 'FAIL'}  ({frame['internet'].get('origin', frame['internet'].get('error'))})")
        m = frame["mission"]
        print(f"  mission       {m['name']}  [{m['current_idx']}/{m['total']}]  {m.get('current_label') or ('COMPLETE' if m['complete'] else '')}")

    def summary(self) -> None:
        print(f"\n{'='*58}")
        print(f"  OPTIMUS CLASS SUMMARY  \u2014  {self.name}")
        print(f"{'='*58}")
        print(f"  Cycles              : {self.cycle}")
        print(f"  Sound-card restarts : {self.sound.hits}")
        print(f"  Internet OK         : {self.internet_ok_count}/{self.cycle}")
        print(f"  Mission             : {self.mission.status()}")
        print(f"  Final pose          : {np.round(self.body.pose, 3)}")
        print(f"  Battery / thermal   : {self.body.battery_pct:.1f}% / {self.body.thermal:.1f}\u00b0C")
        print(f"  Telemetry log       : {self.telemetry.log_path}")
        print(f"  Audio dir           : {self.sound.out_dir}")
        print(f"  restart() available : yes (always restarts sound card)")
        print(f"{'='*58}\n")


# ---------------------------------------------------------------------------
# Demo entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 58)
    print("  OPTIMUS CLASS  \u2014  full humanoid on predictive-echo system")
    print("  Skill untouched \u00b7 virtual sound card \u00b7 internet \u00b7 mission")
    print("=" * 58)

    bot = OptimusClass(name="Optimus-01")
    bot.run(max_cycles=14, stop_on_mission_complete=True)
    bot.summary()
