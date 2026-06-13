#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ACTIVE_PHASES = {"A", "B", "C", "D", "E", "F"}


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    state_path = root / "runtime/state/state.json"
    if not state_path.exists():
        return 0

    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Cannot stop: invalid runtime state JSON: {exc}", file=sys.stderr)
        return 2

    phase = state.get("phase")
    status = state.get("workflow_status")
    blocked = bool(state.get("blocked"))

    if phase in ACTIVE_PHASES and status == "running" and not blocked:
        print(
            "AutoResearch is still running. Continue the loop with "
            "`./scripts/run_loop.sh` until runtime/state/state.json reaches "
            "BLOCKED or DONE.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
