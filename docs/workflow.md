# 完整 Phase 工作流

## Step 0: 初始校验

- 校验 `runtime/states/states.json` 结构
- 校验 `runtime/states/objective.json` 结构
- 检查 baseline 完整性
- 检查 remote/ssh 配置
- 检查 git clean 状态
- 输出: `phase0-validation.schema.json`

## Step 1: 历史载入

- 读取 `runtime/knowledges/baseline.json` — 当前最佳实践
- 读取 `runtime/knowledges/learned.json` — 经验教训
- 读取 `runtime/knowledges/rejected.json` — 已失败的方向
- 输出: 经验上下文（注入 scout/reviewer prompt）

## Step 2: 历史就绪

- 经验已注入上下文，等待方向探索
- 过渡步骤，无独立产出

## Step 3: 方向探索

- `orthogonal-direction-scout` 接收 baseline、learned、rejected、objective、模型上下文
- 并行参考 flow-arch-reviewer、math-theorist、numerical-debugger 三个 reviewer 建议
- 输出去重后的正交候选集
- 输出: candidate_pool 事件 + `phase1-exploration.schema.json`
- `validate_subagent_result.py` 自动发射 `exploration` 和 `candidate_pool` 事件

## Step 4: 票选决策

- `summarizer` 汇总候选集和三方评分
- 输出最高票决策
- 输出: `decision`（自动解析为候选方法名写入 exploration 表）

## Step 5: 代码变更

- `coder` 根据 decision 修改研究仓库代码
- 生成 patch plan
- 执行冒烟测试（`smoke_test.sh`）
  - 通过 → git 提交（`commit_changes.sh`）
  - 失败 → 回到 Step 3 重新探索（保留 candidate_pool 供参考）
- 输出: commit result

## Step 6: 远程同步（可选）

- `objective.json` 中 `remote=false` 时跳过
- `remote=true` 时通过 `sync_remote.sh` 上传代码到远端
- 输出: 同步完成

## Step 7: 训练启动

- `coder` 调用 `generate_launch.sh` 生成训练脚本（或 `generate_remote.sh` 生成远程脚本）
- 调用 `start_training.sh` 启动训练
- 设置 CronCreate 定时轮询 `monitor_training.py`
- 输出: 训练进程 PID

## Step 8: 训练结束

- CronDelete 销毁定时轮询
- `monitor_training.py` / `parse_train_log.py` 解析训练日志
- 自动检测未写入的 eval 检查点，发射 `experiments update_metric` 事件
- 输出: 训练指标（`final-metrics.schema.json`）
- 检测到 loss 爆炸 → 标记训练失败

## Step 9: 经验回收

- team-lead 先运行 `prepare_recovery.py`，显式 emit 最终实验指标与完成事件；
  事件成功追加到 `events.jsonl` 后即可拉起 summarizer，不等待异步 observer 消费
- 训练完成后三个 reviewer 分别从各自角度分析训练结果：
  - `flow-arch-reviewer` — 架构/数据流角度
  - `math-theorist` — 数学/优化理论角度
  - `numerical-debugger` — 数值稳定性角度
- `summarizer` 汇总三方分析，输出经验回收总结
- 通过 `knowledge` 事件更新 baseline/learned/rejected
- 通过 `state` 事件推进到下一轮（`iteration + 1`，回到 Step 1）
- observer daemon 在检测到 `state` 事件 `current_step=9` 时，自动调用 `generate_observation.py` 生成自然语言 observation
- 输出: `phase9-recovery.schema.json`

## 回退逻辑

- 冒烟测试失败 → 回到 Step 3 重新探索
- 训练启动失败 → 尝试回到 Step 7 重新生成 launch script
- 训练 loss 爆炸 → `monitor_training.py` 检测到 loss 连续 N 步上升或超过阈值 → 标记训练失败 → 调用 `terminate_training.sh` → 进入 Step 9 回收，将该方向加入 rejected

## Observer 自动行为

- 方向探索事件 → `write_exploration.py` 写入 exploration 表（decision 列自动从 `candidate_N` 解析为候选方法名）
- 候选方案事件 → `write_candidate_pool.py` 写入候选方案详情
- 训练轮询 → `monitor_training.py` 自动发射未写入的 eval 指标事件
- 经验回收 → `state` 事件 `current_step=9` 触发 LLM observation 生成
