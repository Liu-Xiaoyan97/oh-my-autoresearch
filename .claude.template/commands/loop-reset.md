# /loop-reset

## 描述

将状态机重置为初始状态，清空 experiments / exploration 两张数据表，并让**自治 observer
自行清空** events / offsets / run 三个目录产物（保留 `.gitkeep`）。

> observer 完全自治：主程序**绝不直接调用** observer 的任何脚本，只能通过向 events.jsonl
> **emit 事件**来触发它。清空 observer 自身产物也通过 `control` 事件由 observer 自己完成。

## 用法

在 Claude Code 中运行 `/loop-reset`。

## 行为

### 0. 确认用户意图

用户确认后继续。

### 1. 检查 observer 状态（只读 observer.status，不调 lifecycle 脚本）

```read
runtime/observer/run/observer.status
```

- 如果 `alive` 为 `true` → 继续。
- 如果 `alive` 为 `false` 或文件不存在 → 通知用户 observer 未运行，要求**重启 claude session**
  以触发 session-start hook 重新启动 observer，不可手动调用 lifecycle 脚本。

### 2. 通过 observer state 事件重置 states.json

```bash
python3 runtime/observer/scripts/ingest/emit_event.py state \
  '{"current_step":0,"next_step":1,"iteration":0,"exp_name":"exp_0"}' runtime
```

### 3. 通过 observer 事件清空 experiments、exploration 两表及候选池

```bash
python3 runtime/observer/scripts/ingest/emit_event.py experiments '{"action":"clear_all"}' runtime
python3 runtime/observer/scripts/ingest/emit_event.py exploration '{"action":"clear_all"}' runtime
python3 runtime/observer/scripts/ingest/emit_event.py candidate_pool '{"action":"clear"}' runtime
```

### 4. 记录重置日志

```bash
python3 runtime/observer/scripts/ingest/emit_event.py log \
  '{"level":"INFO","source":"team-lead","message":"/loop-reset 执行：状态机、experiments、exploration 已重置"}' runtime
```

### 5. 等待 observer 消费以上事件（CronCreate 2分钟后检查，而非 sleep 阻塞）

```bash
# 观察 offset 是否增长到 5（state + experiments + exploration + candidate_pool + log 共 5 个事件）
# 使用 CronCreate 定时检查，非 sleep 阻塞
```

### 6. 最后发 control reset 事件，由 observer 自行清空 events/offsets/run

```bash
python3 runtime/observer/scripts/ingest/emit_event.py control '{"action":"reset"}' runtime
```

该事件必须是本次 reset 发出的**最后一个**事件——observer 消费到它时，前面的确定性
重置事件均已落盘，随后它把事件流自清归零。

### 7. 等待 observer 完成自清，然后最终验证

仍用 CronCreate 等待，不用 sleep。验证：
- `Read runtime/states/states.json` → `current_step=0, next_step=1`
- `Read runtime/observer/run/observer.status` → `offset=0`
- `Read runtime/observer/events/events.jsonl` → 空文件

## 约束（必须遵守，否则 PreToolUse hook 会拦截）

- ❌ **绝不**直接写 `states.json`（`echo/cat/write > states.json` 会被 hook 拦截）
- ❌ **绝不**调用 observer lifecycle 脚本（`start_observer.sh`、`restart_observer.sh` 等会被 hook 拦截）
- ❌ **绝不**直接操作 `runtime/observer/` 下的产物文件
- ✅ 所有状态变更只能通过 `emit_event.py` 完成
- ✅ observer 状态只通过 `Read observer/run/observer.status` 只读查看

## 警告

- 此操作不可逆。
- 状态机、experiments / exploration 表、observer 事件流 / offset / 运行日志被清空。
- 不会删除训练日志、knowledge（baseline/learned/rejected）或 observer 的 observations 历史。
