# Loop Design

## State Machine

The loop is controlled by `runtime/state/state.json`.

Allowed phases:

- A: History Maintenance
- B: Exploration Direction Generation
- C: Implementation and Local Validation
- D: Remote Training Launch
- E: Monitoring and Result Retrieval
- F: Checkpoint Write
- BLOCKED: Blocked
- DONE: Done

## Phase Transition

```text
A -> B -> C -> D -> E -> F -> A
```

Phase B is internally split into:

```text
B1 -> B2 -> B3
```

where:

- `B1` is the theory, numerical, and architecture candidate-generation pass by
  `team-leader`, `math-theorist`, `numerical-debugger`, and
  `flow-arch-reviewer`.
- `B2` is the orthogonality review by `team-leader` and
  `orthogonal-direction-scout`.
- `B3` is the final debate and plan selection by `team-leader`,
  `math-theorist`, `numerical-debugger`, and `flow-arch-reviewer`.

Phase F includes:

```text
F1
```

where `team-leader`, `math-theorist`, `numerical-debugger`, and
`flow-arch-reviewer` review the experiment evidence and produce the root-cause
verdict.

If a phase fails, the workflow MUST move to: `BLOCKED`
with 
```json
{
  "blocked": true,
  "block_reason": "..."
}
```
## State File Responsibilities

### state/state.json

Controls routing and phase recovery.

### state/current_iteration.json

Stores the active experiment state.

### state/val_loss.json

Stores the lightweight validation loss index.

### experiments/<exp_name>.json

Stores the full experiment record and loss curve.

### experiments/best.json

Stores the historical best experiment.

## Monitoring Rule

Remote training monitoring MUST be done by cron or equivalent scheduled checks.

The workflow MUST NOT use long-running sleep + ssh polling loops.

## AgentTeam Rule

AgentTeam may propose, debate, deduplicate, and evaluate ideas according to the
B1/B2/B3/F1 ownership in `docs/agentteam_protocol.md`.

AgentTeam MUST NOT directly modify model code.

Implementation is performed in Phase C by the coding executor.
