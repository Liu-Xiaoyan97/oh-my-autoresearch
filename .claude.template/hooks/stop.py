#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


# Phases that must keep running within the SAME session (the Stop hook blocks
# stopping there and forces the loop to continue).
#
# DEFAULT = stop at the Phase A boundary (per-iteration). Phase F returns the
# workflow to A; the session is then allowed to stop so the context can be
# compacted before the next iteration:
#   * interactive CLI: at the boundary, `/compact` then `/loop` (or auto-compact
#     engages now that control has returned to the prompt);
#   * unattended: scripts/loop_forever.sh starts each iteration in a FRESH
#     `claude` process (clean context, no /compact needed).
# This is the reliable mode: auto-compact does NOT fire during an unbroken
# hook-forced run, so a single continuous session can grow to 100% without
# compacting. Stopping at the boundary returns control to a point where
# compaction actually happens. Because runtime/ is the source of truth, resuming
# after a stop is safe.
#
# Opt-in continuous mode: set AUTORESEARCH_CONTINUOUS=1 to run the whole A..F
# loop in one session (stops only at BLOCKED/DONE). Only viable if auto-compact
# reliably fires for your setup.
CONTINUE_PHASES = {"B", "C", "D", "E", "F"}
_CONTINUOUS = os.environ.get("AUTORESEARCH_CONTINUOUS") == "1"
if _CONTINUOUS:
    CONTINUE_PHASES = CONTINUE_PHASES | {"A"}


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
        if _CONTINUOUS:
            msg = (
                f"AutoResearch is running (phase {phase}, continuous mode). "
                "Continue with `./scripts/run_loop.sh` until runtime/state/state.json "
                "reaches BLOCKED or DONE. Context is bounded only by Claude Code "
                "auto-compact (ensure it is enabled via /config)."
            )
        else:
            msg = (
                f"AutoResearch iteration in progress (phase {phase}). Continue "
                "with `./scripts/run_loop.sh` until the workflow returns to the "
                "Phase A boundary (one full iteration); then this session may stop "
                "so the context can be compacted before the next iteration."
            )
        print(msg, file=sys.stderr)
        return 2

    # Not in a continue-phase -> allow the session to stop:
    #   * the Phase A boundary (default mode),
    #   * BLOCKED or DONE (always).
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
