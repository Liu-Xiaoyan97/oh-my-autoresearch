#!/usr/bin/env python3
"""PreToolUse guard for the AutoResearch runtime.

This hook is the structural enforcement layer for the loop protocol. It runs on
every Write / Edit / MultiEdit tool call (main Claude *and* subagents) and denies
edits that would let the main turn bypass the agent-team / script-driven
workflow.

Enforced invariants
-------------------
1. Runtime state is script-owned. The state machine files are mutated **only**
   by the phase scripts and the apply_* scripts (which run as subprocesses and
   are therefore not subject to tool hooks). No tool call — from any actor — may
   hand-edit them. This kills state tampering and step-skipping.

       runtime/state/state.json
       runtime/state/current_iteration.json
       runtime/state/val_loss.json
       runtime/history/timeline.json
       runtime/experiments/**            (best.json, <exp>.json, *.metrics.json)
       runtime/knowledge/learned_patterns.md
       runtime/knowledge/rejected_ideas.md

2. Debate files are team-leader-authored. In every team-leader phase
   (B1/B2/B3/F1) the structure is FLAT: the orchestrator (main turn) invokes the
   specialist agents directly and in parallel; the specialists are READ-ONLY and
   return their conclusions; only `team-leader` consolidates/deduplicates and
   writes under runtime/debates/. Therefore only `team-leader` may write
   runtime/debates/** — not the specialists, and not the main turn. If output is
   missing, the correct action is to wait / re-invoke, never to fabricate.

3. Model code is coder-owned. Only the `coder` subagent may modify
   project/nn-architecture/. The main turn must delegate implementation to
   `coder` instead of editing the model directly.

How actor identity is determined
---------------------------------
The hook stdin payload carries `agent_type` for subagent-originated tool calls
and omits it (None) for the main Claude turn. This was verified empirically; it
is the only reliable discriminator between the main turn and a named subagent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


# In a team-leader phase the specialists are read-only; ONLY team-leader writes
# the consolidated debate/review file under runtime/debates/.
DEBATE_AGENTS = {
    "team-leader",
}

# The single agent permitted to modify model code.
CODER_AGENT = "coder"

# Files mutated exclusively by the phase scripts / apply_* scripts.
PROTECTED_STATE_FILES = {
    "runtime/state/state.json",
    "runtime/state/current_iteration.json",
    "runtime/state/val_loss.json",
    "runtime/history/timeline.json",
    "runtime/knowledge/learned_patterns.md",
    "runtime/knowledge/rejected_ideas.md",
}
PROTECTED_STATE_PREFIXES = (
    "runtime/experiments/",
)

DEBATES_PREFIX = "runtime/debates/"
MODEL_CODE_PREFIX = "project/nn-architecture/"

GUARDED_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def repo_root() -> Path:
    # .claude/hooks/pre_tool_use.py -> repo root is two levels up.
    return Path(__file__).resolve().parents[2]


def rel_path(file_path: str, root: Path) -> str | None:
    if not file_path:
        return None
    try:
        p = Path(file_path)
        if not p.is_absolute():
            p = (root / p).resolve()
        else:
            p = p.resolve()
        return p.relative_to(root).as_posix()
    except Exception:
        return None


def deny(message: str) -> int:
    print(message, file=sys.stderr)
    return 2


def evaluate(rel: str, agent_type: str | None) -> int:
    # 1. Script-owned runtime state — nobody may hand-edit via tools.
    if rel in PROTECTED_STATE_FILES or any(
        rel.startswith(prefix) for prefix in PROTECTED_STATE_PREFIXES
    ):
        return deny(
            "BLOCKED: refusing a direct tool-edit of script-owned runtime state "
            f"({rel}).\n"
            "Runtime state is mutated ONLY by the phase scripts and apply_* "
            "scripts. Hand-editing it bypasses the workflow and is forbidden.\n"
            "Use the sanctioned scripts instead, e.g.:\n"
            "  ./scripts/phases/phase_*.sh\n"
            "  ./scripts/apply_agentteam_plan.py --advance   (Phase B plan)\n"
            "  ./scripts/apply_f1_review.py                  (Phase F1 verdict)\n"
            "  ./scripts/set_phase.sh <PHASE> <STEP>\n"
            "Do NOT fabricate state to skip a step."
        )

    # 2. Debate / review files — only team-leader may author (flat, read-only
    #    specialists).
    if rel.startswith(DEBATES_PREFIX):
        if agent_type in DEBATE_AGENTS:
            return 0
        if agent_type is None:
            return deny(
                "BLOCKED: the main Claude turn must not author or fill in debate "
                f"files ({rel}).\n"
                "In team-leader phases the structure is flat: the orchestrator "
                "invokes the read-only specialists in parallel, then `team-leader` "
                "consolidates their conclusions and writes the debate file.\n"
                "If output does not exist yet, WAIT and re-invoke the agents. "
                "Fabricating agent output yourself is a protocol violation."
            )
        return deny(
            f"BLOCKED: agent '{agent_type}' may not write debate files ({rel}). "
            "Specialists are read-only and return conclusions to the orchestrator; "
            "only `team-leader` consolidates and writes runtime/debates/**."
        )

    # 3. Model code — only the coder subagent may modify.
    if rel.startswith(MODEL_CODE_PREFIX):
        if agent_type == CODER_AGENT:
            return 0
        if agent_type is None:
            return deny(
                "BLOCKED: the main Claude turn must not edit model code directly "
                f"({rel}).\n"
                "All changes to project/nn-architecture/ MUST be delegated to the "
                "`coder` subagent (Agent tool with subagent_type='coder').\n"
                "Spawn `coder` with the Phase C modification plan and let it make "
                "the edits."
            )
        return deny(
            f"BLOCKED: agent '{agent_type}' may not edit model code ({rel}). "
            "Only the `coder` subagent is permitted to modify "
            "project/nn-architecture/."
        )

    return 0


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        # Fail open on a malformed payload rather than bricking the session.
        return 0

    if payload.get("tool_name") not in GUARDED_TOOLS:
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    agent_type = payload.get("agent_type")

    root = repo_root()
    rel = rel_path(file_path, root)
    if rel is None:
        # Path outside the repo (e.g. /tmp scratch) — not our concern.
        return 0

    return evaluate(rel, agent_type)


if __name__ == "__main__":
    raise SystemExit(main())
