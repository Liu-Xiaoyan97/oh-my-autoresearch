# /loop

## 描述

触发完整状态机执行。

## 用法

在 Claude Code 中运行 `/loop`。

## 行为

1. 读取 `runtime/states/states.json` 获取 `current_step`
2. 根据 `current_step` 执行对应 Phase：
   - 0: 初始校验
   - 1: 方向探索 (scout + reviewer × 3 + summarizer)
   - 2: 代码修改 (coder + smoke test + git commit)
   - 3: 训练监控 (launch + start + monitor)
   - 9: 经验回收 (reviewer × 3 + summarizer + knowledge update)
3. 通过 observer `state` 事件推进状态机（emit `state` 事件，由 observer 侧车写入 `runtime/states/states.json`）
4. 如果 `current_step` 到达终态，通知用户

## 约束

- 任何 DB/knowledge/log 写入必须通过 observer event 完成
- team-lead 不直接写 DB 或 knowledge 文件
- subagent 调用必须返回结构化 JSON，由 team-lead 校验
