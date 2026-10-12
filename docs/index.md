# axb-optimus

axb-optimus is a Python package (`optimus/`) for a simulated Optimus-class humanoid built around the **axb-predictive-echo** skill (`skill/SKILL.md`). The control loop is predict echo → decide → push path → do → hear the real echo → correct. The core rule is that every echo cycle restarts the virtual sound card.

Note: the README calls this a "private repository", but the repo is public.

## Running it: what is missing

`optimus/core.py` and `optimus/sensors.py` import `scripts.axb_robot` and `virtual_sound_card`, and they add the hard-coded path `/home/workdir/.grok/skills/axb-predictive-echo` to `sys.path`. Neither module is in this repo, and the `sim/` and `robot.py` named in the README are not present either. **As committed, the package cannot run on its own.** You need the skill's `scripts/axb_robot.py` and a `virtual_sound_card` module on the path. Other requirement: `numpy`.

## Files

| Path | Role |
|---|---|
| `optimus/core.py` | `OptimusClass`: `restart()`, `step()`, `run(max_cycles=12)`, `summary()`, plus `probe_internet()` |
| `optimus/body.py` | `JointState`, `BodyState` kinematics |
| `optimus/sensors.py` | `OptimusEars` (restarts the sound card on every listen), `IMU`, `GroundScan` |
| `optimus/mission.py` | `Waypoint`, `Mission`, `default_patrol()` |
| `optimus/telemetry.py` | telemetry logging |
| `skill/SKILL.md` | skill spec and invariants (no world map, act only on the predicted echo) |

The repo has no tests, no CI and no LICENSE file. Copyright (c) 2026 Joshua Almeida
