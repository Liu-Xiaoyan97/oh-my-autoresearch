# /loop-status

## 描述

读取当前状态、最近日志、observer 健康状态、训练状态摘要，并展示 experiments / exploration 两表全部记录。

## 用法

在 Claude Code 中运行 `/loop-status`。

## 行为

1. 读取 `runtime/states/states.json`，显示 `current_step`、`next_step`、`iteration`、`exp_name`。
2. 读取 `runtime/logs/train-of-<exp_name>.log` 最后 20 行。
3. 调用 `runtime/observer/scripts/lifecycle/healthcheck.sh` 检查 observer 健康。
4. 查询并展示数据表全部记录（team-lead 读 SQLite 允许，只有写须走 observer event）：

   ```bash
   python3 runtime/scripts/database/query_tables.py runtime
   ```

   该脚本按表格形式打印 `experiments`（每行 = 一个实验的各 eval 检查点主指标曲线）
   与 `exploration`（每行 = 一轮的正交候选集 / 票选决策 / commit）全部记录；
   长 JSON 列默认截断到 40 字符，可用 `--width N` 调整。
5. 输出汇总信息。
