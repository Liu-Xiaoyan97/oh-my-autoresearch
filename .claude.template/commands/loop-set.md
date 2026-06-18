# /loop-set

## 描述

从 `objective.json["model"]` 字典中读取各 subagent 对应的模型配置，直接写入
`.claude/agents/<name>.md` 的 `model:` 字段。

这是一个**一次性设置工具**——仅在你修改了 `objective.json` 的 model 映射后执行。
不参与循环迭代，不在 Phase 0 中调用。

## 用法

在 Claude Code 中运行 `/loop-set`。

## 行为

### 1. 执行 apply_model_config.sh

```bash
runtime/scripts/utils/apply_model_config.sh runtime
```

### 2. 验证结果

```read
.claude/agents/orthogonal-direction-scout.md
```

确认 `model:` 字段已更新为 `objective.json` 中配置的模型值。

## 约束

- ✅ 幂等可重复：仅首次运行时替换占位符，后续无占位符则跳过。
- ❌ 不修改 `objective.json` 本身。
- ❌ 不涉及任何 observer 事件或数据库操作。
