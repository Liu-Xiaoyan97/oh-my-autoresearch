# AgentTeam Protocol

AgentTeam is the research reasoning layer of AutoResearch. It may propose,
critique, deduplicate, debate, synthesize, and evaluate experiment evidence. It
must not directly modify target model code.

## Active Roles

The active team is defined in `agentteam/roles/`:

- `math-theorist`
- `numerical-debugger`
- `flow-arch-reviewer`
- `orthogonal-direction-scout`

The team-level protocol lives in `agentteam/team.md`.

## Phase Ownership

| Phase step | Agents | Required result |
|---|---|---|
| `B1` | `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` | Candidate directions with theory, numerical, and architecture-risk notes. |
| `B2` | `orthogonal-direction-scout` | Historical-overlap review and deduplicated candidate list. |
| `B3` | `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` | Final debate and one concrete Phase C modification plan. |
| `F2` | `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` | Root-cause review and learned/rejected/inconclusive verdict. |

## Phase B Protocol

### B1: Candidate Generation and First Review

Inputs:

- `runtime/objective/objective.yaml`
- `runtime/state/val_loss.json`
- `runtime/experiments/best.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`
- `runtime/history/timeline.json`

Responsibilities:

- `math-theorist` checks mathematical validity and hidden assumptions.
- `numerical-debugger` checks empirical plausibility, diagnostic needs, and
  numerical failure modes.
- `flow-arch-reviewer` synthesizes trade-offs and proposes prioritized
  architecture-level directions.

Required B1 output:

- 3-5 candidate directions;
- known assumptions and risks for each candidate;
- minimum evidence required before implementation;
- initial recommendation ranking.

### B2: Orthogonality Review

`orthogonal-direction-scout` reviews B1 candidates against the runtime record.

Required checks:

- overlap with prior validation-loss records;
- overlap with timeline events;
- overlap with learned patterns;
- overlap with rejected ideas;
- overlap with prior debate records when relevant;
- whether the candidate is genuinely new or merely a renamed variation.

Required B2 output:

- accepted candidates;
- rejected duplicates or near-duplicates;
- orthogonality rationale for each accepted candidate;
- missing evidence that would block a confident review.

Candidates rejected in B2 must not reach B3 unless the workflow records an
explicit override reason in the debate log.

### B3: Final Debate and Plan Selection

The B1 team reviews the B2 result and selects one implementation plan.

Required B3 output:

- selected direction;
- modification plan for Phase C;
- expected validation signal;
- theoretical risk assessment;
- numerical diagnostic checklist;
- implementation cost;
- conditions that should move the workflow to `BLOCKED`.

Write the full B1/B2/B3 debate to:

```text
runtime/debates/<exp_name>.md
```

Write structured summaries to:

```text
runtime/state/current_iteration.json
```

## Phase F Protocol

### F2: Evidence Review and Root-Cause Analysis

After Phase E writes experiment results, the F2 team evaluates what happened.

Inputs:

- `runtime/state/current_iteration.json`
- `runtime/state/val_loss.json`
- `runtime/experiments/<exp_name>.json`
- `runtime/experiments/best.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`

Responsibilities:

- `math-theorist` evaluates whether the result supports or contradicts the
  original theoretical hypothesis.
- `numerical-debugger` checks whether observed metrics are trustworthy or
  contaminated by implementation, solver, data, or logging issues.
- `flow-arch-reviewer` synthesizes the verdict and decides whether the lesson is
  actionable.

Required F2 output:

- root-cause summary;
- per-agent vote;
- verdict: `learned`, `rejected`, or `inconclusive`;
- update for learned or rejected knowledge;
- missing evidence if inconclusive.

Append the final knowledge update to exactly one of:

```text
runtime/knowledge/learned_patterns.md
runtime/knowledge/rejected_ideas.md
```

If the verdict is `inconclusive`, append a timeline event but do not force the
method into learned or rejected knowledge.

## Runtime Write Locations

AgentTeam may write only through the workflow into these runtime files:

- `runtime/debates/<exp_name>.md`
- `runtime/state/current_iteration.json`
- `runtime/history/timeline.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`

AgentTeam must not overwrite:

- existing debate logs;
- experiment records;
- objective files;
- target model source code.

## Guardrails

- Runtime files are the source of truth, not chat history.
- AgentTeam recommendations must cite the evidence files they used.
- Missing evidence should produce `BLOCKED` or `inconclusive`, not invented
  certainty.
- Phase C implementation is performed by the coding executor, not by AgentTeam.
