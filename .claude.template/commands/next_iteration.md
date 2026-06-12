# next_iteration

Prepare the next Phase B iteration from runtime state.

## Required Reads

- `runtime/objective/objective.yaml`
- `runtime/state/state.json`
- `runtime/state/current_iteration.json`
- `runtime/state/val_loss.json`
- `runtime/experiments/best.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`
- `runtime/history/timeline.json`

## Required Actions

1. Confirm the workflow is in `A` or `B`; otherwise resume from the recorded phase.
2. Create or confirm the next `exp_name`.
3. Reset Phase B AgentTeam fields in `runtime/state/current_iteration.json`.
4. Run `/debate` to execute B1, B2, and B3.

## AgentTeam Requirement

The next iteration must not proceed to Phase C until:

- B1 candidates exist from `math-theorist`, `numerical-debugger`, and `flow-arch-reviewer`;
- B2 orthogonality review by `orthogonal-direction-scout` is complete;
- B3 has selected exactly one implementation plan.
