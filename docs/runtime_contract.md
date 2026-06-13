# Runtime Contract

`runtime/` is the single source of truth for active workflow state, experiment records, AgentTeam debates, and learned research knowledge.

## Directory Structure

```text
runtime/
├── objective/
│   └── objective.yaml
├── state/
│   ├── state.json
│   ├── current_iteration.json
│   └── val_loss.json
├── debates/
│   └── <exp_name>.md
├── history/
│   └── timeline.json
├── knowledge/
│   ├── learned_patterns.md
│   └── rejected_ideas.md
└── experiments/
    ├── <exp_name>.json
    └── best.json
```
File Responsibilities

objective/objective.yaml

Defines the project-specific research goal, success criteria, constraints, and stop conditions.

This file is initialized from the workflow template but owned by the runtime repository after initialization.

The workflow engine MUST NOT overwrite this file after it exists.

state/state.json

Stores the workflow phase and routing state.

This file answers:

* Which phase is currently active?
* Which phase step is active?
* Which experiment is active?
* Is the workflow blocked?

state/current_iteration.json

Stores the active experiment state.

This file answers:

* What is the active experiment?
* What direction was selected?
* What code modification was planned?
* What did AgentTeam conclude in B1, B2, B3, and F1?
* Did local validation pass?
* What is the remote training status?
* What was the final result?

The `agentteam` object stores structured summaries for:

* `b1_candidate_review`
* `b2_orthogonality_review`
* `b3_plan_selection`
* `f1_evidence_review`

The full debate remains append-oriented in `runtime/debates/<exp_name>.md`.

state/val_loss.json

Stores the validation loss index across experiments.

This file is not the full experiment record.

It should contain lightweight records for ranking and comparison only.

debates/<exp_name>.md

Stores full AgentTeam debate logs for a single experiment.

This file MUST NOT be overwritten.

history/timeline.json

Stores chronological workflow events.

This file SHOULD be append-only.

knowledge/learned_patterns.md

Stores empirically effective methods and root cause analysis.

knowledge/rejected_ideas.md

Stores empirically ineffective methods and root cause analysis.

experiments/<exp_name>.json

Stores the full experiment record, including loss curve and metadata.

experiments/best.json

Stores the historical best experiment according to the primary metric.

Required Reads at Loop Start

Every loop MUST read:

* runtime/objective/objective.yaml
* runtime/state/state.json
* runtime/state/current_iteration.json
* runtime/state/val_loss.json
* runtime/knowledge/learned_patterns.md
* runtime/knowledge/rejected_ideas.md
* runtime/history/timeline.json
* runtime/experiments/best.json

Write Policy

Overwrite allowed:

* runtime/state/state.json
* runtime/state/current_iteration.json
* runtime/state/val_loss.json
* runtime/experiments/best.json

Create per experiment:

* runtime/debates/<exp_name>.md
* runtime/experiments/<exp_name>.json

Append only:

* runtime/history/timeline.json
* runtime/knowledge/learned_patterns.md
* runtime/knowledge/rejected_ideas.md

Never overwrite after initialization:

* runtime/objective/objective.yaml
