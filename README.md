# axb-optimus

Private repository for the **Optimus-class humanoid** built around the `axb-predictive-echo` skill.

## Contents

- `skill/` — the axb-predictive-echo skill (read-only, never modified by the Optimus layer)
- `optimus/` — full OptimusClass (body, sensors, mission, telemetry, restart)
- `sim/` — virtual sound card + early connectivity simulation
- `robot.py` — early thin wrapper

## Core rule (Optimus layer)

Every time the cycle hits echo → restart the virtual sound card.

`OptimusClass.restart()` also always restarts the sound card.

## Quick start

```bash
# From the optimus package root (after adjusting skill path if needed)
python -c "
from optimus.core import OptimusClass
bot = OptimusClass(name='Optimus-01')
bot.run(max_cycles=10)
bot.restart()
bot.summary()
"
```

Skill invariants remain untouched.
