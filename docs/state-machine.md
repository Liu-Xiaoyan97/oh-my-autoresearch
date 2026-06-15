# 状态机

## 字段

- `current_step`: 当前步骤编号
- `next_step`: 下一步编号
- `iteration`: 当前迭代次数
- `exp_name`: 实验名称

## Checkpoint 1-9

| Step | Phase | 入口 | 出口 | 写入目标 |
|------|-------|------|------|----------|
| 0 | 初始校验 | 验证 states/objective/baseline | pass → 1, fail → error | 错误日志 |
| 1 | 方向探索 | 启动 scout + reviewer | done → 2 | exploration 表 |
| 2 | 代码修改 | coder 修改 + smoke test | done → 3, fail → 1 | git commit |
| 3 | 训练监控 | 启动训练 + 监控 | done → 9, fail → 9 | experiments 表 |
| 9 | 经验回收 | 分析 + knowledge 更新 | done → 1 | knowledge 文件 |

## 迁移规则

- 0 → 1: 校验通过
- 1 → 2: 有候选方案
- 2 → 3: 代码修改完成
- 2 → 1: 冒烟测试失败，重新探索
- 3 → 9: 训练完成或失败
- 9 → 1: 经验回收完成，继续下一轮
