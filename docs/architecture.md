# 系统架构

## 概述

`oh-my-autoresearch` 采用四层分离架构：team-lead 主程序、Observer Sidecar、Claude Code Subagents、Runtime 文件系统。

## 组件

### team-lead 主程序

- 位置：`.claude/CLAUDE.md`
- 职责：状态机执行、脚本调度、subagent 编排、训练控制
- 约束：不直接写 DB、不直接写 knowledge、不直接改 states

### Observer Sidecar

- 位置：`runtime/observer/`
- 职责：事件消费、DB 写入、知识管理、日志写入
- 约束：只读取自己的 events/offsets/config，不读项目源码、不参与推理、不调用 Claude tools

### Claude Code Subagents

- 位置：`.claude/agents/`
- 职责：方向探索、代码修改、架构/数学/数值评审、结果汇总
- 约束：只返回结构化 JSON，不写 runtime，不写 DB，不写日志

### Runtime 文件系统

- 位置：`runtime/`
- 包含：状态机状态、知识文件、Schema 契约、公共脚本、Observer

### SQLite 两表

```sql
CREATE TABLE experiments (
    exp_name TEXT PRIMARY KEY,
    ...
);

CREATE TABLE exploration (
    exp_name TEXT PRIMARY KEY,
    ...
);
```

### 事件流

```
team-lead → emit_event.py → events.jsonl → observer_daemon → dispatch → writers → DB/Knowledge
                                                                   失败 → deadletter.jsonl
                                                                   
7 种 event_type: state | log | experiments | exploration | knowledge | candidate_pool | control
```

### 状态机总览

```
0 (校验) → 1 (历史载入) → 2 (历史就绪) → 3 (方向探索) → 4 (票选决策) → 5 (代码变更)
    → 6 (远程同步) → 7 (训练启动) → 8 (训练结束) → 9 (经验回收) → 返回 Step 1
```
