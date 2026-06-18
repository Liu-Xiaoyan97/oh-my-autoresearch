# 状态机

## 字段

- `current_step`: 当前步骤编号
- `next_step`: 下一步编号
- `iteration`: 当前迭代次数
- `exp_name`: 实验名称

## 完整 10 步状态机

| Step | Phase | 说明 | 产出 |
|------|-------|------|------|
| 0 | 校验 | 运行 validate_runtime（含 schema 校验、远程连接检查、git clean） | 校验通过报告 |
| 1 | 历史载入 | 读取 baseline / learned / rejected | 经验上下文 |
| 2 | 历史就绪 | 经验已注入上下文，准备方向探索 | — |
| 3 | 方向探索 | scout + 3 个 reviewer 并行 | 正交候选集 |
| 4 | 票选决策 | summarizer + 3 个 reviewer 并行评分 | 最高票方法 |
| 5 | 代码变更 | coder 实施、冒烟测试、git 提交（含 baseline 回退） | commit result |
| 6 | 远程同步 | 代码上传远端（可选） | 同步完成 |
| 7 | 训练启动 | generate_launch → start_training → CronCreate 轮询 | 训练进程 PID |
| 8 | 训练结束 | CronDelete 销 cron，解析日志 | 训练指标 |
| 9 | 经验回收 | 3 个 reviewer 分析 → summarizer 汇总 → knowledge 更新 | learned/rejected/baseline |

## 迁移规则

```
0 → 1:  校验通过
1 → 2:  经验加载完成
2 → 3:  经验就绪
3 → 4:  有候选方案（scout 产出 orthoSet）
4 → 5:  票选决策完成（summarizer 输出 decision）
5 → 6:  代码修改完成、冒烟测试通过、git 提交成功
5 → 3:  冒烟测试失败，重新探索（candidate_pool 保留供参考）
6 → 7:  远程同步完成（或 remote=false 直接跳转）
7 → 8:  CronCreate 设置完成
8 → 9:  训练结束（成功或失败均进入回收）
9 → 1:  经验回收完成，iteration + 1，继续下一轮
```

## 回退逻辑

- 冒烟测试失败 → 回到 Step 3（方向探索）重新探索，但保留失败方案的 candidate_pool 记录
- 训练启动失败 → 尝试回到 Step 7 重新生成 launch script
- 训练 loss 爆炸 → monitor_training.py 检测 → terminate_training.sh → 进入 Step 9 回收，将该方向标记为 rejected
