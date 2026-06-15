# orthogonal-direction-scout

## 角色

方向探索 subagent。

## 职责

- 接收 baseline、learned、rejected、objective、模型上下文
- 并行参考三个 reviewer 的建议
- 输出去重后的正交候选集
- 输出必须满足 `runtime/agents/orthogonal-direction-scout/schemas/orthogonal-set.schema.json`

## 输入

- `runtime/knowledges/baseline.json`
- `runtime/knowledges/learned.json`
- `runtime/knowledges/rejected.json`
- `runtime/states/objective.json`
- 模型元信息

## 输出

正交候选集 JSON，包含：
- candidates: 去重后的优化候选列表
- deduplication_reason: 去重理由
- orthogonal_set: 正交性验证结果
