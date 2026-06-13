#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


# Phases that must keep running within the SAME session (the Stop hook blocks
# stopping there and forces the loop to continue).
#
# DEFAULT = continuous in-CLI run: the whole A..F loop runs in ONE session and
# keeps going across iterations; it stops only at BLOCKED or DONE. Context is
# bounded by Claude Code auto-compact, which fires automatically once usage
# crosses the threshold. NOTE: the default 95%-of-1M threshold is far too high
# to ever fire usefully — this deployment lowers it via env in
# .claude/settings.json (CLAUDE_CODE_AUTO_COMPACT_WINDOW + AUTOCOMPACT_PCT) so
# compaction actually triggers mid-loop. (No hook can trigger /compact itself;
# the threshold env vars are the real lever.)
#
# Opt-in boundary mode: set AUTORESEARCH_STOP_AT_A=1 (scripts/loop_forever.sh
# does this) to allow stopping at the Phase A boundary, so an external driver can
# start each iteration in a fresh process. runtime/ is the source of truth, so
# resuming after any stop/compaction is safe.
CONTINUE_PHASES = {"B", "C", "D", "E", "F"}
_STOP_AT_A = os.environ.get("AUTORESEARCH_STOP_AT_A") == "1"
if not _STOP_AT_A:
    CONTINUE_PHASES = CONTINUE_PHASES | {"A"}


def main() -> int:
    # ---- subagent detection ----
    # Subagents (team members) must always be allowed to stop — the orchestrator
    # sends them shutdown_request, and they must obey. Only the main turn should
    # be forced to continue the loop.
    #
    # Detection: read stdin JSON (same mechanism as pre_tool_use.py). The Stop
    # hook payload includes "agent_type" for subagents and omits it (None) for
    # the main Claude turn. If agent_type is present and non-null, this is a
    # subagent — allow stopping unconditionally.
    try:
        raw = sys.stdin.read()
        if raw.strip():
            payload = json.loads(raw)
            agent_type = payload.get("agent_type")
            if agent_type is not None:
                # Running as a subagent → always allow stop
                return 0
    except (json.JSONDecodeError, Exception):
        pass
    # ---- end subagent detection ----

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
        if _STOP_AT_A:
            msg = (
                f"AutoResearch iteration in progress (phase {phase}). Continue "
                "with `./scripts/run_loop.sh` until the workflow returns to the "
                "Phase A boundary (one full iteration); then this session may stop."
            )
        else:
            msg = (
                f"AutoResearch is running (phase {phase}). Continue the loop with "
                "`./scripts/run_loop.sh` until runtime/state/state.json reaches "
                "BLOCKED or DONE. Context is bounded automatically by Claude Code "
                "auto-compact (threshold configured in .claude/settings.json env)."
            )
        print(msg, file=sys.stderr)
        return 2

    # Not in a continue-phase -> allow the session to stop:
    #   * BLOCKED or DONE (always),
    #   * the Phase A boundary when AUTORESEARCH_STOP_AT_A=1.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
