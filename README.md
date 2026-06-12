# oh-my-autoresearch

`oh-my-autoresearch` is a workflow template repository for building a long-running autonomous research loop with Claude Code, AgentTeam debate, external runtime state, and reproducible experiment tracking.

The first target use case is neural network architecture exploration, where an AI research loop repeatedly proposes architecture changes, modifies code, launches training, monitors validation loss, records results, and updates its research knowledge over time.

---

## Motivation

Large language models are good at reasoning, writing code, and proposing experiments, but they are not reliable as the only place to store long-running research state.

For an iterative research workflow, relying purely on natural-language context creates several problems:

- The model may forget earlier experiments after context compaction.
- It may repeat failed ideas.
- It may lose track of the current phase.
- It may overwrite or ignore historical results.
- It may continue from the wrong step after interruption.
- It may make decisions without comparing against prior validation loss records.
- It may mix workflow logic, model code, and runtime state in the same repository.

`oh-my-autoresearch` is designed to solve these problems by moving long-term state, experiment history, and workflow control out of the model context and into explicit files.

The core idea is:

```text
The model reasons.
The workflow controls.
The runtime remembers.
The project repository contains the actual research code.
```

---

## Repository Role

This repository is the workflow template and control-plane repository.

It does not contain model code, training data, checkpoints, runtime state, or experiment outputs.

It defines:

- Claude Code workflow templates
- Runtime directory contract
- AgentTeam debate protocol
- Phase-based loop lifecycle
- Runtime initialization templates
- JSON schemas
- Synchronization rules
- Validation scripts
- Prompt templates

---

## Three-Repository Architecture

The system is designed around three independent repositories.

```text
oh-my-autoresearch     = workflow template repository
nn-architecture        = target model/research code repository
research-runtime       = deployment/runtime repository
```

### 1. `oh-my-autoresearch`

This repository defines the reusable AutoResearch workflow.

It owns:

- Runtime templates
- Claude Code prompt templates
- AgentTeam role definitions
- Workflow lifecycle documentation
- Runtime contract
- Sync manifest
- Validation scripts

It must not own:

- Model source code
- Training results
- Runtime state
- Agent debate history
- Experiment records

### 2. `nn-architecture`

This is the target model repository.

It owns:

- Model code
- Training code
- Evaluation code
- Experiment configs
- Tests
- Project-specific implementation

It should not contain:

- Claude workflow state
- AgentTeam debate records
- Runtime lifecycle files
- Claude Code hooks or commands

### 3. `research-runtime`

This is the deployment-side runtime repository.

It owns:

- Runtime state
- Active objective
- AgentTeam debate logs
- Experiment index
- Validation loss records
- Best experiment record
- Submodule references to `oh-my-autoresearch` and `nn-architecture`

A typical structure is:

```text
research-runtime/
├── workflow/
│   └── oh-my-autoresearch/
├── project/
│   └── nn-architecture/
└── runtime/
    ├── objective/
    ├── state/
    ├── history/
    ├── knowledge/
    ├── debates/
    └── experiments/
```

---

## What Problem This Project Solves

`oh-my-autoresearch` aims to create a fixed, resumable, auditable research loop for AI-assisted experimentation.

The workflow is especially useful when:

- Research requires many iterations.
- Experiments run remotely.
- Training takes minutes or hours.
- Multiple agents should debate next research directions.
- Validation loss must be tracked across iterations.
- Successful and failed ideas must be remembered.
- The loop must resume after interruption.
- Runtime state must survive model context loss.

The workflow is not designed to make Claude Code a fully uncontrolled autonomous system. Instead, it provides guardrails, file-based memory, and deterministic phase routing.

---

## Core Design Principles

### 1. Runtime state is externalized

Claude must not rely on chat history as the source of truth.

Every loop must restore state from files under `runtime/`.

### 2. Workflow and project code are separated

Workflow logic lives in `oh-my-autoresearch`.

Model code lives in `nn-architecture`.

Runtime state lives in `research-runtime`.

### 3. The loop is phase-based

The workflow progresses through deterministic phases:

```text
A -> B -> C -> D -> E -> F -> A
```

The current phase is stored in:

```text
runtime/state/state.json
```

### 4. AgentTeam debates, but does not directly modify code

AgentTeam is used to generate, review, deduplicate, debate, and evaluate research directions.

Implementation is performed in the coding phase according to the selected plan.

### 5. Historical records are append-oriented

Historical files should not be casually overwritten.

Debates, timeline events, experiment records, learned patterns, and rejected ideas should preserve the reasoning trail.

### 6. Validation loss is tracked explicitly

The system maintains a lightweight validation loss index:

```text
runtime/state/val_loss.json
```

Full experiment records live in:

```text
runtime/experiments/<exp_name>.json
```

The best experiment is stored in:

```text
runtime/experiments/best.json
```

---

## Runtime Contract

The generated runtime repository should contain:

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

### `runtime/objective/objective.yaml`

Defines the project-specific research objective, success criteria, constraints, and stop conditions.

This file is initialized from the template in `oh-my-autoresearch`, but after initialization it is owned by `research-runtime`.

The workflow engine must not overwrite it after it exists.

### `runtime/state/state.json`

Stores workflow routing state.

It answers:

- Which phase is active?
- Which phase step is active?
- Which experiment is active?
- Is the workflow blocked?
- What phase should run next?

### `runtime/state/current_iteration.json`

Stores the active experiment state.

It answers:

- What is the current experiment?
- What candidate directions were generated?
- What did AgentTeam conclude in B1, B2, B3, and F2?
- Which direction was selected?
- What code modification is planned?
- Did local validation pass?
- What is the remote training status?
- What is the current result?

### `runtime/state/val_loss.json`

Stores the validation loss index across experiments.

It should be lightweight and used for ranking, comparison, and decision support.

It should not contain full training curves.

### `runtime/debates/<exp_name>.md`

Stores the full AgentTeam debate for one experiment.

### `runtime/history/timeline.json`

Stores chronological workflow events.

### `runtime/knowledge/learned_patterns.md`

Stores methods judged effective after experiment review.

### `runtime/knowledge/rejected_ideas.md`

Stores methods judged ineffective, harmful, unstable, or redundant.

### `runtime/experiments/<exp_name>.json`

Stores the full record of one experiment, including loss curves and metadata.

### `runtime/experiments/best.json`

Stores the historical best experiment according to the primary metric.

---

## Workflow Lifecycle

The loop has six phases.

### Phase A: History Maintenance

Purpose:

- Restore current workflow state.
- Read active experiment status.
- Read validation loss index.
- Read learned and rejected knowledge.
- Read historical timeline.
- Read current best experiment.

Required reads:

```text
runtime/state/state.json
runtime/state/current_iteration.json
runtime/state/val_loss.json
runtime/knowledge/learned_patterns.md
runtime/knowledge/rejected_ideas.md
runtime/history/timeline.json
runtime/experiments/best.json
```

If `state.phase` is not `A`, the workflow must resume from the recorded phase instead of restarting.

---

### Phase B: Exploration Direction Generation

Purpose:

- Build an AgentTeam.
- Read the objective and historical records.
- Generate candidate directions.
- Deduplicate against previous attempts.
- Run debate.
- Produce a concrete modification plan.

Inputs:

```text
runtime/objective/objective.yaml
runtime/state/val_loss.json
runtime/experiments/best.json
runtime/knowledge/learned_patterns.md
runtime/knowledge/rejected_ideas.md
runtime/history/timeline.json
```

Outputs:

```text
runtime/debates/<exp_name>.md
runtime/state/current_iteration.json
```

---

### Phase C: Implementation and Local Validation

Purpose:

- Modify the target model repository.
- Run local smoke tests.

The modified repository is:

```text
nn-architecture
```

Runtime updates:

```text
runtime/state/current_iteration.json
runtime/state/state.json
```

If validation fails, the workflow moves to `BLOCKED`.

---

### Phase D: Remote Training Launch

Purpose:

- Upload modified code to the remote training environment.
- Start the training command.

Runtime updates:

```text
runtime/state/current_iteration.json
runtime/state/state.json
```

---

### Phase E: Monitoring and Result Retrieval

Purpose:

- Monitor training progress.
- Avoid long-running `sleep + ssh` polling loops.
- Use cron or an equivalent scheduled monitor.
- Append validation loss updates.
- Retrieve final logs.
- Write the full experiment record.

Runtime updates:

```text
runtime/state/val_loss.json
runtime/state/current_iteration.json
runtime/experiments/<exp_name>.json
```

---

### Phase F: Checkpoint Write

Purpose:

- Compare current result with historical best.
- Update `best.json` if improved.
- Run AgentTeam root cause analysis.
- Decide whether the method is effective.
- Append to learned or rejected knowledge.
- Append the timeline event.
- Return to Phase A.

Runtime updates:

```text
runtime/experiments/best.json
runtime/knowledge/learned_patterns.md
runtime/knowledge/rejected_ideas.md
runtime/history/timeline.json
runtime/state/state.json
```

---

## AgentTeam

AgentTeam is used for research reasoning, not direct code modification.

Active roles:

```text
math-theorist
numerical-debugger
flow-arch-reviewer
orthogonal-direction-scout
```

Phase assignment:

```text
B1 = math-theorist + numerical-debugger + flow-arch-reviewer
B2 = orthogonal-direction-scout
B3 = math-theorist + numerical-debugger + flow-arch-reviewer
F2 = math-theorist + numerical-debugger + flow-arch-reviewer
```

Typical responsibilities:

- Generate candidate research directions from theory, numerical evidence, and architecture trade-offs.
- Review historical overlap and orthogonality before implementation.
- Debate risks, benefits, boundary conditions, and diagnostic needs.
- Produce one concrete Phase C modification plan.
- Evaluate completed experiments and decide whether the result is learned, rejected, or inconclusive.

The current role definitions live in:

```text
agentteam/roles/
```

The team-level protocol lives in:

```text
agentteam/team.md
```

---

## Current Repository Structure

```text
oh-my-autoresearch/
├── agentteam/
│   ├── roles/
│   │   ├── flow-arch-reviewer.md
│   │   ├── math-theorist.md
│   │   ├── numerical-debugger.md
│   │   └── orthogonal-direction-scout.md
│   └── team.md
├── CLAUDE.template.md
├── docs/
│   ├── agentteam_protocol.md
│   ├── lifecycle.md
│   ├── loop_design.md
│   ├── repository_responsibility.md
│   ├── runtime_contract.md
│   ├── runtime_read_policy.md
│   └── synchronization.md
├── LICENSE
├── manifests/
│   └── nn_architecture.yaml
├── prompts/
│   ├── debate_protocol.md
│   ├── experiment_review.md
│   ├── global_system.md
│   ├── memory_compaction.md
│   └── proposal_format.md
├── README.md
├── schemas/
│   ├── best.schema.json
│   ├── current_iteration.schema.json
│   ├── objective.schema.json
│   ├── timeline.schema.json
│   ├── val_loss.schema.json
│   └── state.schema.json
├── scripts/
│   ├── compact_memory.py
│   ├── generate_next_iteration.py
│   ├── install_runtime.py
│   ├── runtime_manifest.py
│   ├── score_proposals.py
│   ├── sync_runtime.py
│   ├── update_templates.py
│   └── validate_workflow.py
├── templates/
│   └── nn_architecture/
│       └── runtime/
│           ├── debates/
│           ├── experiments/
│           │   └── best.json
│           ├── history/
│           │   └── timeline.json
│           ├── knowledge/
│           │   ├── learned_patterns.md
│           │   └── rejected_ideas.md
│           ├── objective/
│           │   └── objective.yaml
│           └── state/
│               ├── current_iteration.json
│               ├── state.json
│               └── val_loss.json
└── VERSION
```

---

## What This Project Is Not

`oh-my-autoresearch` is not:

- A model training framework.
- A replacement for the target research repository.
- A storage location for checkpoints.
- A place for raw datasets.
- A place for runtime experiment history.
- A fully unsupervised system that should freely push code or run arbitrary commands.

It is a workflow template and control layer for reproducible, resumable, AI-assisted research loops.

---

## Current Status

This project is in early design and implementation.

The current focus is to stabilize:

- Runtime contract
- Phase lifecycle
- AgentTeam debate protocol
- Validation loss tracking
- Experiment result recording
- Best-result checkpointing
- Workflow/runtime synchronization

The first supported workflow type is:

```text
nn_architecture
```

---

## Design Summary

`oh-my-autoresearch` exists to make Claude Code usable for long-running iterative research without depending on fragile chat context.

It provides a structured workflow where:

```text
Claude proposes and reasons.
AgentTeam debates and evaluates.
Coders implement selected plans.
Remote training produces evidence.
Runtime files preserve memory.
The loop resumes from explicit state.
```

The intended result is a research process that is more reproducible, inspectable, and resistant to context loss than a purely natural-language agent conversation.
