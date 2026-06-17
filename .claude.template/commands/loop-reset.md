# /loop-reset

## 描述

将状态机重置为初始状态，并清空 experiments / exploration 两张数据表。

## 用法

在 Claude Code 中运行 `/loop-reset`。

## 行为

1. 确认用户意图。
2. 通过 observer `state` 事件将 `runtime/states/states.json` 重置为
   `current_step=0, next_step=1, iteration=0, exp_name=exp_0`
   （team-lead 无写权，必须 emit `state` 事件由 observer 落盘）：

   ```bash
   python3 runtime/observer/scripts/ingest/emit_event.py state \
     '{"current_step":0,"next_step":1,"iteration":0,"exp_name":"exp_0"}' runtime
   ```

3. 通过 observer 事件清空 experiments、exploration 两表（同样不直接写 SQLite）：

   ```bash
   python3 runtime/observer/scripts/ingest/emit_event.py experiments \
     '{"action":"clear_all"}' runtime
   python3 runtime/observer/scripts/ingest/emit_event.py exploration \
     '{"action":"clear_all"}' runtime
   ```

4. 记录重置事件到 observer `log`。

## 警告

- 此操作不可逆。
- 当前实验状态将丢失，experiments / exploration 表记录被清空。
- 但不会删除训练日志或 knowledge（baseline / learned / rejected）。
