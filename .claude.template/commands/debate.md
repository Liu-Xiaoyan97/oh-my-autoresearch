# debate

Run Phase B AgentTeam debate for the active iteration.

## Required Reads

- `runtime/objective/objective.yaml`
- `runtime/state/state.json`
- `runtime/state/current_iteration.json`
- `runtime/state/val_loss.json`
- `runtime/experiments/best.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`
- `runtime/history/timeline.json`

## AgentTeam Flow (FLAT PEER TEAM — no nesting)

Use project agents from `.claude/agents/`. You (the main turn) are the
orchestrator: `TeamCreate` one team and spawn `team-leader` TOGETHER WITH the
read-only specialists as PEERS (`run_in_background: true`). The specialists
`SendMessage` their full conclusions DIRECTLY to `team-leader` — never back to
you; the debate content must not enter the main turn. `team-leader` (the sole
writer) consolidates and writes. No agent spawns another agent (no nesting):
`team-leader` has no agent-spawning tool, and you do not route specialist
content through yourself.

1. B1: spawn `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` as peers
   to generate/stress-test candidates → they DM `team-leader`, which consolidates
   and deduplicates.
2. B2: spawn `orthogonal-direction-scout` as a peer to reject duplicates and
   confirm orthogonality → it DMs `team-leader`.
3. B3: spawn `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` as peers
   to debate survivors → they DM `team-leader`, which reconciles and confirms one
   plan.

The specialists are read-only and only DM their conclusions to `team-leader`. If
a conclusion does not exist yet, `team-leader` WAITS and re-requests it by name —
do not fabricate. `team-leader` must run one-minute response polling for missing
specialists: every 60 seconds it messages only agents that have not returned a
conclusion yet; after all required conclusions arrive it cancels that polling
before writing.

When `team-leader` signals `done`, shut the peers down
with a structured `[TEAM_COMPLETE]` message, parse its `TEAM_NAME`,
`PHASE_STEP`, `RELEASE_SESSIONS`, `TEARDOWN_REQUIRED`, and `NEXT_COMMAND`.
Before running the command, release every team member: send
`shutdown_request` to each member listed in `~/.claude/teams/<team>/config.json`
(including `team-leader`), ping-confirm each member has exited, then call
`TeamDelete`. In in-process mode, the CLI panel is rendered from the team/task
metadata, so also verify `~/.claude/teams/<team>/` and
`~/.claude/tasks/<team>/` are gone; if they remain after shutdown and
`TeamDelete`, run
`./scripts/cleanup_agentteam_metadata.py --yes --remove-team <team> --stale-only`
as the final fallback. Before creating B2/B3, also run
`./scripts/cleanup_agentteam_metadata.py --yes --stale-only`. A previous
B1/B2/B3 team must never remain visible in the CLI panel when Phase C or the
next B sub-step starts; if old in-process sessions remain visible after metadata
cleanup, send them `shutdown_request` and wait, or restart Claude CLI before
continuing.

## Required Writes (by `team-leader`)

`team-leader` waits for every required peer's conclusion, finalizes, sends the
structured `[TEAM_COMPLETE]` signal with the next command, and writes the
consolidated debate to
`runtime/debates/<exp_name>.md`: the four JSON sections (Candidate Directions,
Deduplicated Directions, Selected Direction, Modification Plan) and an
`## Agent Team Execution Log` naming every agent, recording the 60-second
polling id/retries, recording polling cancellation, and recording
`teardown_requested: true`, `release_sessions: true`, plus the `NEXT_COMMAND`.

## Apply and Advance (by the main turn)

```bash
cd /Users/liuxiaoyan/workspace/research-runtime
./scripts/apply_agentteam_plan.py --advance
./scripts/run_loop.sh
```

Run this only after the `[TEAM_COMPLETE]` teardown has released all team members
and removed the team/task metadata. Do not rely on the Stop hook to return to the
main turn.

`apply_agentteam_plan.py` parses the debate file, validates it against the
schema, writes the `current_iteration.json` decision fields, and advances to
Phase C. Do not write those fields by hand — the PreToolUse guard blocks it.

## Guardrails

- Do not modify target model code in this command.
- Do not overwrite existing debate logs.
- If B2 rejects every candidate, move the workflow to `BLOCKED`
  (`./scripts/set_phase.sh BLOCKED --reason "..."`) and record the missing
  evidence or search-space issue.
