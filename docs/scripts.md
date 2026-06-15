# Scripts

## 脚本分类

### .claude.template/scripts (Wrapper)

| 脚本 | 用途 |
|------|------|
| `emit_log_event.sh` | team-lead 向 observer 发送 log event，调用 `runtime/observer/scripts/ingest/emit_event.py` |
| `call_runtime_script.sh` | team-lead 调用 `runtime/scripts/*`，解析 runtime 根目录，标准化 stdout/stderr，返回统一 tool-result JSON |
| `validate_subagent_result.py` | 校验 subagent 返回 JSON，根据 agent 名称选择对应 schema |

### Observer Scripts

| 目录 | 脚本 | 用途 |
|------|------|------|
| lifecycle | `start_observer.sh` | 启动 observer daemon |
| lifecycle | `stop_observer.sh` | 停止 observer daemon |
| lifecycle | `restart_observer.sh` | 重启 observer |
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
| writers | `write_log.py` | 写入 observations log |
| writers | `write_experiments.py` | 写入 experiments 表 |
| writers | `write_exploration.py` | 写入 exploration 表 |
| writers | `write_knowledge.py` | 写入 baseline/learned/rejected JSON |

### Runtime Public Scripts

| 目录 | 脚本 | 用途 |
|------|------|------|
| validate | `validate_schema.py` | 通用 JSON schema 校验器 |
| validate | `validate_states.py` | 校验 states.json |
| validate | `validate_objective.py` | 校验 objective.json |
| validate | `validate_baseline.py` | 校验 baseline 完整性 |
| validate | `validate_runtime.py` | Phase 0 综合校验入口 |
| validate | `validate_remote.py` | 校验 remote 训练配置 |
| database | `init_db.py` | 初始化 SQLite (experiments + exploration) |
| database | `ensure_experiment_row.py` | 保证 experiments 表存在某行 |
| database | `update_experiment_metric.py` | 更新 experiments 表 metric |
| database | `ensure_exploration_row.py` | 保证 exploration 表存在某行 |
| database | `update_exploration_field.py` | 更新 exploration 表字段 |
| git | `check_clean.sh` | 检查 git dirty |
| git | `latest_commit.sh` | 返回最近 commit id |
| git | `sync_remote.sh` | 同步远端代码 |
| training | `generate_launch.sh` | 生成训练 launch script |
| training | `start_training.sh` | 启动训练，返回 PID |
| training | `monitor_training.py` | 监控训练日志 |
| training | `parse_train_log.py` | 纯日志解析器 |
| training | `terminate_training.sh` | 安全终止训练进程组 |
| coding | `smoke_test.sh` | 冒烟测试 |
| coding | `create_train_log.sh` | 创建训练日志文件 |
| coding | `commit_changes.sh` | 执行 git add/commit |
| utils | `atomic_write.py` | 原子写文件 |
| utils | `file_lock.py` | 文件锁 |
| utils | `load_json.py` | 读取 JSON |
| utils | `save_json.py` | 保存 JSON |
| utils | `jsonl.py` | JSONL 读写 |
| utils | `path_resolve.py` | 路径解析 |
| utils | `ssh_chain.py` | SSH 链式检查和执行 |

## 脚本调用链

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
