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
do not fabricate. When `team-leader` signals `done`, shut the peers down
(`SendMessage {type:"shutdown_request"}`) and `TeamDelete`.

## Required Writes (by `team-leader`)

`team-leader` waits for every required peer's conclusion, finalizes, signals the
orchestrator to disband, and writes the consolidated debate to
`runtime/debates/<exp_name>.md`: the four JSON sections (Candidate Directions,
Deduplicated Directions, Selected Direction, Modification Plan) and an
`## Agent Team Execution Log` naming every agent.

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
