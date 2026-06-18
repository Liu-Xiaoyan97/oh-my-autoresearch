# Scripts

## 脚本分类

### .claude.template/scripts (Wrapper)

| 脚本 | 用途 |
|------|------|
| `emit_log_event.sh` | team-lead 向 observer 发送 log event，调用 `runtime/observer/scripts/ingest/emit_event.py` |
| `call_runtime_script.sh` | team-lead 调用 `runtime/scripts/*`，解析 runtime 根目录，标准化 stdout/stderr，返回统一 tool-result JSON |
| `validate_subagent_result.py` | 校验 subagent 返回 JSON，根据 agent 名称选择对应 schema；自动发射 exploration 和 candidate_pool 事件 |

### Hook 脚本

| 脚本 | 用途 |
|------|------|
| `session-start.sh` | session 启动时自动执行：模板解析、observer 启动 |
| `pre-tool-use.sh` | 每次 tool 调用前执行，8 道守卫拦截违规操作（直接写 states.json、调 observer 脚本等） |
| `post-tool-use.sh` | 每次 tool 调用后执行，清理或记录 |
| `stop.sh` | session 结束时清理 observer 进程 |

### Observer Scripts

| 目录 | 脚本 | 用途 |
|------|------|------|
| lifecycle | `start_observer.sh` | 启动 observer daemon |
| lifecycle | `stop_observer.sh` | 停止 observer daemon |
| lifecycle | `restart_observer.sh` | 重启 observer |
| lifecycle | `reset_observer.sh` | 重置 observer（清空 events/offsets/run） |
| lifecycle | `healthcheck.sh` | 检查 observer 健康状态 |
| ingest | `emit_event.py` | 事件入口，补充 event_id/created_at |
| ingest | `append_event.py` | 追加事件到 events.jsonl，使用文件锁 |
| validate | `validate_log_event.py` | 校验 log event payload |
| validate | `validate_experiments_write.py` | 校验 experiments write payload |
| validate | `validate_exploration_write.py` | 校验 exploration write payload |
| validate | `validate_knowledge_write.py` | 校验 knowledge write payload |
| dispatch | `observer_daemon.py` | Observer 主进程，轮询消费事件 |
| dispatch | `consume_events.py` | 根据 offset 读取未消费事件 |
| dispatch | `dispatch_event.py` | 根据 event_type 分发到对应 writer |
| dispatch | `load_offset.py` | 读取当前消费偏移 |
| dispatch | `save_offset.py` | 保存当前消费偏移 |
| dispatch | `write_deadletter.py` | 写入失败事件到 deadletter |
| writers | `write_state.py` | 写入 `runtime/states/states.json` 检查点 |
| writers | `write_log.py` | 写入 observations log |
| writers | `write_experiments.py` | 写入 experiments 表 |
| writers | `write_exploration.py` | 写入 exploration 表 |
| writers | `write_knowledge.py` | 写入 baseline/learned/rejected JSON |
| writers | `write_candidate_pool.py` | 写入候选方案详情 JSON |
| observe | `generate_observation.py` | 一轮收尾时自动生成 LLM observation（独立配置） |
| observe | `observation_store.py` | observation 存储层，同时写入 SQLite + JSONL |

### Runtime Public Scripts

| 目录 | 脚本 | 用途 |
|------|------|------|
| validate | `validate_schema.py` | 通用 JSON schema 校验器 |
| validate | `validate_states.py` | 校验 states.json |
| validate | `validate_objective.py` | 校验 objective.json |
| validate | `validate_baseline.py` | 校验 baseline 完整性 |
| validate | `validate_runtime.py` | Phase 0 综合校验入口 |
| validate | `validate_remote.py` | 校验 remote 训练配置 |
| validate | `validate_db_schema.py` | 校验 SQLite 数据库表结构 |
| validate | `validate_event_chain.py` | 校验事件链完整性 |
| database | `init_db.py` | 初始化 SQLite (experiments + exploration) |
| database | `ensure_experiment_row.py` | 保证 experiments 表存在某行 |
| database | `update_experiment_metric.py` | 更新 experiments 表 metric |
| database | `ensure_exploration_row.py` | 保证 exploration 表存在某行 |
| database | `update_exploration_field.py` | 更新 exploration 表字段 |
| database | `query_tables.py` | 查询 SQLite 表内容 |
| database | `schema_spec.py` | SQLite 表结构定义 |
| training | `generate_launch.sh` | 生成训练 launch script |
| training | `generate_remote.sh` | 生成远程训练 launch script |
| training | `start_training.sh` | 启动训练，返回 PID |
| training | `monitor_training.py` | 监控训练日志（含自动发射 eval 指标事件） |
| training | `parse_train_log.py` | 纯日志解析器 |
| training | `terminate_training.sh` | 安全终止训练进程组 |
| coding | `smoke_test.sh` | 冒烟测试 |
| coding | `create_train_log.sh` | 创建训练日志文件 |
| coding | `commit_changes.sh` | 执行 git add/commit |
| coding | `revert_to_baseline.sh` | 回退到 baseline 状态 |
| git | `check_clean.sh` | 检查 git dirty |
| git | `latest_commit.sh` | 返回最近 commit id |
| git | `sync_remote.sh` | 同步远端代码 |
| utils | `atomic_write.py` | 原子写文件 |
| utils | `file_lock.py` | 文件锁 |
| utils | `load_json.py` | 读取 JSON |
| utils | `save_json.py` | 保存 JSON |
| utils | `jsonl.py` | JSONL 读写 |
| utils | `path_resolve.py` | 路径解析 |
| utils | `ssh_chain.py` | SSH 链式检查和执行 |
| utils | `resolve_templates.sh` | 从 objective.json 填充 `{{var}}` 占位符到模板文件 |
| utils | `resolve_model.sh` | 根据 objective.json 的 model 字段解析 subagent 模型标识 |

## 脚本调用链

### 事件发射

```
team-lead → emit_event.py → events.jsonl → observer_daemon → dispatch → writer → 持久化
                                                                   失败 → deadletter.jsonl
```

### validate_subagent_result.py 自动发射

```
subagent 返回 JSON
  → validate_subagent_result.py 校验
  → 若 event_type=exploration → 自动发射 emit_event.py exploration
  → 若 event_type=candidate_pool → 自动发射 emit_event.py candidate_pool
```

### 训练启动 & 监控

```
team-lead
  → generate_launch.sh (或 generate_remote.sh)
  → start_training.sh → nohup train.py
  → cron 轮询 → monitor_training.py → 解析 → emit_event.py experiments update_metric
```

### Team-lead 调用 runtime 脚本

```
team-lead
  → emit_log_event.sh → observer/ingest/emit_event.py → append_event.py
  → call_runtime_script.sh → runtime/scripts/*
  → validate_subagent_result.py → runtime/agents/*/schemas/*
```

## 禁止规则

- 禁止绕过 Observer 直接写 DB
- 禁止 team-lead 直接修改 knowledge JSON
- 禁止 subagent 拥有 runtime scripts
- 禁止 team-lead 直接 Write/Edit 文件（通过 observer event 间接写入）
