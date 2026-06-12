# evaluate

Run Phase F2 AgentTeam evidence review for the active experiment.

## Required Reads

- `runtime/state/state.json`
- `runtime/state/current_iteration.json`
- `runtime/state/val_loss.json`
- `runtime/experiments/<exp_name>.json`
- `runtime/experiments/best.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`
- `runtime/history/timeline.json`

## AgentTeam Flow

Ask `math-theorist`, `numerical-debugger`, and `flow-arch-reviewer` to review
the completed experiment from three angles:

- mathematical hypothesis support or contradiction;
- numerical reliability and implementation pathologies;
- architecture-level lesson and actionability.

## Required Writes

- Update `runtime/state/current_iteration.json`:
  - `root_cause_analysis.status`
  - `root_cause_analysis.agent_votes`
  - `root_cause_analysis.verdict`
  - `root_cause_analysis.summary`
  - `agentteam.f2_evidence_review`
- Append a timeline event to `runtime/history/timeline.json`.
- If verdict is `learned`, append to `runtime/knowledge/learned_patterns.md`.
- If verdict is `rejected`, append to `runtime/knowledge/rejected_ideas.md`.
- If verdict is `inconclusive`, record missing evidence and do not force a learned/rejected update.

## Guardrails

- Do not rerun or reinterpret training without recorded evidence.
- Do not overwrite experiment records.
- Do not update `best.json` unless the primary metric improved according to `runtime/state/val_loss.json`.
