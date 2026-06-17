# /loop-reset

## 描述

将状态机重置为初始状态，清空 experiments / exploration 两张数据表，并清空 observer 的
events / offsets / run 三个目录产物（保留 `.gitkeep`）。

## 用法

在 Claude Code 中运行 `/loop-reset`。

## 行为

1. 确认用户意图。
2. **清空 observer 的 events / offsets / run 三个目录并重启 observer**（先于 emit 重置事件，
   以"停机清空 → 重启"避免清空时丢弃在途事件的竞态）：

   ```bash
   bash runtime/observer/scripts/lifecycle/reset_observer.sh runtime
   ```

   该脚本停 observer → 删除 `events/`(events.jsonl/deadletter.jsonl)、`offsets/`(events.offset)、
   `run/`(observer.log/observer.pid) 中除 `.gitkeep` 外的所有文件 → 重启 observer
   （重建空 events.jsonl/deadletter.jsonl、offset 归零、新 pid/log）。

3. 通过 observer `state` 事件将 `runtime/states/states.json` 重置为
   `current_step=0, next_step=1, iteration=0, exp_name=exp_0`
   （team-lead 无写权，必须 emit `state` 事件由 observer 落盘）：

   ```bash
   python3 runtime/observer/scripts/ingest/emit_event.py state \
     '{"current_step":0,"next_step":1,"iteration":0,"exp_name":"exp_0"}' runtime
   ```

4. 通过 observer 事件清空 experiments、exploration 两表（同样不直接写 SQLite）：

   ```bash
   python3 runtime/observer/scripts/ingest/emit_event.py experiments \
     '{"action":"clear_all"}' runtime
   python3 runtime/observer/scripts/ingest/emit_event.py exploration \
     '{"action":"clear_all"}' runtime
   ```

5. 记录重置事件到 observer `log`。

## 警告

- 此操作不可逆。
- 当前实验状态将丢失，experiments / exploration 表记录被清空，observer 事件流 /
  offset / 运行态文件被清空（observer 随即重启）。
- 但不会删除训练日志或 knowledge（baseline / learned / rejected）。
