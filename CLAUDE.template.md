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

2. `TeamCreate` a team (e.g. `team_name: "phaseB-<exp_name>"`).

3. Spawn the peers with the Agent tool, each with `team_name`, a `name`, and
   `run_in_background: true` so their output does NOT return into the main turn:
   - `team-leader` (`subagent_type: team-leader`, `name: "team-leader"`) — tell
     it which specialists to wait for this step and to write the debate file
     once all their conclusions arrive, then `SendMessage` the orchestrator
     the signal `"任务完成，解散团队"`.
   - each required specialist (`subagent_type` = its name, same `name`) — tell it
     to `SendMessage` its FULL conclusions to `team-leader` with the
     `[CONCLUSION] <agent-name>` format as the first line, and to return only a
     one-line ack to the orchestrator (no analysis content).

4. **创建主程序 cron 监控。** 在所有 peers 启动完毕后，立即创建一个 cron 任务
   用于监控 team 进度。**Cron 的职责仅是监控和发信号，不执行 shutdown、
   TeamDelete 或 phase 推进——这些由主程序在确认标记后负责。**
   使用 `CronCreate`：
   - `cron`: `1-59/2 * * * *`（每 2 分钟/120 秒，带偏移避免 :00/:30 拥堵）
   - `recurring`: true
   - 记录返回的 cron job ID（下文 prompt 中用 `<本cron_id>` 引用）。
   - `prompt`：

   ```
   你是 Phase B AgentTeam 的监控 cron。**你的职责仅是监控和发信号，
   不执行 shutdown、TeamDelete 或 phase 推进。这些由主程序负责。**

   ## 阶段 0：快速退出（已有待处理信号）
   1. 检查 `runtime/state/.cron_team_completed` 或
      `runtime/state/.cron_team_recreate` 是否存在。
      若任一存在 → 主程序尚未处理该信号，无需再监控。直接结束本次触发。

   ## 阶段 1：阶段校验（Phase Validation）
   1. 读取 `runtime/state/state.json`，记录当前 `phase`。
   2. 列出 `~/.claude/teams/` 下所有 team 目录。
   3. 确定当前阶段对应的预期 team 名称前缀：
      - Phase B 的子步骤（B1/B2/B3）→ team 名称以 `phaseB` 开头
      - Phase F1 → team 名称以 `phaseF1` 开头
   4. 对于每个 team 目录：
      - 若名称前缀不匹配当前阶段 → 陈旧 team
      - 向陈旧 team 的**所有成员**发送 `SendMessage {type:"shutdown_request", reason:"阶段不匹配，清理陈旧 team"}`
      - 执行 `TeamDelete`（若仍失败，记录并继续）
   5. 简要记录清理结果。

   ## 阶段 2：进度查询（保持耐心，不急于重启）
   1. 向 `team-leader` 发送进度查询：
      `SendMessage` to `"team-leader"` 内容：
      "请列出：(1) 已回传 [CONCLUSION] 的 agent 名称；
       (2) 尚未回传的 required agent 名称；
       (3) 你是否仍在等待。"
   2. 等待 team-leader 回复（60 秒内），无论是否回复都进入阶段 3——
      **在 20 分钟预算内不要因一次未回复就重启 team-leader 或重建 team**
      （保持耐心）。是否需要恢复，统一在阶段 3 按耗时判定。

   ## 阶段 3：完成检测 / 20 分钟超时恢复
   1. 若 team-leader 回复了 "任务完成，解散团队" 信号：
      **只创建标记文件，不做清理！**
      用 Write 工具创建 `runtime/state/.cron_team_completed`
      （内容为 team-leader 的完成消息原文）。本次结束。

   2. 否则计算耗时 = 现在 − max(team 创建时间, 上次重启时间)。
      上次重启时间读取 `runtime/state/.cron_patience_reset_at`（若不存在则用
      team 创建时间，取自 `~/.claude/teams/<team>/config.json`）。
      - **耗时 ≤ 20 分钟** → 保持耐心，本次结束，等待下次 cron 触发。
      - **耗时 > 20 分钟（超时恢复）**：
        a. 向 team-leader 发送重启询问：
           `SendMessage` to `"team-leader"` 内容：
           "已超过 20 分钟。请仅回复需要重启的 agent 名称列表（未回传
            [CONCLUSION] 或疑似卡死的）；若一切正常仍在推进，回复 '无'。"
        b. **team-leader 在 90 秒内应答**（team-leader 还活着）：
           - 对它点名的每个 agent，用 Agent 工具重新 spawn（相同 name、
             subagent_type、team_name），告知其重新发送 [CONCLUSION] 给
             team-leader。**team-leader 还在，绝不新建 team、绝不 TeamDelete。**
           - 用 Write 更新 `runtime/state/.cron_patience_reset_at` 为当前 ISO
             时间（重置 20 分钟预算，给恢复后的 team 新的耐心窗口）。
           - 简要记录重启了哪些 agent。本次结束。
        c. **team-leader 90 秒内无应答**（视为 team-leader 已崩溃）：
           - **不要自行 TeamDelete 或重启 team-leader。** 用 Write 工具创建
             `runtime/state/.cron_team_recreate`（内容："team-leader 无应答超过
             90 秒，需清空并重建 team"）。清空与重建由主程序执行。本次结束。
   ```

5. **主程序只与 team-leader 通讯。** 主程序（编排者）在任何时候都**不得**直接
   向 team 中的其他 agent（math-theorist、numerical-debugger、flow-arch-reviewer、
   orthogonal-direction-scout）发送消息或接收其分析内容。所有 team 内部通讯
   仅发生在 team-leader 与各 specialist 之间。主程序的 cron 监控执行上述
   增强 prompt——由 cron 自行查询 team-leader 和重启 agent，主程序不参与。

6. **`team-leader` 内部机制。** `team-leader` 在启动时创建自己的 60 秒轮询
   cron（使用 `CronCreate`），在 cron 触发时检查缺失的 specialist 并发送
   提醒。所有 specialist 回传 `[CONCLUSION]` 后，`team-leader` 取消轮询 cron
   （`CronDelete`），整理写入 debate 文件，然后向主程序发送
   `"任务完成，解散团队"`。

7. **主程序在每轮检查标记并执行清理。** 由于 stop hook 不再豁免主程序
   （phase=B 会阻止退出），主程序会持续循环。每次进入 Phase B 的 turn 中，
   主程序必须：

   1. 检查 `runtime/state/.cron_team_completed` 与
      `runtime/state/.cron_team_recreate` 是否存在

   2. **若 `.cron_team_completed` 存在** → team 已正常完成（team-leader 发出了
      "任务完成，解散团队"）：
      a. **向所有 team 成员发送 `shutdown_request`**
      b. **确认所有成员已退出**：向每个成员发送简短 ping
         （`SendMessage` 内容为 "."），已退出的 agent 会返回错误。
         对仍在运行的 agent，等待 5-10 秒后重试，最多重试 3 轮（约 30 秒）
      c. 执行 `TeamDelete`
      c2. **进程兜底扫描**：`TeamDelete` 只删元数据，本身不杀进程。删完后运行
          `pgrep -fl -- '--agent-id'`（或
          `ps aux | grep -- '--agent-id' | grep '@<team_name>'`）确认没有残留
          的 agent 进程；若仍有，按 pid 逐个 `kill` 后再继续。
      d. 删除 `runtime/state/.cron_team_completed`，并清理本阶段的恢复状态文件
         `runtime/state/.cron_patience_reset_at` 与
         `runtime/state/.cron_recreate_count`（若存在）
      e. 运行 `./scripts/apply_agentteam_plan.py --advance`
      f. 运行 `./scripts/run_loop.sh`

   3. **若 `.cron_team_recreate` 存在** → cron 判定 team-leader 已崩溃（无应答），
      需清空并重建整个 team。**这是唯一允许重建 team 的入口——前提是 team-leader
      已确认失联；只要 team-leader 还能应答就绝不走到这里。**
      a. **重建上限保护**：读取 `runtime/state/.cron_recreate_count`（不存在视为
         0）。若已 ≥ 2 → 重建两次仍失败，运行
         `./scripts/set_phase.sh BLOCKED C1`，
         block_reason="AgentTeam 反复重建仍失败：team-leader 多次崩溃"；删除
         `.cron_team_recreate`、`.cron_patience_reset_at`、`.cron_recreate_count`
         后运行 `./scripts/run_loop.sh`，本 turn 结束。
      b. 否则**清空旧 team**：向所有成员发 `shutdown_request` → 逐个 ping 确认
         退出（最多 3 轮）→ `TeamDelete` → `pgrep -fl -- '--agent-id'` 兜底
         `kill` 残留进程（拆除语义见下方说明）。
      c. 删除 `runtime/state/.cron_team_recreate` 与
         `runtime/state/.cron_patience_reset_at`（若存在）；把
         `runtime/state/.cron_recreate_count` 自增 1 写回。
      d. **重建 team**：按本节步骤 2–4 重新 `TeamCreate`（沿用同一 team 名）+
         spawn `team-leader` 与本步骤所需 specialists + 新建监控 cron。
      e. 本 turn 结束——不推进 phase，等待新 team 完成。

   4. **若两个标记都不存在** → team 仍在进行中（耐心等待，预算 20 分钟）：
      a. 检查 cron 是否仍在活跃（`CronList`）
      b. 若 cron 不存在或已失效 → 重新创建 cron（同步骤 4）
      c. 若 cron 存在 → **不做任何操作，直接结束本 turn。**
         Cron 每 2 分钟自行查询 team-leader 进度，并在超过 20 分钟时按"询问
         team-leader 重启哪些 agent / team-leader 无应答则发重建信号"恢复，
         主程序无需重复查询。

> **为什么必须先 shutdown_request + ping 确认，再 TeamDelete（拆除语义）。**
> `TeamDelete` 是**纯元数据操作**：它只删除 `~/.claude/teams/<team>/` 与
> `~/.claude/tasks/<team>/`，并清掉当前会话里的 team 上下文。它**不会**终止任何
> agent 进程。每个后台 agent 都是一个**独立的 `claude` 进程**
> （`claude ... --agent-id <name>@<team>`），其 OS 父进程是它自己所在的 shell /
> iTerm2 分屏 pane，而非编排者；`--parent-session-id` 只是逻辑链接。因此只有
> **被批准的 `shutdown_request`**（或直接 kill / 关闭 pane）才能真正结束它。
> 若跳过 c 步直接 `TeamDelete`：(1) 团队若仍有活跃成员，`TeamDelete` 会**失败**；
> (2) 即便删掉了元数据，残留的 agent 进程仍会以"孤儿"形式留在 iTerm2 里——可被
> 方向键导航进入、pane 不关闭。这正是先 ping 确认每个成员退出、再 `TeamDelete`、
> 最后 `pgrep` 兜底扫描的原因。

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
  Phase B): the orchestrator uses the **same protocols as Phase B**（包括
  增强版 cron prompt 中的阶段校验、Agent 异常恢复、完成检测三步流程，
  cron 只发信号不清理，主程序负责 shutdown + confirm + TeamDelete）：
  1. **检查 team 唯一性**（一个阶段只有一个 team）
  2. `TeamCreate` a team (e.g. `phaseF1-<exp_name>`)
  3. Spawn `team-leader` together with the read-only specialists
     `math-theorist`, `numerical-debugger`, and `flow-arch-reviewer` as PEERS,
     in the background. Specialists `SendMessage` `[CONCLUSION]` to
     `team-leader`; main turn only receives one-line acks.
  4. **创建主程序 cron 监控**（使用与 Phase B 相同的增强 prompt 模板，
     包含阶段校验 + 进度查询 + 20 分钟超时恢复三阶段，**同样保持 20 分钟耐心
     预算**：超时先问 team-leader 重启哪些 agent，team-leader 无应答才写
     `.cron_team_recreate` 让主程序清空+重建。注意：F1 的 apply 脚本是
     `./scripts/apply_f1_review.py` 而非 `--advance`；标记文件同为
     `runtime/state/.cron_team_completed` 与 `runtime/state/.cron_team_recreate`）
  5. **主程序只与 team-leader 通讯**，不直接联系其他 agent。
  6. **主程序检查标记**：
     - `.cron_team_completed` → 确认所有成员退出 → TeamDelete →
       运行 `./scripts/apply_f1_review.py` → `./scripts/run_loop.sh`；
     - `.cron_team_recreate` → team-leader 已崩溃：清空旧 team（shutdown +
       confirm + TeamDelete + pgrep 兜底）→ 重建同名 team（受 ≥2 次重建上限
       保护）→ 本 turn 结束等待新 team。**team-leader 还在则绝不重建。**
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
