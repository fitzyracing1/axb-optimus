#!/usr/bin/env python3
"""
Telemetry and ground-station push for Optimus-class.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


class Telemetry:
    """Records every cycle and writes a JSONL log the ground station can pull."""

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = Path(log_dir or "/home/workdir/artifacts/axb-robot/optimus/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.records: List[Dict[str, Any]] = []
        self.session_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.log_path = self.log_dir / f"optimus_{self.session_id}.jsonl"

    def record(self, frame: Dict[str, Any]) -> None:
        frame = dict(frame)
        frame["ts"] = time.time()
        frame["session"] = self.session_id
        self.records.append(frame)
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(frame) + "\n")
        except OSError:
            # Sandbox I/O can flake; keep in-memory record and continue
            pass

    def last(self) -> Optional[Dict[str, Any]]:
        return self.records[-1] if self.records else None

    def summary(self) -> Dict[str, Any]:
        return {
            "session": self.session_id,
            "cycles": len(self.records),
            "log_path": str(self.log_path),
        }
