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

## AgentTeam Flow

1. B1: ask `math-theorist`, `numerical-debugger`, and `flow-arch-reviewer` to generate and stress-test candidate directions.
2. B2: ask `orthogonal-direction-scout` to reject duplicates and confirm orthogonality against runtime history.
3. B3: ask `math-theorist`, `numerical-debugger`, and `flow-arch-reviewer` to select one Phase C implementation plan.

## Required Writes

- Append the full B1/B2/B3 debate to `runtime/debates/<exp_name>.md`.
- Update `runtime/state/current_iteration.json` with:
  - `candidate_directions`
  - `deduplicated_directions`
  - `selected_direction`
  - `modification_plan`
  - `agentteam.b1_candidate_review`
  - `agentteam.b2_orthogonality_review`
  - `agentteam.b3_plan_selection`
- Update `runtime/state/state.json` to the next phase only after the debate output is complete.

## Guardrails

- Do not modify target model code in this command.
- Do not overwrite existing debate logs.
- If B2 rejects every candidate, move the workflow to `BLOCKED` and record the missing evidence or search-space issue.
