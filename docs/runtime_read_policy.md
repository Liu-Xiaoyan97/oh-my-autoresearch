# Runtime Read Policy

Every loop MUST restore workflow state from files before making decisions. Chat
history may be helpful context, but it is never the source of truth.

## Required Reads

At the beginning of every loop, read:

- `runtime/objective/objective.yaml`
- `runtime/state/state.json`
- `runtime/state/current_iteration.json`
- `runtime/state/val_loss.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`
- `runtime/history/timeline.json`
- `runtime/experiments/best.json`

If `runtime/state/state.json` says the active phase is not `A`, resume from the
recorded phase instead of restarting the lifecycle.

## Phase-Specific Reads

Read these files only when the phase needs them:

- `runtime/debates/<exp_name>.md`
- `runtime/experiments/<exp_name>.json`

## Missing or Invalid Files

If any required read is missing or invalid, the workflow MUST move to
`BLOCKED`, record `block_reason`, and avoid modifying the target model
repository until the runtime is repaired.
