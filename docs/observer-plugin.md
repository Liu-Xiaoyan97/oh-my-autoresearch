# Observer 插件

## 生命周期

Observer 是独立的 sidecar 进程，随 Claude Code session 启动和停止。

### 启动

```bash
runtime/observer/scripts/lifecycle/start_observer.sh
```

1. 检查是否已有 pid
2. 初始化 events、deadletter、offset 目录
3. 后台启动 `dispatch/observer_daemon.py`
4. 写入 `runtime/observer/run/observer.pid`

### 停止

```bash
runtime/observer/scripts/lifecycle/stop_observer.sh
```

1. 读取 pid
2. 发送 SIGTERM
3. 等待退出
4. 清理 pid 文件

### 重置

```bash
runtime/observer/scripts/lifecycle/reset_observer.sh
```

清空 events/offsets/run 目录（状态机重置时使用，保留现有数据库数据）。

## Events JSONL

Observer 事件入口：`runtime/observer/events/events.jsonl`

写入方式：

```bash
python runtime/observer/scripts/ingest/emit_event.py <event_type> <payload>
```

事件格式：

```json
{
    "event_id": "uuid",
    "event_type": "log|experiments|exploration|knowledge|state|candidate_pool|control",
    "payload": {...},
    "created_at": "2025-01-01T00:00:00Z"
}
```

## 六种事件类型

| event_type | Writer | 写入目标 | 说明 |
|-----------|--------|---------|------|
| `state` | `write_state.py` | `states.json` | 推进状态机检查点，唯一必须由 payload 给定全部字段的事件 |
| `log` | `write_log.py` | `observations/*.log` | 记录运行日志 |
| `experiments` | `write_experiments.py` | SQLite `experiments` 表 | 训练实验指标（建行/更新指标/标记完成） |
| `exploration` | `write_exploration.py` | SQLite `exploration` 表 | 正交候选集/决策/提交记录 |
| `knowledge` | `write_knowledge.py` | `knowledges/baseline.json` / `learned.json` / `rejected.json` | 经验知识库写入 |
| `candidate_pool` | `write_candidate_pool.py` | `runtime/candidate_pool/` | 候选方案详情，含 description/评分理由 |
| `control` | 自治处理（不进 writer） | 自清 | `action=reset` 清空 events/offsets/run |

## Offsets

消费进度记录：`runtime/observer/offsets/events.offset`

每成功消费一行，offset 加 1。

## Deadletter

失败事件：`runtime/observer/events/deadletter.jsonl`

当事件处理失败且重试次数超过阈值时，写入 deadletter。

## 五类 Schema

| Schema | 约束 | 文件 |
|--------|------|------|
| log-event | 写入 observations log | `observer/schemas/log-event.schema.json` |
| experiments-write | 写入 experiments 表 | `observer/schemas/experiments-write.schema.json` |
| exploration-write | 写入 exploration 表 | `observer/schemas/exploration-write.schema.json` |
| knowledge-write | 写入 knowledge JSON | `observer/schemas/knowledge-write.schema.json` |
| candidate-pool-write | 写入候选方案详情 | `observer/schemas/candidate-pool-write.schema.json` |

## 六类 Writer

| Writer | 目标 | 文件 |
|--------|------|------|
| write_state | `runtime/states/states.json` 检查点 | `observer/scripts/writers/write_state.py` |
| write_log | `runtime/observations/<exp_name>.log` | `observer/scripts/writers/write_log.py` |
| write_experiments | experiments 表 | `observer/scripts/writers/write_experiments.py` |
| write_exploration | exploration 表 | `observer/scripts/writers/write_exploration.py` |
| write_knowledge | baseline/learned/rejected JSON | `observer/scripts/writers/write_knowledge.py` |
| write_candidate_pool | 候选方案 JSON 详情 | `observer/scripts/writers/write_candidate_pool.py` |

## 约束

- 不读取项目源码
- 不参与推理
- 不调用 Claude tools
- 只读取自己的 events/offsets/config/schemas
