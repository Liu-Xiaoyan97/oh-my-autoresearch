# Lifecycle

The AutoResearch loop is a deterministic phase-based workflow.

The current phase is stored in:

```text
runtime/state/state.json
```
The workflow MUST resume from the recorded phase rather than relying on chat history.

Phases

Phase A: History Maintenance

Purpose:

* Restore workflow context.
* Read current state.
* Read prior knowledge.
* Read timeline.
* Read best experiment.

Required reads:

* runtime/state/state.json
* runtime/state/current_iteration.json
* runtime/state/val_loss.json
* runtime/knowledge/learned_patterns.md
* runtime/knowledge/rejected_ideas.md
* runtime/history/timeline.json
* runtime/experiments/best.json

If state.phase is not A, the workflow MUST jump to the recorded phase.

⸻

Phase B: Exploration Direction Generation

Purpose:

* Generate candidate research directions.
* Deduplicate against historical attempts.
* Run AgentTeam debate.
* Produce a modification plan.

AgentTeam steps:

* B1: `math-theorist`, `numerical-debugger`, and `flow-arch-reviewer`
  generate and stress-test candidate directions.
* B2: `orthogonal-direction-scout` reviews B1 candidates for historical overlap
  and orthogonality.
* B3: `math-theorist`, `numerical-debugger`, and `flow-arch-reviewer` select
  one concrete implementation plan from the B2 survivors.

Outputs:

* runtime/debates/<exp_name>.md
* runtime/state/current_iteration.json

⸻

Phase C: Implementation and Local Validation

Purpose:

* Modify the target project.
* Run smoke tests locally.

Modified repository:

* nn-architecture

Runtime updates:

* runtime/state/current_iteration.json
* runtime/state/state.json

⸻

Phase D: Remote Training Launch

Purpose:

* Upload modified code to the remote training server.
* Start remote training.

Runtime updates:

* runtime/state/current_iteration.json
* runtime/state/state.json

⸻

Phase E: Monitoring and Result Retrieval

Purpose:

* Monitor training through cron.
* Do not use sleep + ssh polling loops.
* Append monitoring results to val_loss index.
* Retrieve final logs.

Runtime updates:

* runtime/state/val_loss.json
* runtime/state/current_iteration.json
* runtime/experiments/<exp_name>.json

⸻

Phase F: Checkpoint Write

Purpose:

* Compare current result with best.json.
* Update best.json if improved.
* Run F2 AgentTeam root cause analysis with `math-theorist`,
  `numerical-debugger`, and `flow-arch-reviewer`.
* Append learned or rejected knowledge.
* Append timeline event.
* Return to Phase A.

Runtime updates:

* runtime/experiments/best.json
* runtime/knowledge/learned_patterns.md
* runtime/knowledge/rejected_ideas.md
* runtime/history/timeline.json
* runtime/state/state.json
