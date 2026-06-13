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
(`SendMessage {type:"shutdown_request"}`), ping-confirm each member has exited,
then `TeamDelete` BEFORE running `apply_agentteam_plan.py` or `run_loop.sh`.
`TeamDelete` is metadata-only — it removes the team dirs but does NOT kill the
agent processes (each is an independent `claude --agent-id <name>@<team>` under
its own shell/pane). Skipping the shutdown+confirm step either makes `TeamDelete`
fail (active members) or leaves orphan iTerm2 panes; after `TeamDelete`, sweep
with `pgrep -fl -- '--agent-id'` and kill any stragglers. A previous B1/B2/B3
team must never remain alive when Phase C or the next B sub-step starts.

## Required Writes (by `team-leader`)

`team-leader` waits for every required peer's conclusion, finalizes, signals the
orchestrator to disband, and writes the consolidated debate to
`runtime/debates/<exp_name>.md`: the four JSON sections (Candidate Directions,
Deduplicated Directions, Selected Direction, Modification Plan) and an
`## Agent Team Execution Log` naming every agent, recording the 60-second
polling id/retries, recording polling cancellation, and recording that the
orchestrator shut down and deleted the team.

## Apply and Advance (by the main turn)

```bash
cd /Users/liuxiaoyan/workspace/research-runtime
./scripts/apply_agentteam_plan.py --advance
./scripts/run_loop.sh
```

`apply_agentteam_plan.py` parses the debate file, validates it against the
schema, writes the `current_iteration.json` decision fields, and advances to
Phase C. Do not write those fields by hand — the PreToolUse guard blocks it.

## Guardrails

- Do not modify target model code in this command.
- Do not overwrite existing debate logs.
- If B2 rejects every candidate, move the workflow to `BLOCKED`
  (`./scripts/set_phase.sh BLOCKED --reason "..."`) and record the missing
  evidence or search-space issue.
