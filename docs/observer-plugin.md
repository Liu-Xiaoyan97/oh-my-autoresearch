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
    "event_type": "log|experiments|exploration|knowledge",
    "payload": {...},
    "created_at": "2025-01-01T00:00:00Z"
}
```

## Offsets

消费进度记录：`runtime/observer/offsets/events.offset`

每成功消费一行，offset 加 1。

## Deadletter

失败事件：`runtime/observer/events/deadletter.jsonl`

当事件处理失败且重试次数超过阈值时，写入 deadletter。

## 四类 Schema

| Schema | 约束 | 文件 |
|--------|------|------|
| log-event | 写入 observations log | `observer/schemas/log-event.schema.json` |
| experiments-write | 写入 experiments 表 | `observer/schemas/experiments-write.schema.json` |
| exploration-write | 写入 exploration 表 | `observer/schemas/exploration-write.schema.json` |
| knowledge-write | 写入 knowledge JSON | `observer/schemas/knowledge-write.schema.json` |

## 四类 Writer

| Writer | 目标 | 文件 |
|--------|------|------|
| write_log | `runtime/observations/<exp_name>.log` | `observer/scripts/writers/write_log.py` |
| write_experiments | experiments 表 | `observer/scripts/writers/write_experiments.py` |
| write_exploration | exploration 表 | `observer/scripts/writers/write_exploration.py` |
| write_knowledge | baseline/learned/rejected JSON | `observer/scripts/writers/write_knowledge.py` |

## 约束

- 不读取项目源码
- 不参与推理
- 不调用 Claude tools
- 只读取自己的 events/offsets/config/schemas
