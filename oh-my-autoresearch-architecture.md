# oh-my-autoresearch Submodule 文件架构说明

本文档用于指导 Claude Code 生成 `oh-my-autoresearch` 代码仓库。  
该仓库作为 git submodule 安装到真实 `research-runtime` 仓库中，提供 Claude Code 主程序、Subagents、Observer Sidecar、Runtime 模板、Schema 契约、公共脚本、测试与示例。

---

## 1. 总体设计原则

### 1.1 角色边界

```text
team-lead
    Claude Code 主程序，由 .claude/CLAUDE.md 定义。
    负责状态机、调度、脚本调用、subagent 调用、训练控制、远程同步。

observer
    独立 sidecar/plugin。
    随 team-lead 生命周期启动和停止。
    观察 team-lead、hooks、subagents、训练监控产生的事件。
    只写 observations、SQLite、knowledges。
    只读取自己的 runtime/observer/events 事件入口。

subagents
    Claude Code subagents。
    只定义在 .claude/agents/。
    不直接写 DB、不直接写日志、不直接改 states。
    返回结构化 JSON，由 team-lead 校验后继续推进流程。

runtime
    宿主仓库中的运行时目录。
    保存 states、objective、knowledge、logs、observations、db、observer 状态、schema、公共脚本。
```

### 1.2 目录边界

```text
.claude.template/
    Claude Code 安装目标模板。
    安装后复制/合并到宿主仓库 .claude/。
    包含 team-lead 主程序、subagents、commands、hooks、轻量 wrapper scripts。

runtime.template/
    Runtime 安装目标模板。
    安装后复制/合并到宿主仓库 runtime/。
    包含运行状态、知识文件、日志目录、数据库目录、observer、subagent schemas、公共执行器。

tests/
    测试 submodule 自身结构、schema、权限边界、observer sidecar、安装布局。

examples/
    给用户和 Claude Code 参考的最小样例，不作为运行态真实数据。
```

### 1.3 不应存在的目录或文件

```text
.claude.template/agents/team-lead.md      # team-lead 是主程序，不是 subagent
.claude.template/agents/observer.md       # observer 是 sidecar，不是 subagent
runtime.template/team-lead/               # team-lead 属于 .claude.template，不属于 runtime
runtime.template/artifacts/               # 当前设计不需要 artifacts
runtime.template/agents/*/scripts/        # subagents 不拥有 runtime scripts
runtime.template/scripts/observer/        # observer scripts 已独立在 runtime/observer/scripts
runtime.template/db/runtime.sqlite        # 数据库运行时生成
runtime.template/db/schema.sql            # 当前只需要 init_db.py 动态初始化
runtime.template/db/init_db.py            # init_db.py 放在 runtime/scripts/database/
src/                                      # 当前不是 Python package 架构
migrations/                               # 当前数据库只有两个表，不需要迁移目录
```

---

## 2. 最终目录树

```text
oh-my-autoresearch/
├── README.md
├── LICENSE
├── VERSION
├── manifest.json
├── pyproject.toml
├── .gitignore
│
├── install.sh
├── uninstall.sh
├── bootstrap.sh
├── upgrade.sh
├── doctor.sh
│
├── docs/
│   ├── architecture.md
│   ├── installation.md
│   ├── workflow.md
│   ├── state-machine.md
│   ├── team-lead.md
│   ├── observer-plugin.md
│   ├── subagents.md
│   ├── schemas.md
│   ├── scripts.md
│   └── troubleshooting.md
│
├── .claude.template/
│   ├── CLAUDE.md
│   ├── settings.json
│   ├── settings.local.example.json
│   │
│   ├── commands/
│   │   ├── loop.md
│   │   ├── loop-status.md
│   │   ├── loop-recover.md
│   │   ├── loop-reset.md
│   │   └── loop-doctor.md
│   │
│   ├── agents/
│   │   ├── orthogonal-direction-scout.md
│   │   ├── summarizer.md
│   │   ├── coder.md
│   │   ├── flow-arch-reviewer.md
│   │   ├── math-theorist.md
│   │   └── numerical-debugger.md
│   │
│   ├── schemas/
│   │   ├── phase0-validation.schema.json
│   │   ├── phase1-exploration.schema.json
│   │   ├── phase3-training.schema.json
│   │   ├── phase9-recovery.schema.json
│   │   ├── state-transition.schema.json
│   │   ├── subagent-result.schema.json
│   │   └── tool-result.schema.json
│   │
│   ├── scripts/
│   │   ├── emit_log_event.sh
│   │   ├── call_runtime_script.sh
│   │   └── validate_subagent_result.py
│   │
│   └── hooks/
│       ├── session-start.sh
│       ├── stop.sh
│       ├── pre-tool-use.sh
│       └── post-tool-use.sh
│
├── runtime.template/
│   ├── states/
│   │   ├── states.json
│   │   └── objective.example.json
│   │
│   ├── knowledges/
│   │   ├── baseline.json
│   │   ├── learned.json
│   │   └── rejected.json
│   │
│   ├── observations/
│   │   └── .gitkeep
│   │
│   ├── logs/
│   │   └── .gitkeep
│   │
│   ├── launchscripts/
│   │   └── .gitkeep
│   │
│   ├── db/
│   │   └── .gitkeep
│   │
│   ├── schemas/
│   │   ├── state.schema.json
│   │   ├── objective.schema.json
│   │   ├── baseline.schema.json
│   │   ├── learned.schema.json
│   │   ├── rejected.schema.json
│   │   ├── experiment-row.schema.json
│   │   ├── exploration-row.schema.json
│   │   ├── validation-result.schema.json
│   │   ├── training-progress.schema.json
│   │   ├── final-metrics.schema.json
│   │   ├── recovery-result.schema.json
│   │   └── error.schema.json
│   │
│   ├── observer/
│   │   ├── config.json
│   │   ├── events/
│   │   │   └── .gitkeep
│   │   ├── run/
│   │   │   └── .gitkeep
│   │   ├── offsets/
│   │   │   └── .gitkeep
│   │   ├── schemas/
│   │   │   ├── log-event.schema.json
│   │   │   ├── experiments-write.schema.json
│   │   │   ├── exploration-write.schema.json
│   │   │   └── knowledge-write.schema.json
│   │   └── scripts/
│   │       ├── lifecycle/
│   │       │   ├── start_observer.sh
│   │       │   ├── stop_observer.sh
│   │       │   ├── restart_observer.sh
│   │       │   └── healthcheck.sh
│   │       ├── ingest/
│   │       │   ├── emit_event.py
│   │       │   └── append_event.py
│   │       ├── validate/
│   │       │   ├── validate_log_event.py
│   │       │   ├── validate_experiments_write.py
│   │       │   ├── validate_exploration_write.py
│   │       │   └── validate_knowledge_write.py
│   │       ├── dispatch/
│   │       │   ├── observer_daemon.py
│   │       │   ├── consume_events.py
│   │       │   ├── dispatch_event.py
│   │       │   ├── load_offset.py
│   │       │   ├── save_offset.py
│   │       │   └── write_deadletter.py
│   │       └── writers/
│   │           ├── write_log.py
│   │           ├── write_experiments.py
│   │           ├── write_exploration.py
│   │           └── write_knowledge.py
│   │
│   ├── agents/
│   │   ├── orthogonal-direction-scout/
│   │   │   └── schemas/
│   │   │       ├── input.schema.json
│   │   │       ├── reviewer-proposal.schema.json
│   │   │       ├── candidate.schema.json
│   │   │       └── orthogonal-set.schema.json
│   │   ├── summarizer/
│   │   │   └── schemas/
│   │   │       ├── vote-input.schema.json
│   │   │       ├── vote.schema.json
│   │   │       ├── decision.schema.json
│   │   │       ├── recovery-analysis.schema.json
│   │   │       └── recovery-summary.schema.json
│   │   ├── coder/
│   │   │   └── schemas/
│   │   │       ├── coding-task.schema.json
│   │   │       ├── patch-plan.schema.json
│   │   │       ├── smoke-test.schema.json
│   │   │       ├── launch-script.schema.json
│   │   │       └── commit-result.schema.json
│   │   ├── flow-arch-reviewer/
│   │   │   └── schemas/
│   │   │       ├── proposal.schema.json
│   │   │       ├── vote.schema.json
│   │   │       └── recovery.schema.json
│   │   ├── math-theorist/
│   │   │   └── schemas/
│   │   │       ├── proposal.schema.json
│   │   │       ├── vote.schema.json
│   │   │       └── recovery.schema.json
│   │   └── numerical-debugger/
│   │       └── schemas/
│   │           ├── proposal.schema.json
│   │           ├── vote.schema.json
│   │           └── recovery.schema.json
│   │
│   └── scripts/
│       ├── validate/
│       │   ├── validate_schema.py
│       │   ├── validate_states.py
│       │   ├── validate_objective.py
│       │   ├── validate_baseline.py
│       │   ├── validate_runtime.py
│       │   └── validate_remote.py
│       ├── database/
│       │   ├── init_db.py
│       │   ├── ensure_experiment_row.py
│       │   ├── update_experiment_metric.py
│       │   ├── ensure_exploration_row.py
│       │   └── update_exploration_field.py
│       ├── git/
│       │   ├── check_clean.sh
│       │   ├── latest_commit.sh
│       │   └── sync_remote.sh
│       ├── training/
│       │   ├── generate_launch.sh
│       │   ├── start_training.sh
│       │   ├── monitor_training.py
│       │   ├── parse_train_log.py
│       │   └── terminate_training.sh
│       ├── coding/
│       │   ├── smoke_test.sh
│       │   ├── create_train_log.sh
│       │   └── commit_changes.sh
│       └── utils/
│           ├── atomic_write.py
│           ├── file_lock.py
│           ├── load_json.py
│           ├── save_json.py
│           ├── jsonl.py
│           ├── path_resolve.py
│           └── ssh_chain.py
│
├── tests/
│   ├── conftest.py
│   ├── test_manifest.py
│   ├── test_install_layout.py
│   ├── test_team_lead_main.py
│   ├── test_claude_template.py
│   ├── test_subagent_contracts.py
│   ├── test_observer_sidecar.py
│   ├── test_observer_events.py
│   ├── test_runtime_scripts.py
│   ├── test_schema_binding.py
│   ├── test_state_machine.py
│   ├── test_database.py
│   ├── test_runtime_validation.py
│   ├── test_permissions.py
│   └── fixtures/
│       ├── valid_runtime/
│       ├── invalid_runtime/
│       ├── valid_observer_events/
│       ├── invalid_observer_events/
│       ├── valid_subagent_outputs/
│       ├── invalid_subagent_outputs/
│       ├── valid_objectives/
│       ├── invalid_objectives/
│       └── mock_research_repo/
│
└── examples/
    ├── minimal-local/
    │   ├── README.md
    │   ├── objective.json
    │   ├── states.json
    │   └── baseline.json
    ├── remote-ssh-chain/
    │   ├── README.md
    │   ├── objective.json
    │   └── hosts.example.txt
    ├── observer-events/
    │   ├── log-event.json
    │   ├── experiments-write.json
    │   ├── exploration-write.json
    │   └── knowledge-write.json
    ├── subagent-outputs/
    │   ├── orthogonal-direction-scout.json
    │   ├── summarizer-decision.json
    │   ├── coder-commit-result.json
    │   ├── reviewer-proposal.json
    │   ├── reviewer-vote.json
    │   └── reviewer-recovery.json
    └── research-runtime-layout/
        ├── before-install.txt
        ├── after-install.txt
        └── README.md
```

---

## 3. 根目录文件说明

### `README.md`

项目总说明。应包含：

- 项目目的
- submodule 安装方式
- `/loop` 工作流简介
- team-lead / observer / subagents 职责
- 最小运行示例
- 常见问题链接

### `LICENSE`

开源许可证文件。

### `VERSION`

当前 submodule 版本，例如：

```text
0.1.0
```

### `manifest.json`

子模块安装清单。应声明：

- package name
- version
- required Claude template files
- required runtime template files
- install targets
- supported commands
- observer lifecycle hooks
- compatible runtime version

### `pyproject.toml`

用于 pytest、ruff、jsonschema 等开发依赖和测试配置。  
该项目不必作为完整 Python package 发布，但建议保留 `pyproject.toml` 统一测试工具配置。

### `.gitignore`

忽略运行时生成物，例如：

```text
runtime/db/*.sqlite
runtime/logs/*.log
runtime/observations/*.log
runtime/observer/events/*.jsonl
runtime/observer/offsets/*.offset
runtime/observer/run/*.pid
__pycache__/
.pytest_cache/
```

### `install.sh`

安装脚本。职责：

- 检查当前目录是否为宿主 `research-runtime` 仓库
- 复制或合并 `.claude.template/` 到宿主 `.claude/`
- 复制或合并 `runtime.template/` 到宿主 `runtime/`
- 不覆盖用户已有 `objective.json`、`states.json`、knowledge、logs、db
- 设置脚本执行权限
- 调用 `bootstrap.sh`

### `uninstall.sh`

卸载脚本。职责：

- 移除本 submodule 注入的 `.claude` commands、agents、hooks、scripts、schemas
- 可选择保留或移除 `runtime/observer`
- 默认不删除用户数据：`runtime/states`、`runtime/knowledges`、`runtime/db`、`runtime/logs`、`runtime/observations`

### `bootstrap.sh`

首次初始化脚本。职责：

- 创建缺失 runtime 目录
- 初始化 `runtime/db/runtime.sqlite`
- 创建 `events.jsonl`、`deadletter.jsonl`、`events.offset`
- 校验 schema 文件存在
- 确认 `.claude` 配置完整

### `upgrade.sh`

升级脚本。职责：

- 同步新增模板文件
- 更新 `.claude` commands、agents、hooks、schemas、scripts
- 更新 runtime scripts 和 schemas
- 不执行数据库迁移
- 不覆盖用户数据

### `doctor.sh`

环境诊断脚本。职责：

- 检查 Claude Code 配置是否完整
- 检查 runtime 目录是否完整
- 检查 observer 是否可启动
- 检查 SQLite 是否可写
- 检查 JSON schema 校验工具是否可用
- 检查 git、ssh、python 环境

---

## 4. `docs/` 文件说明

### `docs/architecture.md`

系统架构说明。应包含：

- team-lead 主程序
- observer sidecar
- Claude Code subagents
- runtime 文件系统
- SQLite 两表
- 事件流
- 状态机总览

### `docs/installation.md`

安装说明。应包含：

- 作为 git submodule 添加方式
- 运行 `install.sh`
- 初始化 objective
- 首次运行 `/loop`

### `docs/workflow.md`

完整 Phase 工作流说明。应覆盖：

- Phase 0 初始校验
- Phase 1 方向探索
- Phase 3 训练监控
- Phase 9 经验回收
- 回退逻辑
- loss 爆炸逻辑

### `docs/state-machine.md`

状态机说明。应包含：

- `current_step`
- `next_step`
- checkpoint 1-9
- 每个状态的入口、出口、写入目标

### `docs/team-lead.md`

team-lead 主程序说明。应包含：

- team-lead 是 `.claude/CLAUDE.md`
- 可读内容
- 可调用脚本
- 调用 subagent 规则
- 不直接写 DB / knowledge 的约束

### `docs/observer-plugin.md`

Observer 插件说明。应包含：

- 生命周期
- events JSONL
- offsets
- deadletter
- 四类 schema
- 四类 writer
- 不读取项目源码、不参与推理、不调用 Claude tools

### `docs/subagents.md`

Subagents 说明。应包含：

- 每个 subagent 的职责
- 输入上下文
- 输出 schema
- 不直接写 runtime 的约束

### `docs/schemas.md`

Schema 说明。应包含：

- `.claude.template/schemas`
- `runtime.template/schemas`
- `runtime.template/observer/schemas`
- `runtime.template/agents/*/schemas`
- schema 和脚本绑定关系

### `docs/scripts.md`

脚本说明。应包含：

- `.claude.template/scripts` wrapper
- observer scripts
- runtime public scripts
- 脚本调用链
- 禁止绕过 Observer 写 DB 的规则

### `docs/troubleshooting.md`

故障排查文档。应覆盖：

- observer 未启动
- events 积压
- schema 校验失败
- SQLite 写入失败
- baseline 不完整
- git dirty
- ssh chain 失败
- training log 无法解析

---

## 5. `.claude.template/` 文件说明

### `.claude.template/CLAUDE.md`

team-lead 主程序定义。  
安装后成为宿主仓库 `.claude/CLAUDE.md`。

应包含：

- team-lead 的职责
- `/loop` 状态机执行规则
- 只读/调用工具边界
- subagent 调用顺序
- observer event emit 规则
- 任何 DB/knowledge/log 写入必须通过 observer event 完成

### `.claude.template/settings.json`

Claude Code 项目设置。应包含：

- hook 配置
- permission policy
- allowed tools
- denied tools
- observer 生命周期 hook 绑定

### `.claude.template/settings.local.example.json`

本机私有设置样例。  
不应安装为真实 `settings.local.json`，只作为用户参考。

---

## 6. `.claude.template/commands/` 文件说明

### `loop.md`

`/loop` 主命令。  
触发完整状态机执行。

### `loop-status.md`

`/loop-status` 命令。  
读取当前状态、最近日志、observer 健康状态、训练状态摘要。

### `loop-recover.md`

`/loop-recover` 命令。  
用于从异常状态恢复，例如训练启动失败、observer 中断、状态机不一致。

### `loop-reset.md`

`/loop-reset` 命令。  
将状态机重置为：

```json
{
  "current_step": 0,
  "next_step": 1
}
```

应谨慎使用。

### `loop-doctor.md`

`/loop-doctor` 命令。  
触发环境诊断，等价于通过 Claude 调用 `doctor.sh` 和相关 runtime validate scripts。

---

## 7. `.claude.template/agents/` 文件说明

### `orthogonal-direction-scout.md`

方向探索 subagent。职责：

- 接收 baseline、learned、rejected、objective、模型上下文
- 并行参考三个 reviewer 的建议
- 输出去重后的正交候选集
- 输出必须满足 `runtime/agents/orthogonal-direction-scout/schemas/orthogonal-set.schema.json`

### `summarizer.md`

汇总与投票 subagent。职责：

- Phase 1：汇总候选集和三方评分，输出最高票决策
- Phase 9：汇总三方训练结果分析，输出经验回收总结
- 输出必须满足 `decision.schema.json` 或 `recovery-summary.schema.json`

### `coder.md`

代码修改 subagent。职责：

- 根据 summarizer 的 decision 修改研究仓库代码
- 生成 patch plan
- 执行冒烟测试
- 调用 runtime coding/training/git 脚本
- 输出 commit result

### `flow-arch-reviewer.md`

架构评审 subagent。职责：

- 从模型结构、数据流、模块边界角度提出优化候选
- 对候选方案评分
- Phase 9 从架构角度总结经验或教训

### `math-theorist.md`

数学理论 subagent。职责：

- 从目标函数、正则化、优化理论、表示空间角度提出候选
- 对候选方案评分
- Phase 9 从数学角度总结经验或教训

### `numerical-debugger.md`

数值调试 subagent。职责：

- 从 loss、梯度、初始化、归一化、精度、爆炸/消失等数值角度提出候选
- 对候选方案评分
- Phase 9 从数值稳定性角度总结经验或教训

---

## 8. `.claude.template/schemas/` 文件说明

### `phase0-validation.schema.json`

定义 Phase 0 初始校验结果。  
应包含：

- states 校验结果
- objective 校验结果
- baseline 完整性
- remote/ssh 校验结果
- git clean 检查结果
- pass/fail
- error messages

### `phase1-exploration.schema.json`

定义 Phase 1 方向探索阶段的结构化结果。  
应覆盖：

- loaded knowledge summary
- orthogonal candidates
- votes
- decision
- commit result

### `phase3-training.schema.json`

定义训练阶段结构化状态。  
应覆盖：

- launch script
- PID
- latest train step
- latest train loss
- latest val step
- latest primary metric
- failure status
- completion status

### `phase9-recovery.schema.json`

定义经验回收阶段结构化结果。  
应覆盖：

- final metrics
- baseline comparison
- recovery analyses
- recovery summary
- target knowledge file

### `state-transition.schema.json`

定义状态迁移事件。  
应包含：

- exp_name
- previous current_step / next_step
- new current_step / next_step
- checkpoint
- reason

### `subagent-result.schema.json`

定义 team-lead 接收 subagent 返回值的通用外壳。  
应包含：

- agent_name
- phase
- status
- payload_schema
- payload
- error

### `tool-result.schema.json`

定义 team-lead 调用 runtime scripts 或工具后的统一结果格式。  
应包含：

- command
- exit_code
- stdout
- stderr
- status
- parsed_payload

---

## 9. `.claude.template/scripts/` 文件说明

### `emit_log_event.sh`

轻量 wrapper。  
用于 team-lead 向 observer 发送 log event。  
实际应调用：

```text
runtime/observer/scripts/ingest/emit_event.py
```

### `call_runtime_script.sh`

轻量 wrapper。  
用于 team-lead 调用：

```text
runtime/scripts/*
```

应负责：

- 解析 runtime 根目录
- 标准化 stdout/stderr
- 返回统一 tool-result JSON

### `validate_subagent_result.py`

校验 subagent 返回 JSON。  
应根据 agent 名称和阶段选择：

```text
runtime/agents/<agent>/schemas/*.schema.json
```

---

## 10. `.claude.template/hooks/` 文件说明

### `session-start.sh`

Claude Code session 启动时执行。职责：

- 启动 observer sidecar
- 初始化 observer events、offsets、run 目录
- 发出 session start log event

### `stop.sh`

Claude Code session 停止时执行。职责：

- 发出 session stop log event
- 停止 observer sidecar
- 清理 `runtime/observer/run/observer.pid`

### `pre-tool-use.sh`

工具调用前执行。职责：

- 记录 tool pre-use event
- 不阻塞正常工具执行，除非权限策略明确拒绝

### `post-tool-use.sh`

工具调用后执行。职责：

- 记录 tool post-use event
- 可记录 exit code、耗时、工具名称、简要结果

---

## 11. `runtime.template/states/` 文件说明

### `states.json`

状态机当前状态。初始值：

```json
{
  "current_step": 0,
  "next_step": 1,
  "iteration": 0,
  "exp_name": "exp_0"
}
```

### `objective.example.json`

优化目标模板。用户应复制为：

```text
runtime/states/objective.json
```

应包含：

- goal
- primary_metrics.name
- primary_metrics.mode
- project_root
- command
- remote
- hosts
- num_training_steps
- eval_n_steps
- devices

---

## 12. `runtime.template/knowledges/` 文件说明

### `baseline.json`

当前基线方法记录。  
由 observer 在 Phase 9 中更新。

### `learned.json`

有效或持平方法的经验记录。  
由 observer 追加。

### `rejected.json`

无效或劣于 baseline 的方法记录。  
由 observer 追加。

---

## 13. Runtime 日志与输出目录说明

### `runtime.template/observations/.gitkeep`

占位目录。运行时生成：

```text
runtime/observations/<exp_name>.log
```

格式：

```text
[YYYY-MM-DD HH:MM:SS]|[LEVEL]-{Message}
```

### `runtime.template/logs/.gitkeep`

训练日志目录。运行时生成：

```text
runtime/logs/train-of-<exp_name>.log
```

### `runtime.template/launchscripts/.gitkeep`

训练脚本输出目录。运行时生成：

```text
runtime/launchscripts/launch_<exp_name>.sh
```

### `runtime.template/db/.gitkeep`

数据库目录。运行时生成：

```text
runtime/db/runtime.sqlite
```

数据库只包含两个表：

```text
experiments
exploration
```

---

## 14. `runtime.template/schemas/` 文件说明

### `state.schema.json`

约束 `runtime/states/states.json`。

### `objective.schema.json`

约束 `runtime/states/objective.json`。

### `baseline.schema.json`

约束 `runtime/knowledges/baseline.json`。

### `learned.schema.json`

约束 `runtime/knowledges/learned.json`。

### `rejected.schema.json`

约束 `runtime/knowledges/rejected.json`。

### `experiment-row.schema.json`

约束 experiments 表单行数据结构。

### `exploration-row.schema.json`

约束 exploration 表单行数据结构。

### `validation-result.schema.json`

约束 Phase 0 runtime validation 返回结果。

### `training-progress.schema.json`

约束训练监控解析结果：

```json
{
  "train_step": 1000,
  "train_loss": 0.123,
  "val_step": 1000,
  "val_metric": 0.812
}
```

### `final-metrics.schema.json`

约束训练完成后的最终指标结果。

### `recovery-result.schema.json`

约束经验回收判断结果。

### `error.schema.json`

统一错误结构。

---

## 15. `runtime.template/observer/` 文件说明

### `config.json`

Observer 配置。应包含：

- runtime root
- events path
- offsets path
- run path
- schemas path
- observations path
- db path
- knowledges path
- poll interval
- deadletter path

### `events/.gitkeep`

事件入口目录占位。运行时生成：

```text
runtime/observer/events/events.jsonl
runtime/observer/events/deadletter.jsonl
```

### `run/.gitkeep`

运行状态目录占位。运行时生成：

```text
runtime/observer/run/observer.pid
```

### `offsets/.gitkeep`

消费进度目录占位。运行时生成：

```text
runtime/observer/offsets/events.offset
```

---

## 16. `runtime.template/observer/schemas/` 文件说明

### `log-event.schema.json`

约束写入 observations log 的事件 payload。  
字段应包含：

- exp_name
- timestamp
- level
- source
- message

### `experiments-write.schema.json`

约束写入 experiments 表的事件 payload。  
应支持：

- insert_experiment
- update_metric
- mark_complete

### `exploration-write.schema.json`

约束写入 exploration 表的事件 payload。  
应支持：

- insert_exploration
- update_orthogonal_candidates
- update_decision
- update_commit

### `knowledge-write.schema.json`

约束写入 knowledge JSON 的事件 payload。  
应支持：

- update_baseline
- append_learned
- append_rejected

---

## 17. `runtime.template/observer/scripts/` 文件说明

### `lifecycle/start_observer.sh`

启动 observer daemon。职责：

- 检查是否已有 pid
- 初始化 events、deadletter、offset
- 后台启动 `dispatch/observer_daemon.py`
- 写入 `run/observer.pid`

### `lifecycle/stop_observer.sh`

停止 observer daemon。职责：

- 读取 pid
- 发送 SIGTERM
- 等待退出
- 清理 pid

### `lifecycle/restart_observer.sh`

重启 observer。  
可选脚本，可调用 stop 再 start。

### `lifecycle/healthcheck.sh`

检查 observer 健康状态：

- pid 是否存在
- 进程是否存活
- events 是否可写
- db 是否可写
- observations 是否可写
- knowledges 是否可写

### `ingest/emit_event.py`

事件入口。职责：

- 接收 event_type 和 payload
- 补充 event_id、created_at
- 调用 `append_event.py`

### `ingest/append_event.py`

追加事件到：

```text
runtime/observer/events/events.jsonl
```

应使用文件锁，保证并发安全。

### `validate/validate_log_event.py`

校验 log event payload。

### `validate/validate_experiments_write.py`

校验 experiments write payload。

### `validate/validate_exploration_write.py`

校验 exploration write payload。

### `validate/validate_knowledge_write.py`

校验 knowledge write payload。

### `dispatch/observer_daemon.py`

Observer 主进程。职责：

- 读取 config
- 加载 offset
- 轮询或 tail events.jsonl
- 消费新事件
- 调用 dispatch_event
- 成功后保存 offset
- 失败后写 deadletter

### `dispatch/consume_events.py`

根据 offset 从 events.jsonl 中读取未消费事件。

### `dispatch/dispatch_event.py`

根据 event_type 分发：

```text
log          -> writers/write_log.py
experiments  -> writers/write_experiments.py
exploration  -> writers/write_exploration.py
knowledge    -> writers/write_knowledge.py
```

### `dispatch/load_offset.py`

读取当前消费偏移。

### `dispatch/save_offset.py`

保存当前消费偏移。

### `dispatch/write_deadletter.py`

写入失败事件到：

```text
runtime/observer/events/deadletter.jsonl
```

### `writers/write_log.py`

写入：

```text
runtime/observations/<exp_name>.log
```

格式：

```text
[YYYY-MM-DD HH:MM:SS]|[LEVEL]-{Message}
```

### `writers/write_experiments.py`

写入 experiments 表。  
可调用 `runtime/scripts/database/*` helper，但外部入口必须仍然是 observer event。

### `writers/write_exploration.py`

写入 exploration 表。  
可调用 `runtime/scripts/database/*` helper。

### `writers/write_knowledge.py`

写入 baseline / learned / rejected JSON。  
必须使用原子写，避免 JSON 损坏。

---

## 18. `runtime.template/agents/` 文件说明

该目录只保存 subagent runtime contract schemas。  
不保存 scripts、不保存 inbox/outbox、不保存运行态中间结果。

### `orthogonal-direction-scout/schemas/input.schema.json`

约束 direction scout 输入上下文。

### `orthogonal-direction-scout/schemas/reviewer-proposal.schema.json`

约束三个 reviewer 返回给 scout 的原始提案。

### `orthogonal-direction-scout/schemas/candidate.schema.json`

约束单个优化候选。

### `orthogonal-direction-scout/schemas/orthogonal-set.schema.json`

约束去重后的正交候选集。

### `summarizer/schemas/vote-input.schema.json`

约束 summarizer 给 reviewer 的投票输入。

### `summarizer/schemas/vote.schema.json`

约束 reviewer 的评分输出。

### `summarizer/schemas/decision.schema.json`

约束最终票选方法。

### `summarizer/schemas/recovery-analysis.schema.json`

约束 Phase 9 中 reviewer 的经验/教训分析。

### `summarizer/schemas/recovery-summary.schema.json`

约束 Phase 9 summarizer 汇总结果。

### `coder/schemas/coding-task.schema.json`

约束 coder 接收的编码任务。

### `coder/schemas/patch-plan.schema.json`

约束 coder 生成的修改计划。

### `coder/schemas/smoke-test.schema.json`

约束冒烟测试结果。

### `coder/schemas/launch-script.schema.json`

约束训练脚本生成结果。

### `coder/schemas/commit-result.schema.json`

约束 git commit 结果。

### `flow-arch-reviewer/schemas/proposal.schema.json`

约束架构 reviewer 的候选提案。

### `flow-arch-reviewer/schemas/vote.schema.json`

约束架构 reviewer 的投票结果。

### `flow-arch-reviewer/schemas/recovery.schema.json`

约束架构 reviewer 的经验回收分析。

### `math-theorist/schemas/proposal.schema.json`

约束数学 reviewer 的候选提案。

### `math-theorist/schemas/vote.schema.json`

约束数学 reviewer 的投票结果。

### `math-theorist/schemas/recovery.schema.json`

约束数学 reviewer 的经验回收分析。

### `numerical-debugger/schemas/proposal.schema.json`

约束数值 reviewer 的候选提案。

### `numerical-debugger/schemas/vote.schema.json`

约束数值 reviewer 的投票结果。

### `numerical-debugger/schemas/recovery.schema.json`

约束数值 reviewer 的经验回收分析。

---

## 19. `runtime.template/scripts/` 文件说明

### `validate/validate_schema.py`

通用 JSON schema 校验器。

### `validate/validate_states.py`

校验 `runtime/states/states.json`。

### `validate/validate_objective.py`

校验 `runtime/states/objective.json`。

### `validate/validate_baseline.py`

校验 baseline 是否完整。  
应检查 experiments 表中 baseline 是否包含完整评估字段。

### `validate/validate_runtime.py`

Phase 0 综合校验入口。  
应调用 states、objective、baseline、remote 等校验。

### `validate/validate_remote.py`

校验 remote 训练配置。  
包括 hosts 非空和 ssh chain 可达。

### `database/init_db.py`

初始化 SQLite。  
只创建两个表：

```text
experiments
exploration
```

### `database/ensure_experiment_row.py`

保证 experiments 表中存在某个 exp_name 行。

### `database/update_experiment_metric.py`

更新 experiments 表中某个 step 的 metric。

### `database/ensure_exploration_row.py`

保证 exploration 表中存在某个 exp_name 行。

### `database/update_exploration_field.py`

更新 exploration 表中的：

- orthogonal-direction-scout
- decision
- commit

### `git/check_clean.sh`

检查宿主研究仓库是否存在未提交变动。

### `git/latest_commit.sh`

返回当前仓库最近一次 commit id。

### `git/sync_remote.sh`

根据 objective hosts 配置同步远端代码。

### `training/generate_launch.sh`

生成：

```text
runtime/launchscripts/launch_<exp_name>.sh
```

### `training/start_training.sh`

通过 nohup 启动训练：

```text
nohup runtime/launchscripts/launch_<exp_name>.sh > runtime/logs/train-of-<exp_name>.log 2>&1 &
```

返回 PID。

### `training/monitor_training.py`

监控训练日志，输出最近训练进度和最近验证记录。

### `training/parse_train_log.py`

纯日志解析器。  
不写状态、不写 DB。

### `training/terminate_training.sh`

安全终止训练进程组：

```bash
kill -- -$(ps -o pgid= -p <PID> | tr -d ' ')
```

### `coding/smoke_test.sh`

运行最小冒烟测试，确认代码修改不会立即失败。

### `coding/create_train_log.sh`

创建：

```text
runtime/logs/train-of-<exp_name>.log
```

### `coding/commit_changes.sh`

执行 git add / commit。  
返回 commit id。  
commit id 后续通过 observer 写入 exploration 表。

### `utils/atomic_write.py`

原子写文件工具。

### `utils/file_lock.py`

文件锁工具。

### `utils/load_json.py`

读取 JSON 工具。

### `utils/save_json.py`

保存 JSON 工具。

### `utils/jsonl.py`

JSONL 读写工具。

### `utils/path_resolve.py`

路径解析工具。

### `utils/ssh_chain.py`

按 hosts 链式 SSH 检查和执行工具。

---

## 20. `tests/` 文件说明

### `conftest.py`

pytest 公共 fixture。

### `test_manifest.py`

测试 manifest 是否完整。

### `test_install_layout.py`

测试安装后 `.claude/` 和 `runtime/` 布局是否正确。

### `test_team_lead_main.py`

测试 team-lead 是 `.claude/CLAUDE.md` 主程序，而不是 subagent。

### `test_claude_template.py`

测试 `.claude.template` 包含 commands、agents、hooks、schemas、scripts。

### `test_subagent_contracts.py`

测试 runtime/agents 只包含 schemas，不包含 scripts。

### `test_observer_sidecar.py`

测试 observer 是 sidecar，不是 subagent，且包含 events、offsets、run、schemas、scripts。

### `test_observer_events.py`

测试四类 observer event schema。

### `test_runtime_scripts.py`

测试 runtime scripts 目录结构和脚本归属。

### `test_schema_binding.py`

测试 schema 与 scripts 的绑定关系。

### `test_state_machine.py`

测试 current_step / next_step 迁移规则。

### `test_database.py`

测试 SQLite 只包含 experiments 和 exploration 两张表。

### `test_runtime_validation.py`

测试 Phase 0 校验逻辑。

### `test_permissions.py`

测试权限边界：

- team-lead 不直接写 DB / knowledge
- observer 不读取项目源码
- subagents 不写 runtime
- DB 写入必须通过 observer event

### `tests/fixtures/valid_runtime/`

合法 runtime 样例。

### `tests/fixtures/invalid_runtime/`

非法 runtime 样例。

### `tests/fixtures/valid_observer_events/`

合法 observer event 样例。

### `tests/fixtures/invalid_observer_events/`

非法 observer event 样例。

### `tests/fixtures/valid_subagent_outputs/`

合法 subagent 输出样例。

### `tests/fixtures/invalid_subagent_outputs/`

非法 subagent 输出样例。

### `tests/fixtures/valid_objectives/`

合法 objective 配置样例。

### `tests/fixtures/invalid_objectives/`

非法 objective 配置样例。

### `tests/fixtures/mock_research_repo/`

模拟宿主研究仓库，用于安装和 git 测试。

---

## 21. `examples/` 文件说明

### `examples/minimal-local/README.md`

本地最小运行示例说明。

### `examples/minimal-local/objective.json`

本地训练 objective 示例。

### `examples/minimal-local/states.json`

初始 states 示例。

### `examples/minimal-local/baseline.json`

baseline 示例。

### `examples/remote-ssh-chain/README.md`

远程训练示例说明。

### `examples/remote-ssh-chain/objective.json`

remote=True 的 objective 示例。

### `examples/remote-ssh-chain/hosts.example.txt`

hosts 链式 SSH 示例。

### `examples/observer-events/log-event.json`

log event 示例。

### `examples/observer-events/experiments-write.json`

experiments 写入事件示例。

### `examples/observer-events/exploration-write.json`

exploration 写入事件示例。

### `examples/observer-events/knowledge-write.json`

knowledge 写入事件示例。

### `examples/subagent-outputs/orthogonal-direction-scout.json`

direction scout 输出示例。

### `examples/subagent-outputs/summarizer-decision.json`

summarizer decision 输出示例。

### `examples/subagent-outputs/coder-commit-result.json`

coder commit result 输出示例。

### `examples/subagent-outputs/reviewer-proposal.json`

reviewer proposal 输出示例。

### `examples/subagent-outputs/reviewer-vote.json`

reviewer vote 输出示例。

### `examples/subagent-outputs/reviewer-recovery.json`

reviewer recovery 输出示例。

### `examples/research-runtime-layout/before-install.txt`

安装前宿主仓库结构示例。

### `examples/research-runtime-layout/after-install.txt`

安装后宿主仓库结构示例。

### `examples/research-runtime-layout/README.md`

安装布局说明。

---

## 22. 安装后的宿主仓库结构

安装到 `research-runtime` 后，目标结构应为：

```text
research-runtime/
├── agent-system/
│   └── oh-my-autoresearch/        # git submodule
│
├── .claude/
│   ├── CLAUDE.md
│   ├── settings.json
│   ├── settings.local.example.json
│   ├── commands/
│   ├── agents/
│   ├── schemas/
│   ├── scripts/
│   └── hooks/
│
├── runtime/
│   ├── states/
│   ├── knowledges/
│   ├── observations/
│   ├── logs/
│   ├── launchscripts/
│   ├── db/
│   ├── schemas/
│   ├── observer/
│   ├── agents/
│   └── scripts/
│
└── <research code>
```

---

## 23. 关键实现约束

### 23.1 DB 写入必须经过 Observer

禁止：

```text
team-lead -> runtime/scripts/database/update_experiment_metric.py
```

应当：

```text
team-lead -> emit observer event
observer -> write_experiments.py
observer -> runtime/scripts/database/update_experiment_metric.py
```

### 23.2 Knowledge 写入必须经过 Observer

禁止：

```text
team-lead 直接修改 baseline.json / learned.json / rejected.json
```

应当：

```text
team-lead -> knowledge event
observer -> write_knowledge.py
```

### 23.3 Subagent 不拥有 runtime scripts

禁止：

```text
runtime/agents/<agent>/scripts/
```

Subagent 只返回结构化 JSON，由 team-lead 校验。

### 23.4 Observer 只读取自己的 events

Observer 可以读取：

```text
runtime/observer/events/events.jsonl
runtime/observer/offsets/events.offset
runtime/observer/config.json
runtime/observer/schemas/*
```

Observer 不应读取：

```text
runtime/states/objective.json
runtime/states/states.json
project source code
training source code
```

### 23.5 Runtime 生成物不进入模板

模板中只保留 `.gitkeep`。运行时生成：

```text
runtime/db/runtime.sqlite
runtime/observer/events/events.jsonl
runtime/observer/events/deadletter.jsonl
runtime/observer/offsets/events.offset
runtime/observer/run/observer.pid
runtime/logs/train-of-<exp_name>.log
runtime/launchscripts/launch_<exp_name>.sh
runtime/observations/<exp_name>.log
```

---

## 24. 给 Claude Code 的实现顺序建议

建议按下面顺序生成代码仓库：

```text
1. 创建目录和空文件
2. 实现 manifest.json
3. 实现 runtime schemas
4. 实现 observer schemas
5. 实现 subagent schemas
6. 实现 runtime/scripts/utils
7. 实现 runtime/scripts/database
8. 实现 observer ingest/dispatch/writers
9. 实现 runtime/scripts/validate
10. 实现 runtime/scripts/git/training/coding
11. 实现 .claude.template/CLAUDE.md
12. 实现 .claude.template/agents/*
13. 实现 .claude.template/hooks/*
14. 实现 install/bootstrap/doctor/upgrade/uninstall
15. 实现 tests
16. 实现 examples
17. 运行 pytest 和 doctor
```
