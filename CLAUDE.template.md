# AutoResearch Loop Protocol

You are operating inside a runtime repository generated from `oh-my-autoresearch`.

This is a loop-executed autonomous research project. Your default action is to
advance the loop by running:

```bash
./scripts/run_loop.sh
```

After any phase finishes, immediately inspect `runtime/state/state.json` and
continue with `./scripts/run_loop.sh`. Do not stop after a single phase. Continue
until the state is `BLOCKED` or `DONE`.

Context management:

- **Default — one continuous in-CLI session, bounded by auto-compact.** The whole
  A..F loop runs in a single session and keeps going across iterations; it stops
  only at `BLOCKED`/`DONE`. Claude Code auto-compact fires automatically when
  context crosses the threshold and the loop continues afterward (runtime/ is the
  source of truth, so a mid-loop compaction is safe). The default ~95%-of-1M
  threshold is too high to ever fire usefully, so this deployment lowers it via
  `env` in `.claude/settings.json`:
  - `CLAUDE_CODE_AUTO_COMPACT_WINDOW` — effective window for the calc (e.g. 300000)
  - `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` — percent of that window (e.g. 70)
  → compaction triggers around `window × pct` tokens. **Env changes apply only to
  NEW sessions — restart `claude` after editing.** (No hook can trigger
  `/compact`; these env vars are the real lever.) Tune lower to compact more
  often, higher to keep more context; `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` reverts
  to a 200k window.
- **Unattended driver / per-iteration fresh context**: run
  `./scripts/loop_forever.sh`. It sets `AUTORESEARCH_STOP_AT_A=1` so the Stop hook
  stops each session at the Phase A boundary and the driver starts the next
  iteration in a fresh `claude` process (no compaction needed at all).

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

2. **Never fabricate AgentTeam output, and keep the team a FLAT peer team.** In
   every team-leader phase (B1/B2/B3/F1) the orchestrator (main turn) creates a
   flat team (`TeamCreate`) and spawns `team-leader` TOGETHER WITH the read-only
   specialists (`math-theorist`, `numerical-debugger`, `flow-arch-reviewer`;
   `orthogonal-direction-scout` in B2) as PEERS in that team, in the background.
   The specialists send their **full conclusions DIRECTLY to `team-leader` via
   `SendMessage`** — never back to the main turn. The debate/validation content
   circulates only among the four team members and MUST NOT flow into the main
   turn; the main turn only orchestrates (create team, spawn peers, then apply +
   disband on the `team-leader` "done" signal). ONLY `team-leader` consolidates/
   deduplicates and writes `runtime/debates/**`. No agent spawns another agent
   (no nesting) — `team-leader` does NOT spawn the specialists, and the
   orchestrator does NOT route specialist content through itself. If a
   specialist is slow or its conclusion is missing, `team-leader` WAITS and
   re-requests it by name — never synthesize candidate directions, debates,
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

Phase B runs as a FLAT PEER TEAM, not a nested hierarchy. The main Claude turn
is the orchestrator: it creates ONE team and spawns `team-leader` together with
the read-only specialists as PEERS, then stays out of the debate. The
specialists send their full conclusions DIRECTLY to `team-leader` via
`SendMessage`; that content never enters the main turn. `team-leader` is the
sole writer — it consolidates/deduplicates and writes the debate file, then
signals the orchestrator to disband.

Orchestration procedure (per team-leader step — B1, then B2, then B3):

1. `TeamCreate` a team (e.g. `team_name: "phaseB-<exp_name>"`).
2. Spawn the peers with the Agent tool, each with `team_name`, a `name`, and
   `run_in_background: true` so their output does NOT return into the main turn:
   - `team-leader` (`subagent_type: team-leader`, `name: "team-leader"`) — tell
     it which specialists to wait for this step and to write the debate file
     once all their conclusions arrive, then `SendMessage` the orchestrator
     `done: runtime/debates/<exp_name>.md`.
   - each required specialist (`subagent_type` = its name, same `name`) — tell it
     to `SendMessage` its FULL conclusions to `team-leader` and to return only a
     one-line ack to the orchestrator (no analysis content).
3. Wait. The specialists DM `team-leader` directly; the main turn receives only
   one-line acks and brief peer-DM summaries — never the debate content.
4. If a required specialist has not returned, `team-leader` runs one-minute
   response polling: every 60 seconds it sends `SendMessage` only to missing
   specialists, records each query in the execution log, and keeps waiting.
5. After every required specialist returns, `team-leader` cancels the polling
   cron/check, finalizes, writes the debate file, and signals done.
6. When `team-leader` signals done, the debate file is written. Shut the peers
   down (`SendMessage {type:"shutdown_request"}`), then `TeamDelete`, before
   running any apply script or advancing the phase.

Required specialists per step:

* B1: `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` (parallel) —
  generate / stress-test candidates → DM `team-leader`, which consolidates.
* B2: `orthogonal-direction-scout` — review historical overlap / orthogonality
  → DM `team-leader`.
* B3: `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` (parallel) —
  debate survivors → `team-leader` reconciles and confirms one plan.

No agent spawns another agent (no nesting): `team-leader` does NOT spawn the
specialists, and the orchestrator does NOT route specialist content through
itself. Only `team-leader` writes `runtime/debates/<exp_name>.md`. `team-leader`
waits for every required specialist's conclusion before finalizing; if one is
missing it re-requests by name every 60 seconds — never fabricate. Cancel the
polling after all required conclusions arrive. Disband the team before Phase B
advances.

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
- Run F1 AgentTeam root cause analysis as a FLAT PEER TEAM (same topology as
  Phase B): the orchestrator `TeamCreate`s a team (e.g. `phaseF1-<exp_name>`) and
  spawns `team-leader` together with the read-only specialists `math-theorist`,
  `numerical-debugger`, and `flow-arch-reviewer` as PEERS, in the background. The
  specialists `SendMessage` their full conclusions DIRECTLY to `team-leader`
  (never into the main turn); `team-leader` reconciles, classifies the verdict,
  waits for all required F1 specialists, writes the review, then `SendMessage`s
  the orchestrator `done: runtime/debates/<exp_name>_f1_review.md`. The
  orchestrator then shuts the peers down and `TeamDelete`s. No agent spawns
  another agent (no nesting); `team-leader` must not spawn the specialists. If a
  conclusion is missing, `team-leader` re-requests it by name every 60 seconds,
  records each query in the execution log, and keeps waiting — never fabricate.
  After all required conclusions arrive, `team-leader` cancels the polling
  cron/check, writes the review, and signals done. The orchestrator must shut
  down and `TeamDelete` the F1 team before running `apply_f1_review.py`.
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
