# AutoResearch Loop Protocol

You are operating inside a runtime repository generated from `oh-my-autoresearch`.

This is a loop-executed autonomous research project. Your default action is to
advance the loop by running:

```bash
./scripts/run_loop.sh
```

After any phase finishes, immediately inspect `runtime/state/state.json` and
continue with `./scripts/run_loop.sh`, unless you are waiting for an AgentTeam
completion signal. AgentTeam phases advance by an explicit `[TEAM_COMPLETE]`
message from `team-leader`; that message includes the `NEXT_COMMAND` the main
turn must run after teardown. Continue until the state is `BLOCKED` or `DONE`.

Context management:

- **Default — explicit in-process continuation.** The Stop hook is non-coercive
  by default: it does not force the main turn to keep running. Continue by
  running the explicit commands produced by the phase scripts or by the
  AgentTeam `[TEAM_COMPLETE]` signal. This prevents the Stop hook from dragging
  the main turn forward while old in-process team sessions are still being
  released. Claude Code auto-compact still fires automatically when context
  crosses the threshold (runtime/ is the source of truth, so a mid-loop
  compaction is safe). The default ~95%-of-1M threshold is too high to ever fire
  usefully, so this deployment lowers it via `env` in `.claude/settings.json`:
  - `CLAUDE_CODE_AUTO_COMPACT_WINDOW` — effective window for the calc (e.g. 300000)
  - `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` — percent of that window (e.g. 70)
  → compaction triggers around `window × pct` tokens. **Env changes apply only to
  NEW sessions — restart `claude` after editing.** (No hook can trigger
  `/compact`; these env vars are the real lever.) Tune lower to compact more
  often, higher to keep more context; `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` reverts
  to a 200k window.
- **Unattended driver / per-iteration fresh context**: run
  `./scripts/loop_forever.sh`. It sets `AUTORESEARCH_FORCE_CONTINUE=1` and
  `AUTORESEARCH_STOP_AT_A=1` so the Stop hook is used only inside driver-spawned
  sessions: it blocks mid-iteration stops, then allows stopping at the Phase A
  boundary so the driver can start the next iteration in a fresh `claude`
  process (no compaction needed at all).

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

**关键约束：一个阶段只允许一个 team。** 每个 B1/B2/B3 步骤都必须创建新的
team，但在同一时间内只能存在一个活跃的 team。在创建新 team 之前，必须
先确认上一个 team 已完全清除（TeamDelete + shutdown）。

**耐心与重建不变量（主程序行为规约）。** 主程序对每个阶段的 team 必须**保持
耐心**：单个 team 的等待预算为**最长 20 分钟**（从该 team 创建、或上一次成功
重启 agent 起算，以较晚者为准）。在预算内不得催促性地拆除或重建 team。超时后
也不要直接放弃，而是先**向 team-leader 询问哪些 agent 需要重启**并重启它们；
**只有在确认 team-leader 本身已崩溃（无法应答）时，才清空并重建整个 team。**
铁律：**只要 team-leader 还在（能应答），就绝不创建新的 team，也不 TeamDelete**
——重建只发生在 team-leader 确认失联之后。

Orchestration procedure (per team-leader step — B1, then B2, then B3):

1. **检查 team 唯一性。** 在创建任何新 team 之前，确认没有活跃的 team 存在。
   如果 `~/.claude/teams/` 目录下已有活跃的 team 配置，必须先清理干净
   （发送 shutdown_request、TeamDelete）。
   然后运行：
   ```bash
   ./scripts/cleanup_agentteam_metadata.py --yes --stale-only
   ```
   如果 CLI agent 面板仍显示上一 B 子阶段的 in-process agent，说明旧 session
   还活在当前 Claude 进程内存里；此时**不得创建下一 team**，必须先对可见旧
   agent 发送 `shutdown_request` 并等待它们消失，必要时重启 Claude CLI。

2. `TeamCreate` a team (e.g. `team_name: "phaseB-<exp_name>"`).

3. Spawn the peers with the Agent tool, each with `team_name`, a `name`, and
   `run_in_background: true` so their output does NOT return into the main turn:
   - `team-leader` (`subagent_type: team-leader`, `name: "team-leader"`) — tell
     it which specialists to wait for this step and to write the debate file
     once all their conclusions arrive, then `SendMessage` the orchestrator the
     structured `[TEAM_COMPLETE]` signal with `TEAM_NAME`, `PHASE_STEP`,
     `RELEASE_SESSIONS: true`, `TEARDOWN_REQUIRED`, and `NEXT_COMMAND`.
   - each required specialist (`subagent_type` = its name, same `name`) — tell it
     to `SendMessage` its FULL conclusions to `team-leader` with the
     `[CONCLUSION] <agent-name>` format as the first line, and to return only a
     one-line ack to the orchestrator (no analysis content).

4. **主程序不创建常驻监控 cron。** in-process 模式下，team 面板/session 的生命
   周期必须由完成信号后的同步 teardown 驱动；不要再依赖 Stop hook 或主程序
   监控 cron 把流程强行拉回主 turn。`team-leader` 自己已经有 60 秒 polling
   cron，会催促未回传的 specialist，并在全部完成后取消该 cron。

5. **主程序只与 team-leader 通讯。** 主程序（编排者）在任何时候都**不得**直接
   向 team 中的其他 agent（math-theorist、numerical-debugger、flow-arch-reviewer、
   orthogonal-direction-scout）发送消息或接收其分析内容。所有 team 内部通讯
   仅发生在 team-leader 与各 specialist 之间。唯一例外是 teardown：收到
   `[TEAM_COMPLETE]` 后，主程序必须按 team config 中的成员名单向**非 lead 的
   project agents** 发送 `shutdown_request`，这不是分析通讯，而是 session 释放
   协议。**不要向 `team-lead` 发送 shutdown_request**：`team-lead` 是主进程/
   编排者，等待它的 `shutdown_response` 会把主进程也纳入退出协议，导致流程卡住。

6. **`team-leader` 内部机制。** `team-leader` 在启动时创建自己的 60 秒轮询
   cron（使用 `CronCreate`），在 cron 触发时检查缺失的 specialist 并发送
   提醒。所有 specialist 回传 `[CONCLUSION]` 后，`team-leader` 取消轮询 cron
   （`CronDelete`），整理写入 debate 文件，然后向主程序发送 `[TEAM_COMPLETE]`
   消息，里面包含 `NEXT_COMMAND`。

7. **主程序收到 `[TEAM_COMPLETE]` 后同步清理并推进。** 不写
   `.cron_team_completed`，不等待 Stop hook 重新唤醒自己。主程序必须：

   a. 解析 `TEAM_NAME`、`PHASE_STEP`、`RELEASE_SESSIONS`、`TEARDOWN_REQUIRED`、
      `NEXT_COMMAND`。若缺任一字段，视为无效完成信号，要求 team-leader 重发。
   b. 执行本节末尾的「团队拆除标准动作（TEARDOWN）」；尤其在 in-process
      模式下，必须确认 `~/.claude/teams/<team_name>/` 与
      `~/.claude/tasks/<team_name>/` 两个目录均已消失，否则 CLI 面板仍会显示
      已取消的 agent。
      TEARDOWN 之后立即运行：
      ```bash
      ./scripts/cleanup_agentteam_metadata.py --yes --remove-team <team_name> --stale-only
      ```
   c. teardown 成功后，若 `NEXT_COMMAND` 为
      `TEARDOWN_ONLY_THEN_CREATE_B2_TEAM` 或
      `TEARDOWN_ONLY_THEN_CREATE_B3_TEAM`，立即创建下一 B 子步骤的全新 team。
      上一 team 的任何 member 都不得复用或继续存在。
   d. teardown 成功后，若 `NEXT_COMMAND` 是 shell 命令，则从仓库根目录运行该
      命令。例如 B3 后运行
      `./scripts/apply_agentteam_plan.py --advance && ./scripts/run_loop.sh`；
      F1 后运行 `./scripts/apply_f1_review.py && ./scripts/run_loop.sh`。

> **团队拆除标准动作（TEARDOWN）。** 拆除一个 team 必须按下列顺序，**判据是
> 磁盘上的 team/task 目录消失，而不是 `TeamDelete` 的返回值**：
>
> 1. **计算 teardown targets**：读取
>    `~/.claude/teams/<team_name>/config.json`。从 `members[]` 中排除主进程/
>    编排者，即满足任一条件的成员都**不是** shutdown target：
>    `agentId == leadAgentId`、`agentType == "team-lead"`、`name == "team-lead"`。
>    剩下的才是要释放的 project agents（例如 project-agent `team-leader`、
>    `math-theorist`、`numerical-debugger`、`flow-arch-reviewer`、
>    `orthogonal-direction-scout`）。B1/B3/F1 通常应等待 4 个 approval，B2
>    通常应等待 2 个 approval；绝不是等待包含主进程在内的 5/5。
> 2. **对每个 target 逐个发 `shutdown_request`**。必须用 `SendMessage` 的
>    structured object form，不能把 JSON 当字符串正文发送；否则 Claude Code 会报
>    `summary is required when message is a string` 或
>    `message text must not be a teammate protocol frame`，并且 teammate 不会真正退出。
>    示例：
>    ```yaml
>    to: "<member-name>"
>    summary: "Request AgentTeam shutdown"
>    message:
>      type: "shutdown_request"
>      request_id: "shutdown-<timestamp>@<member-name>"
>      reason: "AgentTeam phase complete; release this in-process teammate."
>    ```
>    这一步**不依赖当前会话的 team 上下文指针**，所以即使跨会话/compact 之后也能送达。
> 3. **等待结构化批准**：每个 target 必须通过 `SendMessage` 回复请求方：
>    ```yaml
>    summary: "Shutdown approved"
>    message:
>      type: "shutdown_response"
>      request_id: "<same request_id if present>"
>      approve: true
>      reason: "shutdown_request accepted"
>    ```
>    自然语言“收到/确认”不算完成；把 JSON 放进字符串正文也不算完成。没有
>    structured-object `shutdown_response.approve=true`，Claude Code
>    可能会继续把该 teammate 渲染为 idle。最多等待 30 秒；未批准者再次发送
>    `shutdown_request`，仍未批准则不要推进下一 team，提示需要人工处理或重启
>    Claude CLI。
> 4. 调用 `TeamDelete` 收尾。**注意它可能返回 `"No team name found"` 而 no-op**
>    （见下）——所以不能把它当判据。
> 5. 运行 metadata cleanup 兜底：
>    `./scripts/cleanup_agentteam_metadata.py --yes --remove-team <team_name> --stale-only`。
> 6. **验证拆除**：`ls -d ~/.claude/teams/<team_name> ~/.claude/tasks/<team_name>`。
>    - 两个目录都不存在 → 拆除成功，结束。
>    - 仍存在 → 先 `pgrep -fl -- '--agent-id'` 确认没有该 team 的残留进程
>      （tmux/iTerm 后端才会有；in-process 后端恒为空）；确认无进程后，
>      **`rm -rf ~/.claude/teams/<team_name> ~/.claude/tasks/<team_name>` 兜底删除**
>      元数据，再复查目录已消失。
>
> **为什么需要 rm 兜底（两种后端的故障各不相同）。**
> `TeamDelete` 是**纯元数据操作 + 依赖当前会话的 team 上下文指针**：它删除
> `~/.claude/teams/<team>/` 与 `~/.claude/tasks/<team>/`，并清掉会话里的 team
> 上下文；它**不会**终止任何 teammate。两种后端的残留方式不同：
> - **tmux / iTerm 后端**：每个 teammate 是**独立 `claude` 进程**
>   （`claude ... --agent-id <name>@<team>`），OS 父进程是它所在的 shell / iTerm2
>   分屏 pane。只有**收到 `shutdown_response.approve=true` 的 `shutdown_request`**
>   （或 kill / 关 pane）能结束它；
>   否则 `TeamDelete` 即便删了元数据，孤儿进程仍留在 iTerm2 pane 里、可被方向键
>   导航进入。`pgrep --agent-id` 兜底正是为这种后端。
> - **in-process 后端**（本部署默认 `teammateMode: in-process`）：teammate 没有
>   独立进程，作为 `local_workflow` 任务跑在编排者**同一进程内**，其 CLI 面板由
>   **磁盘上的 team 元数据 + 仍存活的 in-process task**渲染。`shutdown_request`
>   只有在 agent 用 `SendMessage` 返回 `shutdown_response.approve=true` 后才会让
>   任务退出；空 team 被回收后面板才消失。**致命陷阱**：若 team 是在**会话边界/compact 之前**建立的，
>   continuation 后的会话**不再持有指向它的上下文指针**，此时 `TeamDelete` 直接
>   返回 `"No team name found"` 并 **no-op**——既不报错也不删元数据，于是元数据
>   长期残留、CLI 每次启动都把它渲染成可切换的孤儿面板。`pgrep` 对它恒为空、毫无
>   帮助。**唯一可靠的清理 = 先按名 `shutdown_request` 每个非 lead target，并要求
>   `shutdown_response.approve=true`，再以目录消失为判据，目录仍在则 `rm -rf`
>   兜底。**

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
  Phase B): the orchestrator uses the **same in-process completion protocol as
  Phase B**（team-leader 自己 60 秒 polling；完成后发送 `[TEAM_COMPLETE]`
  + `NEXT_COMMAND`；主程序先按「团队拆除标准动作（TEARDOWN）」释放 session
  / 删除 team metadata，再执行命令）：
  1. **检查 team 唯一性**（一个阶段只有一个 team）
  2. `TeamCreate` a team (e.g. `phaseF1-<exp_name>`)
  3. Spawn `team-leader` together with the read-only specialists
     `math-theorist`, `numerical-debugger`, and `flow-arch-reviewer` as PEERS,
     in the background. Specialists `SendMessage` `[CONCLUSION]` to
     `team-leader`; main turn only receives one-line acks.
  4. **不要创建主程序常驻监控 cron**，也不要依赖 Stop hook 强制回主进程。
     等待 team-leader 的 `[TEAM_COMPLETE]` 信号。
  5. 收到 `[TEAM_COMPLETE]` 后，先对 F1 team 执行 TEARDOWN（确认
     `~/.claude/teams/<team>/`、`~/.claude/tasks/<team>/` 目录消失，目录残留则
     `rm -rf` 兜底），然后运行消息中的
     `NEXT_COMMAND: ./scripts/apply_f1_review.py && ./scripts/run_loop.sh`。
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
