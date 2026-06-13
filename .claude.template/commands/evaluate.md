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

When `team-leader` signals `done`, shut the peers down
(`SendMessage {type:"shutdown_request"}`), ping-confirm each member has exited,
then `TeamDelete` BEFORE running `apply_f1_review.py` or `run_loop.sh`.
`TeamDelete` is metadata-only — it removes the team dirs but does NOT kill the
agent processes (each is an independent `claude --agent-id <name>@<team>` under
its own shell/pane). Skipping the shutdown+confirm step either makes `TeamDelete`
fail (active members) or leaves orphan iTerm2 panes; after `TeamDelete`, sweep
with `pgrep -fl -- '--agent-id'` and kill any stragglers. The F1 team must never
remain alive after its verdict has been applied.

## Required Writes (by `team-leader`)

`team-leader` writes the review to `runtime/debates/<exp_name>_f1_review.md`: the
`## F1 Verdict` JSON block (verdict, summary, missing_evidence, agent_votes) and
an `## Agent Team Execution Log` naming every required agent, recording the
60-second polling id/retries, recording polling cancellation, and recording that
the orchestrator shut down and deleted the team.

## Apply (by the main turn)

```bash
cd /Users/liuxiaoyan/workspace/research-runtime
./scripts/apply_f1_review.py
./scripts/run_loop.sh
```

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
