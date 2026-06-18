# /loop-set

## 描述

一次性设置工具。从 `objective.json` 中预解析 model、goal、poll_interval
三个配置项，分别写入对应位置。运行时不再调 resolve 脚本，直接读已解析文件。

仅在你修改了 `objective.json` 后执行。不参与循环迭代，不在 Phase 0 中调用。

## 用法

在 Claude Code 中运行 `/loop-set`。

## 行为

### 1. 填充 agent model 配置

```bash
runtime/scripts/utils/apply_model_config.sh runtime
```

将 `objective.json["model"]` 字典中各 subagent 对应的模型值写入
`.claude/agents/<name>.md` 的 `model:` 字段。幂等可重复。

### 2. 预解析 goal

```bash
runtime/scripts/utils/resolve_goal.sh runtime > runtime/states/resolved_goal.txt
```

将 `objective.json["goal"]` 解析为纯文本写入 `runtime/states/resolved_goal.txt`。

### 3. 预解析 poll_interval

```bash
runtime/scripts/utils/resolve_poll_interval.sh runtime > runtime/states/resolved_poll_interval.txt
```

将 `objective.json["poll_interval"]` 解析为纯数字写入
`runtime/states/resolved_poll_interval.txt`。

### 4. 验证结果

```read
.claude/agents/orthogonal-direction-scout.md
```
```read
runtime/states/resolved_goal.txt
```
```read
runtime/states/resolved_poll_interval.txt
```

确认三个配置均已正确解析。

## 运行时用法

| 配置 | `/loop-set` 写入位置 | 运行时读取方式 |
|------|----------------------|---------------|
| model | `.claude/agents/*.md` 的 `model:` 字段 | .md 定义直接生效，spawn 时不传 model 参数 |
| goal | `runtime/states/resolved_goal.txt` | `cat runtime/states/resolved_goal.txt` |
| poll_interval | `runtime/states/resolved_poll_interval.txt` | `cat runtime/states/resolved_poll_interval.txt` |

## 约束

- ✅ 幂等可重复。
- ❌ 不修改 `objective.json` 本身。
- ❌ 不涉及任何 observer 事件或数据库操作。
