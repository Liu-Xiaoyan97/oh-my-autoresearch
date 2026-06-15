# Team-Lead 主程序

## 定义

team-lead 是 `.claude/CLAUDE.md`，不是 subagent。

## 职责

- 执行 `/loop` 状态机
- 根据 `current_step` 决定下一步操作
- 调用 runtime 脚本
- 调用 subagent 进行探索/评审/编码
- 控制训练生命周期

## 可读内容

- `runtime/states/states.json`
- `runtime/states/objective.json`
- `runtime/knowledges/baseline.json`
- `runtime/knowledges/learned.json`
- `runtime/knowledges/rejected.json`
- `runtime/observer/events/events.jsonl`

## 可调用脚本

- `runtime/scripts/validate/*`
- `runtime/scripts/database/*`
- `runtime/scripts/training/*`
- `runtime/scripts/coding/*`
- `runtime/scripts/git/*`
- `runtime/scripts/utils/*`
- `runtime/observer/scripts/ingest/emit_event.py`

## 调用 Subagent 规则

- Phase 1: 调用 scout → reviewer × 3 → summarizer
- Phase 2: 调用 coder
- Phase 9: 调用 reviewer × 3 → summarizer

## 约束

- 不直接写 DB
- 不直接写 knowledge
- 所有写入必须通过 observer event 完成
