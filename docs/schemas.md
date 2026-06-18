# Schemas

## 目录分布

| 目录 | 用途 |
|------|------|
| `.claude.template/schemas/` | team-lead 内部使用的阶段结果 schema |
| `runtime.template/schemas/` | runtime 数据文件的约束 schema |
| `runtime.template/observer/schemas/` | observer event 的 payload schema |
| `runtime.template/agents/*/schemas/` | subagent 输入/输出的 contract schema |

## .claude.template/schemas

| 文件 | 描述 |
|------|------|
| `phase0-validation.schema.json` | Phase 0 初始校验结果 |
| `phase1-exploration.schema.json` | Phase 1 方向探索阶段结果 |
| `phase3-training.schema.json` | Phase 3 训练阶段状态 |
| `phase9-recovery.schema.json` | Phase 9 经验回收结果 |
| `state-transition.schema.json` | 状态迁移事件 |
| `subagent-result.schema.json` | team-lead 接收 subagent 返回值的通用外壳 |
| `tool-result.schema.json` | team-lead 调用 runtime scripts 的统一结果格式 |

## runtime.template/schemas

| 文件 | 描述 |
|------|------|
| `state.schema.json` | 约束 `runtime/states/states.json` |
| `objective.schema.json` | 约束 `runtime/states/objective.json` |
| `baseline.schema.json` | 约束 `runtime/knowledges/baseline.json` |
| `learned.schema.json` | 约束 `runtime/knowledges/learned.json` |
| `rejected.schema.json` | 约束 `runtime/knowledges/rejected.json` |
| `experiment-row.schema.json` | 约束 experiments 表单行数据 |
| `exploration-row.schema.json` | 约束 exploration 表单行数据 |
| `validation-result.schema.json` | 约束 Phase 0 runtime validation 返回结果 |
| `training-progress.schema.json` | 约束训练监控解析结果 |
| `final-metrics.schema.json` | 约束训练完成后的最终指标 |
| `recovery-result.schema.json` | 约束经验回收判断结果 |
| `error.schema.json` | 统一错误结构 |

## runtime.template/observer/schemas

| 文件 | 描述 |
|------|------|
| `log-event.schema.json` | 约束 observations log 事件 payload |
| `experiments-write.schema.json` | 约束 experiments 表写入事件 payload |
| `exploration-write.schema.json` | 约束 exploration 表写入事件 payload |
| `knowledge-write.schema.json` | 约束 knowledge JSON 写入事件 payload |
| `candidate-pool-write.schema.json` | 约束候选方案详情写入事件 payload |

## schema 和脚本绑定关系

- `validate_schema.py` → 通用 JSON schema 校验
- `validate_states.py` → state.schema.json
- `validate_objective.py` → objective.schema.json
- `validate_baseline.py` → baseline.schema.json
- `validate_log_event.py` → log-event.schema.json
- `validate_experiments_write.py` → experiments-write.schema.json
- `validate_exploration_write.py` → exploration-write.schema.json
- `validate_knowledge_write.py` → knowledge-write.schema.json
- `validate_candidate_pool_write.py` → candidate-pool-write.schema.json
