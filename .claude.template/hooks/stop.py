#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


# By default this hook is advisory: it allows the main session to stop. The
# AutoResearch loop is driven by explicit commands sent through the AgentTeam
# protocol, not by Stop-hook coercion. This matters for in-process AgentTeam
# mode: forcing the main turn to continue after a team finishes can keep old
# team/task metadata rendered in the CLI panel and wastes context.
#
# Opt-in force mode: set AUTORESEARCH_FORCE_CONTINUE=1 when you intentionally
# want the old "do not stop mid-loop" behavior. scripts/loop_forever.sh sets
# this flag for unattended driver sessions and also sets AUTORESEARCH_STOP_AT_A=1
# so each spawned session may stop at the next Phase A boundary.
CONTINUE_PHASES = {"B", "C", "D", "E", "F"}
_FORCE_CONTINUE = os.environ.get("AUTORESEARCH_FORCE_CONTINUE") == "1"
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

    if not _FORCE_CONTINUE:
        return 0

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
