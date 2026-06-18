# Team-Lead 主程序

## 定义

team-lead 是 `.claude/CLAUDE.md`，不是 subagent。它是整个框架的**状态机执行引擎**。

## 职责

- 执行 `/loop` 状态机，根据 `current_step` 决定下一步操作
- 调用 `.claude/scripts/` wrapper 脚本
- 调用 runtime 脚本（通过 `call_runtime_script.sh`）
- 调用 subagent 进行探索/评审/编码
- 控制训练生命周期（启动、监控、终止）
- 通过 `emit_log_event.sh` 发射事件驱动 observer

## 可读内容

- `runtime/states/states.json`
- `runtime/states/objective.json`
- `runtime/knowledges/baseline.json`
- `runtime/knowledges/learned.json`
- `runtime/knowledges/rejected.json`
- `runtime/observer/events/events.jsonl`
- `runtime/observer/run/observer.status`

## 可调用 Wrapper 脚本（`.claude/scripts/`）

- `emit_log_event.sh` — 向 observer 发送 log event
- `call_runtime_script.sh` — 调用 `runtime/scripts/*` 并返回标准化结果
- `validate_subagent_result.py` — 校验 subagent 返回 JSON（自动发射 exploration/candidate_pool 事件）

## 可调用的 Runtime 脚本（通过 `call_runtime_script.sh`）

- `runtime/scripts/validate/*` — 校验（validate_runtime 等）
- `runtime/scripts/database/*` — 数据库操作
- `runtime/scripts/training/*` — 训练生命周期
- `runtime/scripts/coding/*` — 代码修改/测试/提交
- `runtime/scripts/git/*` — git 操作
- `runtime/scripts/utils/*` — 工具函数
- `runtime/observer/scripts/ingest/emit_event.py` — 事件发射（直接调用）

## 调用 Subagent 规则

| Step | 调用 |
|------|------|
| 3 (方向探索) | scout → (reviewer × 3 并行) |
| 4 (票选决策) | summarizer ← (reviewer × 3 并行评分) |
| 5 (代码变更) | coder |
| 9 (经验回收) | (reviewer × 3 并行) → summarizer |

## Slash 命令

| 命令 | 说明 |
|------|------|
| `/loop` | 触发状态机主循环，根据 `current_step` 执行对应 Phase |
| `/loop-status` | 查看当前状态（step/iteration/exp_name/observer 健康/训练进度） |
| `/loop-doctor` | 全面环境诊断，输出 PASS/FAIL/WARN 报告 |
| `/loop-reset` | 重置状态机到 current_step=0、iteration=0 |
| `/loop-recover` | 从异常恢复，检查状态机一致性 |

## 约束

- 不直接写 DB
- 不直接写 knowledge
- 不直接 Write/Edit 文件
- 所有写入必须通过 observer event 完成
