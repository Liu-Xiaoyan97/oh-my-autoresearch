# /loop-reset

## 描述

将状态机重置为初始状态，清空 experiments / exploration 两张数据表，并让**自治 observer
自行清空** events / offsets / run 三个目录产物（保留 `.gitkeep`）。

> observer 完全自治：主程序**绝不直接调用** observer 的任何脚本，只能通过向 events.jsonl
> **emit 事件**来触发它。清空 observer 自身产物也通过 `control` 事件由 observer 自己完成。

## 用法

在 Claude Code 中运行 `/loop-reset`。

## 行为

1. 确认用户意图。
2. 通过 observer `state` 事件将 `runtime/states/states.json` 重置为
   `current_step=0, next_step=1, iteration=0, exp_name=exp_0`：

   ```bash
   python3 runtime/observer/scripts/ingest/emit_event.py state \
     '{"current_step":0,"next_step":1,"iteration":0,"exp_name":"exp_0"}' runtime
   ```

3. 通过 observer 事件清空 experiments、exploration 两表：

   ```bash
   python3 runtime/observer/scripts/ingest/emit_event.py experiments '{"action":"clear_all"}' runtime
   python3 runtime/observer/scripts/ingest/emit_event.py exploration '{"action":"clear_all"}' runtime
   ```

4. 记录重置事件到 observer `log`。
5. **最后**发一个 `control` 重置事件，由 observer **自行**清空 events / offsets / run
   （truncate events.jsonl、deadletter.jsonl、offset 归零、清 observer.log，保留 `.gitkeep`）：

   ```bash
   python3 runtime/observer/scripts/ingest/emit_event.py control '{"action":"reset"}' runtime
   ```

   该事件必须是本次 reset 发出的**最后一个**事件——observer 消费到它时，前面的确定性
   重置事件均已落盘，随后它把事件流自清归零。

## 警告

- 此操作不可逆。
- 状态机、experiments / exploration 表、observer 事件流 / offset / 运行日志被清空。
- 不会删除训练日志、knowledge（baseline/learned/rejected）或 observer 的 observations 历史。
