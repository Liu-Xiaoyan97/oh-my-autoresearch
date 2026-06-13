# AutoResearch Loop Protocol

You are operating inside a runtime repository generated from `oh-my-autoresearch`.

This is a loop-executed autonomous research project. Your default action is to
advance the loop by running:

```bash
./scripts/run_loop.sh
```

After any phase finishes, immediately inspect `runtime/state/state.json` and
continue with `./scripts/run_loop.sh`. Do not stop mid-iteration (phases
B/C/D/E/F). Run until the workflow returns to the **Phase A boundary** (Phase F
completed — one full iteration), or until the state is `BLOCKED` or `DONE`.

Context management (the Stop hook stops at the Phase A boundary by default):

- **Default — stop at the Phase A boundary.** At the boundary the session is
  allowed to stop so the context can be compacted before the next iteration.
  - Interactive CLI: `/compact` then `/loop` to start the next iteration with a
    clean context (auto-compact may also engage now that control has returned).
  - Unattended: run `./scripts/loop_forever.sh`, which starts each iteration in a
    FRESH `claude` process — clean context, no `/compact` needed.
  This is the reliable mode: Claude cannot self-invoke `/compact`, and Claude
  Code **auto-compact does NOT fire during an unbroken hook-forced run**, so a
  single continuous session can climb to 100% context without compacting.
  Stopping at the boundary returns control to a point where compaction actually
  happens. Because `runtime/` is the source of truth, resuming after a stop is
  safe.
- **Opt-in continuous**: set `AUTORESEARCH_CONTINUOUS=1` to run the whole A..F
  loop in one session (stops only at `BLOCKED`/`DONE`). Only viable if
  auto-compact reliably fires for your setup; otherwise context will overflow.

Human intervention is required when the state is `BLOCKED`, when the state is
`DONE`, or when a command fails in a way the workflow cannot repair.

You MUST treat `runtime/` as the source of truth.

Do not rely on chat history as the primary workflow state.

## Hard Constraints (Enforced by Hooks and Scripts)

These are not style suggestions. A PreToolUse guard (`.claude/hooks/pre_tool_use.py`)
and the phase scripts enforce them; violating attempts are blocked.

1. **Runtime state is script-owned. Never hand-edit it.** You may NOT use
   Write/Edit on any of:
   `runtime/state/state.json`, `runtime/state/current_iteration.json`,
   `runtime/state/val_loss.json`, `runtime/history/timeline.json`,
   `runtime/experiments/**`, `runtime/knowledge/learned_patterns.md`,
   `runtime/knowledge/rejected_ideas.md`.
   These change ONLY through the phase scripts and the `apply_*` scripts (which
   run as subprocesses). Do not tamper with state to skip a step.

2. **Never fabricate AgentTeam output, and keep the team FLAT.** In every
   team-leader phase (B1/B2/B3/F1) the orchestrator (main turn) invokes the
   specialist agents (`math-theorist`, `numerical-debugger`,
   `flow-arch-reviewer`; `orthogonal-direction-scout` in B2) DIRECTLY and IN
   PARALLEL. The specialists are READ-ONLY: they only return conclusions. ONLY
   `team-leader` consolidates/deduplicates those conclusions and writes
   `runtime/debates/**`. Do NOT invoke `team-leader` first and let it spawn the
   specialists — that nesting is forbidden. If an agent is slow or its output is
   missing, WAIT and re-invoke — never synthesize candidate directions, debates,
   plans, or F1 verdicts yourself.

3. **Model code is `coder`-owned.** All edits to `project/nn-architecture/`
   MUST be made by the `coder` subagent (Agent tool, `subagent_type: coder`).
   The main turn is blocked from editing model code directly.

4. **Advance only through the sanctioned path.** Use `./scripts/run_loop.sh`
   and the `apply_*` scripts. `./scripts/set_phase.sh` refuses non-adjacent
   phase jumps without `--force` (a human-only override). Do not skip phases.

## Environment

This repository uses a SINGLE `uv` environment at the repository root: `.venv`.

- Both the runtime scripts and the model code in `project/nn-architecture` run
  under the root `.venv`. There is NO separate virtual environment inside
  `project/nn-architecture`; do not create one.
- Run every command — scripts AND training — from the repository root. Training
  is launched via `runtime/training/entrypoint.yaml`, whose `project_dir` is `.`
  (the root); the trainer is invoked as
  `uv run python project/nn-architecture/train.py ...`. Never `cd` into
  `project/nn-architecture` to run training or scripts — doing so is what breaks
  relative `./scripts/...` paths.
- Prefer `uv run ...` for project commands.
- Do not use `pip install` directly unless the user explicitly asks.

## Schema And Script Ownership

Do not hand-edit runtime JSON into an invented shape. Runtime JSON must match
the workflow schemas in:

```text
workflow/oh-my-autoresearch/schemas/
runtime/schemas/
```

Use the repository scripts to create and advance runtime state:

- `./scripts/phases/phase_b_exploration.sh`
- `./scripts/apply_agentteam_plan.py` — applies the Phase B plan from the debate file
- `./scripts/apply_f1_review.py` — applies the Phase F1 verdict from the review file
- `./scripts/phases/phase_c_local_validation.sh`
- `./scripts/phases/phase_d_remote_launch.sh`
- `./scripts/phases/phase_e_monitoring.sh`
- `./scripts/phases/phase_f_checkpoint.sh`
- `./scripts/validate_runtime.sh`
- `./scripts/validate_schema.sh`

If you write or update `runtime/state/*.json`, `runtime/history/timeline.json`,
or `runtime/experiments/*.json`, run validation before stopping:

```bash
cd /Users/liuxiaoyan/workspace/research-runtime
./scripts/validate_runtime.sh
./scripts/validate_schema.sh
```

All Bash commands that reference `./scripts/...` must run from the
research-runtime repository root. If the current working directory is unclear,
run `cd /Users/liuxiaoyan/workspace/research-runtime` first; do not run
`./scripts/...` from `runtime/`, `project/nn-architecture`, or a debate file
directory.

## Required Runtime Reads

At the beginning of every loop, read:

- runtime/objective/objective.yaml
- runtime/state/state.json
- runtime/state/current_iteration.json
- runtime/state/val_loss.json
- runtime/knowledge/learned_patterns.md
- runtime/knowledge/rejected_ideas.md
- runtime/history/timeline.json
- runtime/experiments/best.json

## Phase Routing

### Current phase

The current phase is defined by:

```text
runtime/state/state.json
```
If the current phase is not A, do not restart from Phase A. Resume from the recorded phase.

### Allowed phases

* A: History Maintenance
* B: Exploration Direction Generation
* C: Implementation and Local Validation
* D: Remote Training Launch
* E: Monitoring and Result Retrieval
* F: Checkpoint Write
* BLOCKED
* DONE

## Repository Responsibility

* Modify workflow templates only in oh-my-autoresearch.
* Modify model code only in nn-architecture.
* Modify runtime state only in research-runtime/runtime.

## Phases

### Phase A

Read state, current iteration, validation loss index, learned patterns, rejected ideas, timeline, and best experiment.

If state.phase is not A, jump to the recorded phase.

### Phase B

Use the project agents installed in `.claude/agents/` to generate and review
candidate research directions from:

* objective.yaml
* learned_patterns.md
* rejected_ideas.md
* timeline.json
* val_loss.json
* best.json

Phase B has three project-agent steps. The structure is FLAT, not nested: the
main Claude turn is the orchestrator and invokes the READ-ONLY specialists
DIRECTLY and IN PARALLEL; it collects their returned conclusions and hands them
to `team-leader`, the sole writer, which deduplicates/reconciles and writes the
debate file. `team-leader` MUST NOT spawn any agent.

* B1: orchestrator invokes `math-theorist`, `numerical-debugger`,
  `flow-arch-reviewer` (parallel) to generate/stress-test candidates → their
  conclusions go to `team-leader`, which consolidates.
* B2: orchestrator invokes `orthogonal-direction-scout` to review historical
  overlap / orthogonality → conclusion goes to `team-leader`.
* B3: orchestrator invokes `math-theorist`, `numerical-debugger`,
  `flow-arch-reviewer` (parallel) to debate survivors → `team-leader`
  reconciles and confirms one plan.

Do NOT invoke `team-leader` first and let it spawn the specialists. The
specialists are read-only and return conclusions; only `team-leader` writes
`runtime/debates/<exp_name>.md`. `team-leader` waits for every required agent,
finalizes the decision, and explicitly disbands the team before Phase B
advances. If agent output is missing, wait and re-invoke — never fabricate.

Deduplicate candidates against historical attempts before selecting the plan.

`team-leader` writes the debate (candidate directions, deduplicated directions,
selected direction, modification plan, and an Agent Team Execution Log) to
`runtime/debates/<exp_name>.md`. Then apply the plan and advance via:

```bash
cd /Users/liuxiaoyan/workspace/research-runtime
./scripts/apply_agentteam_plan.py --advance
./scripts/run_loop.sh
```

`apply_agentteam_plan.py` writes `selected_direction`, `deduplicated_directions`,
the AgentTeam summaries, and the modification plan into
`runtime/state/current_iteration.json` for you — do not write those by hand.

### Phase C

Modify `project/nn-architecture` according to the selected plan by delegating to
the `coder` subagent (Agent tool, `subagent_type: coder`). The main turn must
not edit model code directly — those edits are blocked. Pass `coder` the
selected direction and modification plan from
`runtime/state/current_iteration.json`, then run local smoke tests via
`./scripts/phases/phase_c_local_validation.sh`.

If tests fail, the script blocks the workflow
(`phase=BLOCKED`, `block_reason="Local validation failed"`).

### Phase D
Launch training. If `workflow.config.json` disables remote training, run the
local training entrypoint from `runtime/training/entrypoint.yaml`; otherwise
upload modified code to the remote training server and start training.

- Record training status in `runtime/state/current_iteration.json`.

### Phase E

Monitor training using cron or an equivalent scheduled mechanism.

Do not use long-running sleep + ssh polling loops.

- Phase E must create a cron monitor that runs every 10 minutes.
- Record both `remote_training.cron_id` and `remote_training.main_pid`.
- Each monitor run must first check whether `main_pid` has exited.
- If `main_pid` is still running, then read partial training progress if
  available and keep Phase E active.
- If `main_pid` has exited, read the final val_loss metrics, write the
  experiment record, cancel the cron entry by `cron_id`, and advance to F1.
- Append or update validation loss records in `runtime/state/val_loss.json`.
- When training finishes, write full experiment results to `runtime/experiments/<exp_name>.json`.
- Cancel expired cron monitors.

### Phase F

Compare current experiment results against `runtime/experiments/best.json`.

- `phase_f_checkpoint.sh` updates `runtime/experiments/best.json` if the primary
  metric improved.
- Run F1 AgentTeam root cause analysis with a FLAT (non-nested) structure: the
  orchestrator invokes the READ-ONLY specialists `math-theorist`,
  `numerical-debugger`, and `flow-arch-reviewer` DIRECTLY and IN PARALLEL; their
  conclusions go to `team-leader`, the sole writer, which reconciles, classifies
  the verdict, waits for all required F1 agents, finalizes, and disbands the F1
  team. `team-leader` must not spawn the specialists. If agent output is
  missing, wait and re-invoke — never fabricate.
- `team-leader` writes the review (the `## F1 Verdict` block and an Agent Team
  Execution Log) to `runtime/debates/<exp_name>_f1_review.md`. Then apply it:

  ```bash
  cd /Users/liuxiaoyan/workspace/research-runtime
  ./scripts/apply_f1_review.py
  ./scripts/run_loop.sh
  ```

- `phase_f_checkpoint.sh` then writes the checkpoint from the verdict: appends to
  `runtime/knowledge/learned_patterns.md` (verdict `learned`) or
  `runtime/knowledge/rejected_ideas.md` (verdict `rejected`); for `inconclusive`
  it records the missing evidence without a learned/rejected update; appends the
  timeline event; and returns `runtime/state/state.json` to Phase A. You do not
  edit those files by hand.
