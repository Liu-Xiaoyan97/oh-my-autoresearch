#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


# Phases that must keep running within the SAME session (the Stop hook blocks
# stopping there and forces the loop to continue).
#
# Two modes:
#   * Default (in-CLI continuous run): the whole A..F loop runs in ONE session;
#     Phase A also keeps going. Context is bounded by Claude Code's auto-compact
#     (enable it via /config). The session stops only at BLOCKED or DONE.
#   * AUTORESEARCH_STOP_AT_A=1 (set by scripts/loop_forever.sh): the session is
#     allowed to stop at the Phase A boundary (Phase F returns the workflow to
#     A), so an external driver can start each iteration in a FRESH session with
#     a clean context. Because runtime/ is the source of truth, resuming is safe.
CONTINUE_PHASES = {"B", "C", "D", "E", "F"}
if os.environ.get("AUTORESEARCH_STOP_AT_A") != "1":
    # Continuous in-CLI mode: do not stop at the Phase A boundary either.
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
        if os.environ.get("AUTORESEARCH_STOP_AT_A") == "1":
            msg = (
                f"AutoResearch iteration in progress (phase {phase}). Continue "
                "with `./scripts/run_loop.sh` until the workflow returns to the "
                "Phase A boundary (one full iteration); then this session may stop."
            )
        else:
            msg = (
                f"AutoResearch is running (phase {phase}). Continue the loop with "
                "`./scripts/run_loop.sh` until runtime/state/state.json reaches "
                "BLOCKED or DONE. Context is bounded by Claude Code auto-compact "
                "(ensure it is enabled via /config)."
            )
        print(msg, file=sys.stderr)
        return 2

    # Not in a continue-phase (e.g. BLOCKED / DONE, or the Phase A boundary when
    # AUTORESEARCH_STOP_AT_A=1) -> allow the session to stop.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
