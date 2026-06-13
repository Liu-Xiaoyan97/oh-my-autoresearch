#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


# Phases that must keep running within the SAME session. Phase A is intentionally
# excluded: it is the per-iteration boundary (Phase F returns the workflow to A).
# Allowing the session to stop there lets the context be compacted, or a fresh
# session (e.g. scripts/loop_forever.sh) start the next iteration with a clean
# context. Because runtime/ is the source of truth, resuming after a stop is
# safe. BLOCKED and DONE always allow stopping.
CONTINUE_PHASES = {"B", "C", "D", "E", "F"}


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

    if phase in CONTINUE_PHASES and status == "running" and not blocked:
        print(
            f"AutoResearch iteration in progress (phase {phase}). Continue with "
            "`./scripts/run_loop.sh` until the workflow returns to the Phase A "
            "boundary (one full iteration), then this session may stop so the "
            "context can be compacted before the next iteration.",
            file=sys.stderr,
        )
        return 2

    # phase == A (iteration boundary), BLOCKED, or DONE -> allow the session to
    # stop. At the A boundary: /compact then /loop to continue, or let
    # scripts/loop_forever.sh start the next iteration in a fresh session.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
