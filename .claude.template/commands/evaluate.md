# evaluate

Run Phase F1 AgentTeam evidence review for the active experiment.

## Required Reads

- `runtime/state/state.json`
- `runtime/state/current_iteration.json`
- `runtime/state/val_loss.json`
- `runtime/experiments/<exp_name>.json`
- `runtime/experiments/best.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`
- `runtime/history/timeline.json`

## AgentTeam Flow (FLAT PEER TEAM — no nesting)

Use project agents from `.claude/agents/`. You (the main turn) are the
orchestrator: `TeamCreate` one team and spawn `team-leader` TOGETHER WITH the
read-only specialists as PEERS (`run_in_background: true`). The specialists
`SendMessage` their full conclusions DIRECTLY to `team-leader` — never back to
you; the review content must not enter the main turn. No agent spawns another
agent (no nesting).

1. Spawn `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` as peers to
   review the completed experiment:
   - mathematical hypothesis support or contradiction;
   - numerical reliability and implementation pathologies;
   - architecture-level lesson and actionability.
2. They DM `team-leader`, which reconciles, classifies the verdict (`learned` /
   `rejected` / `inconclusive`), waits for all required F1 peers, writes the
   review, and signals the orchestrator to disband. `team-leader` does not spawn
   agents.

If a conclusion is missing, `team-leader` WAITS and re-requests it by name — do
not fabricate the verdict. `team-leader` must run one-minute response polling
for missing specialists: every 60 seconds it messages only agents that have not
returned a conclusion yet; after all required conclusions arrive it cancels that
polling before writing.

When `team-leader` signals completion with a structured `[TEAM_COMPLETE]`
message, parse its `TEAM_NAME`, `PHASE_STEP`, `RELEASE_SESSIONS`,
`TEARDOWN_REQUIRED`, and `NEXT_COMMAND`. Before running the command, release
every team member: send `shutdown_request` to each member listed in
`~/.claude/teams/<team>/config.json` (including `team-leader`), require each
member to reply via `SendMessage` with
`{"type":"shutdown_response","approve":true}`, then call `TeamDelete`. In in-process mode, the CLI
panel is rendered from the team/task metadata, so also verify
`~/.claude/teams/<team>/` and `~/.claude/tasks/<team>/` are gone; if they remain
after shutdown and `TeamDelete`, run
`./scripts/cleanup_agentteam_metadata.py --yes --remove-team <team> --stale-only`
as the final fallback. The F1 team must never remain visible in the CLI panel
after its verdict has been applied; if old in-process sessions remain visible
after metadata cleanup, send them `shutdown_request` and wait, or restart Claude
CLI before continuing.

## Required Writes (by `team-leader`)

`team-leader` writes the review to `runtime/debates/<exp_name>_f1_review.md`: the
`## F1 Verdict` JSON block (verdict, summary, missing_evidence, agent_votes) and
an `## Agent Team Execution Log` naming every required agent, recording the
60-second polling id/retries, recording polling cancellation, and recording
`teardown_requested: true`, `release_sessions: true`, plus the `NEXT_COMMAND`.

## Apply (by the main turn)

```bash
cd /Users/liuxiaoyan/workspace/research-runtime
./scripts/apply_f1_review.py
./scripts/run_loop.sh
```

Run this only after the `[TEAM_COMPLETE]` teardown has released all team members
and removed the team/task metadata. Do not rely on the Stop hook to return to the
main turn.

`apply_f1_review.py` writes `root_cause_analysis` and
`agentteam.f1_evidence_review` into `current_iteration.json` and appends the
timeline event. `phase_f_checkpoint.sh` then writes the checkpoint: `learned`
appends to `runtime/knowledge/learned_patterns.md`, `rejected` to
`runtime/knowledge/rejected_ideas.md`, `inconclusive` records missing evidence.
Do not write any of these by hand.

## Guardrails

- Do not rerun or reinterpret training without recorded evidence.
- Do not overwrite experiment records.
- `best.json` is updated by `phase_f_checkpoint.sh` only when the primary metric
  improved according to `runtime/state/val_loss.json`.
