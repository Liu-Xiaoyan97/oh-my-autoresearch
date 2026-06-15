# /loop-recover

## 描述

从异常状态恢复，例如训练启动失败、observer 中断、状态机不一致。

## 用法

在 Claude Code 中运行 `/loop-recover`。

## 行为

1. 检查 `runtime/states/states.json` 一致性
2. 如果 `current_step` 指向不存在的 Phase，重置为上一个稳定状态
3. 如果 observer 未运行，尝试启动
4. 如果训练进程已终止但未标记完成，尝试重新解析日志更新状态
5. 输出恢复报告

## 注意

- 恢复操作会记录到 observer log event
- 不保证完全恢复到之前状态，可能有数据丢失
