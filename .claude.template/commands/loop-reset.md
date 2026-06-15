# /loop-reset

## 描述

将状态机重置为初始状态。

## 用法

在 Claude Code 中运行 `/loop-reset`。

## 行为

1. 确认用户意图
2. 将 `runtime/states/states.json` 重置为：

```json
{
  "current_step": 0,
  "next_step": 1,
  "iteration": 0,
  "exp_name": "exp_0"
}
```

3. 记录重置事件到 observer

## 警告

- 此操作不可逆
- 当前实验状态将丢失
- 但不会删除训练数据或 knowledge
