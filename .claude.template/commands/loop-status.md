# /loop-status

## 描述

读取当前状态、最近日志、observer 健康状态、训练状态摘要。

## 用法

在 Claude Code 中运行 `/loop-status`。

## 行为

1. 读取 `runtime/states/states.json`，显示 `current_step`、`next_step`、`iteration`、`exp_name`
2. 读取 `runtime/logs/train-of-<exp_name>.log` 最后 20 行
3. 调用 `runtime/observer/scripts/lifecycle/healthcheck.sh` 检查 observer 健康
4. 查询 SQLite `experiments` 表最新一行
5. 输出汇总信息
