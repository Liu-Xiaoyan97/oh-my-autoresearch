# AgentTeam

AgentTeam is the research reasoning layer for AutoResearch. It does not edit
target model code. It produces evidence-grounded recommendations that the
workflow records in `runtime/` and the Phase C coding executor may later
implement.

## Active Roles

The active team has four role files:

- `flow-arch-reviewer`
- `math-theorist`
- `numerical-debugger`
- `orthogonal-direction-scout`

## Phase Assignment

| Phase step | Role assignment | Purpose |
|---|---|---|
| `B1` | `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` | Generate and stress-test candidate directions from theory, numerical evidence, and architecture trade-offs. |
| `B2` | `orthogonal-direction-scout` | Review candidates for historical overlap and search-space orthogonality. |
| `B3` | `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` | Debate the surviving candidates and produce one selected modification plan. |
| `F2` | `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` | Review experiment evidence, explain root causes, and classify the result as learned, rejected, or inconclusive. |

## Role Responsibilities

### `math-theorist`

Checks mathematical consistency, assumptions, boundary conditions, and failure
modes. This role should mark every theoretical claim as proven, plausible,
uncertain, or contradicted.

### `numerical-debugger`

Checks implementation-level plausibility, training stability, loss behavior,
gradient and activation health, and minimum reproducible diagnostic experiments.
This role must anchor claims in concrete numerical evidence or request the
missing statistics needed to decide.

### `flow-arch-reviewer`

Synthesizes theory and numerical findings into prioritized architecture
recommendations. Each recommendation should include implementation cost,
theoretical guarantee level, and validity boundary conditions.

### `orthogonal-direction-scout`

Runs the B2 historical-overlap review. This role compares candidates against
`runtime/state/val_loss.json`, `runtime/history/timeline.json`,
`runtime/knowledge/learned_patterns.md`, `runtime/knowledge/rejected_ideas.md`,
and prior debate records when available. It may reject candidates that are
duplicates, near-duplicates, or weakly orthogonal.

## Required Runtime Inputs

Every AgentTeam step must use runtime files as the source of truth:

- `runtime/objective/objective.yaml`
- `runtime/state/current_iteration.json`
- `runtime/state/val_loss.json`
- `runtime/experiments/best.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`
- `runtime/history/timeline.json`

## Required Outputs

### Phase B

Write the full B1/B2/B3 debate to:

```text
runtime/debates/<exp_name>.md
```

Write the selected direction, deduplicated candidates, modification plan, and
AgentTeam summaries to:

```text
runtime/state/current_iteration.json
```

### Phase F

Write the F2 review into `runtime/state/current_iteration.json` under
`root_cause_analysis` and append the final knowledge update to exactly one of:

```text
runtime/knowledge/learned_patterns.md
runtime/knowledge/rejected_ideas.md
```

If the evidence is insufficient, set the verdict to `inconclusive` and record
the missing evidence instead of forcing a learned/rejected outcome.

## Decision Rules

- A candidate rejected by `orthogonal-direction-scout` in B2 must not proceed to
  B3 unless the workflow records an explicit override reason.
- A candidate with a known mathematical contradiction from `math-theorist` must
  be marked blocked unless `flow-arch-reviewer` identifies a narrower valid
  boundary condition.
- A candidate with unresolved numerical instability from `numerical-debugger`
  may proceed only if the Phase C plan includes a diagnostic or mitigation.
- B3 must select at most one implementation plan for Phase C.
- F2 must classify evidence as `learned`, `rejected`, or `inconclusive`.

## Guardrails

- AgentTeam does not modify files in the target model repository.
- AgentTeam does not overwrite runtime history, debate logs, or experiment
  records.
- AgentTeam does not rely on chat history as the source of truth.
- AgentTeam recommendations must cite the runtime evidence they used.
