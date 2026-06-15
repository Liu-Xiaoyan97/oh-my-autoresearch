# 完整 Phase 工作流

## Phase 0: 初始校验

- 校验 `runtime/states/states.json` 结构
- 校验 `runtime/states/objective.json` 结构
- 检查 baseline 完整性
- 检查 remote/ssh 配置
- 检查 git clean 状态
- 输出: `phase0-validation.schema.json`

## Phase 1: 方向探索

- `orthogonal-direction-scout` 接收 baseline、learned、rejected、objective、模型上下文
- 并行参考 flow-arch-reviewer、math-theorist、numerical-debugger 三个 reviewer 建议
- 输出去重后的正交候选集
- `summarizer` 汇总候选集和三方评分，输出最高票决策
- 输出: `phase1-exploration.schema.json`

## Phase 3: 训练监控

- `coder` 根据 decision 修改研究仓库代码
- 生成 patch plan，执行冒烟测试
- 调用 `generate_launch.sh` 生成训练脚本
- 调用 `start_training.sh` 启动训练
- 调用 `monitor_training.py` 持续监控训练进度
- 输出: `phase3-training.schema.json`

## Phase 9: 经验回收

- 训练完成后，三个 reviewer 分别从各自角度分析训练结果
- `summarizer` 汇总三方分析，输出经验回收总结
- Observer 通过 knowledge event 更新 baseline/learned/rejected
- 输出: `phase9-recovery.schema.json`

## 回退逻辑

- 冒烟测试失败 → 回到 Phase 1 重新探索
- 训练启动失败 → 尝试重新生成 launch script
- 训练 loss 爆炸 → 标记为 rejected，回到 Phase 1

## loss 爆炸逻辑

- `monitor_training.py` 检测到 loss 连续 N 步上升或超过阈值
- 标记训练失败，调用 `terminate_training.sh`
- 触发 Phase 9 回收，将该方向加入 rejected
