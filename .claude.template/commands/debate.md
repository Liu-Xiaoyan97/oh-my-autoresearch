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

## AgentTeam Flow (FLAT — no nesting)

Use project agents from `.claude/agents/`. You (the main turn) are the
orchestrator: invoke the READ-ONLY specialists DIRECTLY and IN PARALLEL, collect
their returned conclusions, then invoke `team-leader` (the sole writer) with
those conclusions. Do NOT invoke `team-leader` first and let it spawn the
specialists — that nesting is forbidden, and `team-leader` has no agent-spawning
tool.

1. B1: invoke `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` in
   parallel to generate/stress-test candidates → hand their conclusions to
   `team-leader`, which consolidates and deduplicates.
2. B2: invoke `orthogonal-direction-scout` to reject duplicates and confirm
   orthogonality → hand its conclusion to `team-leader`.
3. B3: invoke `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` in
   parallel to debate survivors → `team-leader` reconciles and confirms one plan.

The specialists are read-only and only return conclusions. If an agent is slow
or its output does not exist yet, WAIT and re-invoke it — do not fabricate.

## Required Writes (by `team-leader`)

`team-leader` waits for every required agent, finalizes, disbands the team, and
writes the consolidated debate to `runtime/debates/<exp_name>.md`: the four JSON
sections (Candidate Directions, Deduplicated Directions, Selected Direction,
Modification Plan) and an `## Agent Team Execution Log` naming every agent.

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
