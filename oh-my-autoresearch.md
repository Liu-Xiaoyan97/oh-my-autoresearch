## 系统架构图

![系统架构图](research-runtime/assets/oh-my-autoresearch.png)

## Agent
- team-lead 主程序，只有读权限，没有写权限，可以调用工具
- Observer 用于监控team-lead和其他agent，只有日志的写入权限和数据库的写入权限，没有读取权限，禁用一切工具
- flow-arch-reviewer 
- math-theorist
- numerical-debugger
- orthogonal-direction-scout
- summarizer

## Runtime File System
### 整体项目文件架构
```
oh-my-autoresearch/
├── README.md
├── LICENSE
├── VERSION
├── manifest.json
├── pyproject.toml
├── .gitignore
│
├── install.sh
├── uninstall.sh
├── bootstrap.sh
├── upgrade.sh
├── doctor.sh
│
├── docs/
│   ├── architecture.md
│   ├── installation.md
│   ├── workflow.md
│   ├── state-machine.md
│   ├── team-lead.md
│   ├── observer-plugin.md
│   ├── subagents.md
│   ├── schemas.md
│   ├── scripts.md
│   └── troubleshooting.md
│
├── .claude.template/
│   ├── CLAUDE.md                          # team-lead 主程序定义
│   ├── settings.json                      # hooks / permissions / tool policy
│   ├── settings.local.example.json
│   │
│   ├── commands/
│   │   ├── loop.md
│   │   ├── loop-status.md
│   │   ├── loop-recover.md
│   │   ├── loop-reset.md
│   │   └── loop-doctor.md
│   │
│   ├── agents/                            # 仅 Claude Code subagents
│   │   ├── orthogonal-direction-scout.md
│   │   ├── summarizer.md
│   │   ├── coder.md
│   │   ├── flow-arch-reviewer.md
│   │   ├── math-theorist.md
│   │   └── numerical-debugger.md
│   │
│   ├── schemas/
│   │   ├── phase0-validation.schema.json
│   │   ├── phase1-exploration.schema.json
│   │   ├── phase3-training.schema.json
│   │   ├── phase9-recovery.schema.json
│   │   ├── state-transition.schema.json
│   │   ├── subagent-result.schema.json
│   │   └── tool-result.schema.json
│   │
│   ├── scripts/
│   │       ├── emit_log_event.sh # team-lead 向 observer 写 log event 的轻量入口
│   │       ├── call_runtime_script.sh #team-lead 调用 runtime/scripts/* 的统一 wrapper 
│   │       └── validate_subagent_result.py # 校验 subagent 返回 JSON 是否符合 runtime/agents/<agent>/schemas/*
│   │
│   └── hooks/                             # 启停 observer sidecar
│       ├── session-start.sh
│       ├── stop.sh
│       ├── pre-tool-use.sh
│       └── post-tool-use.sh
│
├── runtime.template/
│   ├── states/
│   │   ├── states.json
│   │   └── objective.example.json
│   │
│   ├── knowledges/
│   │   ├── baseline.json
│   │   ├── learned.json
│   │   └── rejected.json
│   │
│   ├── observations/
│   │   └── .gitkeep
│   │
│   ├── logs/
│   │   └── .gitkeep
│   │
│   ├── launchscripts/
│   │   └── .gitkeep
│   │
│   ├── db/
│   │   └── .gitkeep
│   │
│   ├── schemas/                           # 全局 runtime schema
│   │   ├── state.schema.json
│   │   ├── objective.schema.json
│   │   ├── baseline.schema.json
│   │   ├── learned.schema.json
│   │   ├── rejected.schema.json
│   │   ├── experiment-row.schema.json
│   │   ├── exploration-row.schema.json
│   │   ├── validation-result.schema.json
│   │   ├── training-progress.schema.json
│   │   ├── final-metrics.schema.json
│   │   ├── recovery-result.schema.json
│   │   └── error.schema.json
│   │
│   ├── observer/                          # 独立插件 / sidecar
│   │   ├── config.json
│   │   ├── events/ # 事件入口，append-only / inbox
│   │   │   └── .gitkeep
│   │   │
│   │   ├── run/ # 运行时生成目录
│   │   │   └── .gitkeep
│   │   │
│   │   ├── offsets/ # 消费进度
│   │   │   └── .gitkeep
│   │   │
│   │   ├── schemas/
│   │   │   ├── log-event.schema.json          # 写 observations/*.log
│   │   │   ├── experiments-write.schema.json  # 写 experiments 表
│   │   │   ├── exploration-write.schema.json  # 写 exploration 表
│   │   │   └── knowledge-write.schema.json    # 写 baseline/learned/rejected
│   │   │
│   │   └── scripts/
│   │       ├── lifecycle/
│   │       │   ├── start_observer.sh
│   │       │   ├── stop_observer.sh
│   │       │   ├── restart_observer.sh
│   │       │   └── healthcheck.sh
│   │       │
│   │       ├── ingest/
│   │       │   ├── emit_event.py
│   │       │   └── append_event.py
│   │       │
│   │       ├── validate/
│   │       │   ├── validate_log_event.py
│   │       │   ├── validate_experiments_write.py
│   │       │   ├── validate_exploration_write.py
│   │       │   └── validate_knowledge_write.py
│   │       │
│   │       ├── dispatch/
│   │       │   ├── observer_daemon.py
│   │       │   ├── consume_events.py
│   │       │   ├── dispatch_event.py
│   │       │   ├── load_offset.py
│   │       │   ├── save_offset.py
│   │       │   └── write_deadletter.py
│   │       │
│   │       └── writers/
│   │           ├── write_log.py
│   │           ├── write_experiments.py # 是observer事件writer，可调用datase helper
│   │           ├── write_exploration.py # 是observer事件writer，可调用datase helper
│   │           └── write_knowledge.py
│   │
│   ├── agents/                            # subagents runtime contracts
│   │   ├── orthogonal-direction-scout/
│   │   │   └── schemas/
│   │   │       ├── input.schema.json
│   │   │       ├── reviewer-proposal.schema.json
│   │   │       ├── candidate.schema.json
│   │   │       └── orthogonal-set.schema.json
│   │   │
│   │   ├── summarizer/
│   │   │   └── schemas/
│   │   │       ├── vote-input.schema.json
│   │   │       ├── vote.schema.json
│   │   │       ├── decision.schema.json
│   │   │       ├── recovery-analysis.schema.json
│   │   │       └── recovery-summary.schema.json
│   │   │
│   │   ├── coder/
│   │   │   └── schemas/
│   │   │       ├── coding-task.schema.json
│   │   │       ├── patch-plan.schema.json
│   │   │       ├── smoke-test.schema.json
│   │   │       ├── launch-script.schema.json
│   │   │       └── commit-result.schema.json
│   │   │
│   │   ├── flow-arch-reviewer/
│   │   │   └── schemas/
│   │   │       ├── proposal.schema.json
│   │   │       ├── vote.schema.json
│   │   │       └── recovery.schema.json
│   │   │
│   │   ├── math-theorist/
│   │   │   └── schemas/
│   │   │       ├── proposal.schema.json
│   │   │       ├── vote.schema.json
│   │   │       └── recovery.schema.json
│   │   │
│   │   └── numerical-debugger/
│   │       └── schemas/
│   │           ├── proposal.schema.json
│   │           ├── vote.schema.json
│   │           └── recovery.schema.json
│   │
│   └── scripts/                           # 公共执行器
│       ├── validate/
│       │   ├── validate_schema.py
│       │   ├── validate_states.py
│       │   ├── validate_objective.py
│       │   ├── validate_baseline.py
│       │   ├── validate_runtime.py
│       │   └── validate_remote.py
│       │
│       ├── database/ # 是底层DB helper
│       │   ├── init_db.py 
│       │   ├── ensure_experiment_row.py # 
│       │   ├── update_experiment_metric.py
│       │   ├── ensure_exploration_row.py
│       │   └── update_exploration_field.py
│       │
│       ├── git/
│       │   ├── check_clean.sh # 检查当前研究仓库是否存在未提交变动
│       │   ├── latest_commit.sh # 获取 coder 提交后的 commit id
│       │   └── sync_remote.sh # 远程同步代码
│       │
│       ├── training/
│       │   ├── generate_launch.sh #生成runtime/launchscripts/launch_<exp_name>.sh
│       │   ├── start_training.sh # nohup runtime/launchscripts/launch_<exp_name>.sh输出到 runtime/logs/train-of-<exp_name>.log
│       │   ├── monitor_training.py # 解析 runtime/logs/train-of-<exp_name>.log
│       │   ├── parse_train_log.py # 仅做日志解析，不做状态修改
│       │   └── terminate_training.sh #  kill 训练进程组
│       │
│       ├── coding/
│       │   ├── smoke_test.sh
│       │   ├── create_train_log.sh
│       │   └── commit_changes.sh
│       │
│       └── utils/
│           ├── atomic_write.py
│           ├── file_lock.py
│           ├── load_json.py
│           ├── save_json.py
│           ├── jsonl.py
│           ├── path_resolve.py
│           └── ssh_chain.py
│
├── tests/
│   ├── conftest.py
│   ├── test_manifest.py
│   ├── test_install_layout.py
│   ├── test_team_lead_main.py
│   ├── test_claude_template.py
│   ├── test_subagent_contracts.py
│   ├── test_observer_sidecar.py
│   ├── test_observer_events.py
│   ├── test_runtime_scripts.py 
│   ├── test_schema_binding.py
│   ├── test_state_machine.py
│   ├── test_database.py
│   ├── test_runtime_validation.py
│   ├── test_permissions.py
│   └── fixtures/
│
└── examples/
```
fixtures文件夹
```
tests/fixtures/
├── valid_runtime/
│   ├── states/
│   │   ├── states.json
│   │   └── objective.json
│   ├── knowledges/
│   │   ├── baseline.json
│   │   ├── learned.json
│   │   └── rejected.json
│   ├── db/
│   │   └── runtime.sqlite
│   └── logs/
│       └── train-of-exp_1.log
│
├── invalid_runtime/
│   ├── missing_states/
│   ├── invalid_objective_mode/
│   ├── remote_without_hosts/
│   ├── incomplete_baseline/
│   └── dirty_git/
│
├── valid_observer_events/
│   ├── log.json
│   ├── experiments_insert.json
│   ├── experiments_update_metric.json
│   ├── exploration_candidates.json
│   ├── exploration_decision.json
│   ├── exploration_commit.json
│   ├── knowledge_baseline.json
│   ├── knowledge_learned.json
│   └── knowledge_rejected.json
│
├── invalid_observer_events/
│   ├── missing_exp_name.json
│   ├── invalid_log_level.json
│   ├── unknown_experiment_action.json
│   ├── invalid_exploration_field.json
│   └── invalid_knowledge_target.json
│
├── valid_subagent_outputs/
│   ├── orthogonal-direction-scout.json
│   ├── summarizer_decision.json
│   ├── coder_commit.json
│   ├── flow-arch-reviewer_proposal.json
│   ├── math-theorist_vote.json
│   └── numerical-debugger_recovery.json
│
├── invalid_subagent_outputs/
│   ├── missing_candidate_id.json
│   ├── invalid_vote_score.json
│   ├── missing_commit_id.json
│   └── malformed_recovery_summary.json
│
├── valid_objectives/
│   ├── local_mps.json
│   ├── local_cuda.json
│   └── remote_ssh_chain.json
│
├── invalid_objectives/
│   ├── invalid_metric_mode.json
│   ├── missing_command.json
│   ├── invalid_steps.json
│   └── remote_hosts_empty.json
│
└── mock_research_repo/
    ├── .git/
    ├── model.py
    ├── train.py
    ├── configs/
    │   └── default.yaml
    └── README.md
```
examples文件夹
```
examples/
├── minimal-local/
│   ├── README.md
│   ├── objective.json
│   ├── states.json
│   ├── baseline.json
│   └── expected-layout.txt
│
├── remote-ssh-chain/
│   ├── README.md
│   ├── objective.json
│   ├── states.json
│   └── hosts.example.txt
│
├── observer-events/
│   ├── log-event.json
│   ├── experiments-write.json
│   ├── exploration-write.json
│   └── knowledge-write.json
│
├── subagent-outputs/
│   ├── orthogonal-direction-scout.json
│   ├── summarizer-decision.json
│   ├── coder-commit-result.json
│   ├── reviewer-proposal.json
│   ├── reviewer-vote.json
│   └── reviewer-recovery.json
│
└── research-runtime-layout/
    ├── before-install.txt
    ├── after-install.txt
    └── README.md
```
### runtime文件构成
```
runtime
    ├── knowledges  # 历史经验
    │   ├── baseline.json # 基线方法
    │   ├── learned.json # 可以优化指标的方法记录
    │   └── rejected.json # 不可优化指标的方法记录
    ├── schemas # agent通讯格式
    │   └── <schema>.json
    ├── scripts # team-lead可调用的脚本
    │   ├── generate_launch.sh # 训练脚本生成器
    │   └── launchscripts # 训练脚本目录
    │       └── launch_<exp_name>.sh # 真实训练脚本
    ├── observations # 观察者日志目录
    │   └── <exp_name>.log # 观察者日志
    ├── logs # 训练日志
    │   └── train-of-<exp_name>.log # 训练状态日志
    └── states 
        ├── objective.json # 优化对象描述
        └── states.json # 状态描述
```
### 日志文件
<exp_name>.log仅包含时间、等级、信息三要素，[YYYY-MM-DD HH:MM:SS]|[LEVEL]-{Message}，下面是一个例子
```
[2026-06-14 19:23:23]|[INFO]-[启动校验]
[2026-06-14 19:23:24]|[ERROR]-[无baseline记录或记录不完整]
```
### 数据库
experiments表（sqlite数据库table）primary key为实验名，<exp_name>

| 字段名      | 类型     | 描述                                  | 备注                                                    |
| -------- | ------ | ----------------------------------- | ----------------------------------------------------- |
| exp_name | string | 实验名                                 | primary key                                           |
| <step_n> | float  | 第n*evel_n_step的primary_metrics.name | 总共有num_training_steps//eval_n_steps个字段，用来记录完整的metrics |

exploration表(sqlite数据库table)，primary key为实验名，<exp_name>

| 字段名                        | 类型     | 描述             | 备注          |
| -------------------------- | ------ | -------------- | ----------- |
| exp_name                   | string | 实验名            | primary key |
| orthogonal-direction-scout | text   | 去重候选集          |             |
| decision                   | text   | 最终投票决定的修改方向    |             |
| commit                     | text   | 仓库提交的commit_id |             |

## 工作流
#### 状态说明（用于team-lead)
current_step表示当前状态，next_step表示下一步跳转状态，初始 current_step = 0, next_step = 1
#### 检查点说明(用于observer)
checkpoint 1: 初始校验通过，current_step = 1, next_step = 2
checkpoint 2: 载入历史经验，current_step = 2, next_step = 3
checkpoint 3: 获得去重正交候选集, current_step = 3, next_step = 4
checkpoint 4: 获得票选最高方法, current_step = 4, next_step = 5
checkpoint 5: git提交成功, current_step = 5, next_step = 6
checkpoint 6: git同步完成, current_step = 6, next_step = 7
checkpoint 7: 训练脚本启动成功, current_step = 7, next_step = 8
checkpoint 8: 训练结束, current_step = 8, next_step = 9
checkpoint 9: 经验回收结束, current_step = 9, next_step = 0
### Phase 0
初始校验，包括states、objective和baseline

---
#### 文件描述
states 状态机

| key          | 类型     | 描述                      |
| ------------ | ------ | ----------------------- |
| next_step    | int    | 记录下一跳地址                 |
| iteration    | int    | 记录轮次信息                  |
| current_step | int    | 记录当前阶段                  |
| exp_name     | string | 实验名，一般为exp_\<iteration> |

objective 优化目标信息

| key                | 类型     | 描述                                                                                                             |
| ------------------ | ------ | -------------------------------------------------------------------------------------------------------------- |
| goal               | string | 描述优化思路                                                                                                         |
| primary_metrics    | Dict   | 优化对象指标，包含name（监控指标）mode（指标模式，maximization, minimization中的一个）                                                   |
| project_root       | Path   | 代码仓库根目录                                                                                                        |
| command            | Path   | 训练脚本地址，num_training_steps和eval_n_steps需要作为参数传递进去                                                               |
| remote             | bool   | 启用远程训练，默认为false                                                                                                |
| hosts              | List   | 服务器地址，可以是嵌套结构，如["mgt", "gpu01"]表示先连接mgt在跳转至gpu01，注意本地与服务器必须配置免密登陆，默认为[]表示本地训练，若remote为True，host必须非空，且可以ssh连接上。 |
| num_training_steps | int    | 训练步数                                                                                                           |
| eval_n_steps       | int    | 每隔eval_n_steps进行一次模型验证                                                                                         |
| devices            | List   | 默认为mps，也可以是gpu_id的列表                                                                                           |

---
#### 流程描述
1. 识别到用户的slash命令`/loop`，team-lead进入状态1，启动脚本校验states.json、objective.json和baseline信息是否符合要求，Observer向`runtime/observations/<exp_name>.log`写入记录**启动校验**：
    - 符合要求：通知team-lead校验通过，observer向`runtime/observations/<exp_name>.log`写入**校验通过**
    - 不符合：raise错误信息，team-lead通知用户，observer写入错误信息，待用户确认修改完毕后，再次启动脚本校验states.json、objective.json和baseline
2. team-lead调用git查阅当前代码是否有未提交的变动：
    - 如果有，team-lead通知用户，observer写入日志**存在未提交变动**，待用户确认处理完毕后，再次调用git检查。
    - 否则，team-lead使用codegraph找到并载入模型定义文件，observer写入日志**载入xxx.py**
 3. team-lead载入states.json、objective.json再跳转至状态next_step-1（返回到最近的一个检查点），Observer查找experiments和exploration表是否存在key为<exp_name>的记录（如果没有就插入），更新states.json文件的current_step=next_step-1，next_step=next_step
---
#### 脚本校验描述
脚本校验使用pytest需要符合以下规则：
1. states.json、objective.json的key类型正确
2. primary_metrics的mode值必须是maximization或minimization
3. remote若为True，确认hosts非空，
4. 使用ssh测试是否可以按顺序登陆至最后一个host
5. 查询experiments表的baseline是否完整，完整的一条记录应该包含num_training_steps//eval_n_steps + 1个非空字段，如果有字段为空，表明baseline没有训练完成，测试不通过，否则通过
6. 1-5项检测均通过后返回`[PASS]`
7. 若存在未通过项，返回错误信息
### Phase 1
方向探索阶段，查询历史记录，创建两级subagent，找到一条评分最高的正交路线实施

---
#### 文件描述
baseline.json
```
{
    "exp_name":
	"method_summary": 
}
```
learned.json\/rejected.json
```
{
	{
		"exp_name":
		"method_summary":
		"reason":
	},
	{
		"exp_name":
		"method_summary":
		"reason":
	}
}
```
runtime/scripts/generate_launch.sh 见scripts

---
#### 流程描述
1. team-lead 进入状态2，载入knowledges/baseline.json、knowledges/learned.json和knowledges/rejected.json，observer写入日志**载入经验文件**，更新states.json文件的current_step=2，next_step=3
2. team-lead 创建嵌套结构的subagent，创建完毕后observer写入日志**两级subagent创建成功**。嵌套subagent的结构如下：
    ```
    team-lead # 主agent
        ├── orthogonal-direction-scout # 去重得到正交候选集交给summarizer
        │   ├── flow-arch-reviewer # 从架构上找优化点
        │   ├── math-theorist # 从数学上找优化点
        │   └── numerical-debugger # 从数值上找优化点
        ├── summarizer # 总结票选候选集，找出投票最高的一个方法交给coder
        │   ├── flow-arch-reviewer # 从架构上给候选集评分
        │   ├── math-theorist # 从数学上给候选集评分
        │   └── numerical-debugger # 从数值上给候选集评分
        └── coder # 基于sumarizer给出的票选最高方法实施代码修改，在本地完成冒烟测试，调用runtime/scripts/generate_launch.sh生成真实的训练脚本，创建runtime/logs/train-of-<exp_name>.log，并使用git提交变更
    ```
   要求：
     1. 一级subagent（orthogonal-direction-scout、summarizer、coder)信息串行处理，二级subagent（flow-arch-reviewer、math-theorist、numerical-debugger）信息并行处理。
     2. orthogonal-direction-scout销毁后，team-lead进入状态3，observer查找exploration表`exp_name`为<exp_name>的记录，将`orthogonal-direction-scout`字段为去重后的正交候选集总结，并写入日志记录**正交候选集生成完成**，更新states.json文件的current_step=3，next_step=4
     3. summarizer销毁后，team-lead进入状态4，observer查找exploration表`exp_name`为<exp_name>的记录，将`decision`字段更新为票选最高的方法描述，并写入日志记录**票选最高方法完成**,更新states.json文件的current_step=4，next_step=5
     4. coder销毁后，team-lead进入状态5，observer查找exploration表`exp_name`为<exp_name>的记录，并将`commit`字段更新为最近一次提交的commit id，并写入日志记录**代码变更完成**,更新states.json文件的current_step=5，next_step=6
   3. team-lead发现所有subagent销毁后，进入状态6，使用ssh登陆跳板机，从远程仓库同步代码，observer写入日志**代码上传成功**,更新states.json文件的current_step=6，next_step=7
   4. team-lead的current_step为[3, 4, 5]，检查是否存在对应的嵌套agent，如果不存在，则拉起该subagent
### Phase 3
模型训练、监控与经验回收

---
#### 文件描述


---
#### 流程描述
1. team-lead确认代码同步完成后，进入状态7，使用`nohup runtime/scripts/launchscripts/launch_<exp_name>.sh > runtimes/logs/train-of-<exp_name>.log 2>&1 &`后台挂起训练，获得主进程PID，创建cron定时查询runtimes/logs/train-of-<exp_name>.log（返回最近的一个训练进度和最近的一个验证记录，注意，step为训练进度的step，val_step为最近一次进行eval的step），observer写入日志**启动训练监控，主进程PID为\[$PID\]**
```{
	"train_step": step,
	"train_loss": train_loss,
	"val_step": val_step,
	"val_{primary_metrics.name}": value,
}
```
cron查询训练进度存在以下两种情况：
    A. 训练启动失败：team-lead取消cron任务，回退至current_step=5, next_step=6，observer写入日志**启动失败，回退至步骤5**，team-lead随后创建subagent `coder`传递错误信息给它，`coder`销毁后，team-lead同步代码后进入状态7
    B. 训练启动成功：cron每返回一次结果，team-lead检查返回结果：
	    B1. 若"train_loss"有爆炸迹象，则使用`kill -- -$(ps -o pgid= -p <PID> | tr -d ' ')`，安全结束训练，取消cron定时查询任务，team-lead跳转至状态9，observer记录日志**loss爆炸**并更新states.json的current_step = 9, next_step = 0
		B2. 若"val_step"为空，team-lead继续等待
		B3. 若"val_step"和"val_{primary_metrics.name}"均不为空，observer更新experiments表exp_name为<exp_name>的记录的val_step字段值为value
		B4. 若"val_step"已经等于"num_training_steps"表明训练完成，team-lead进入状态8，取消cron定时查询任务，observer记录日志**训练结束**并更新states.json的current_step = 8， next_step = 9
2. team-lead进入状态9，创建结果分析的嵌套subagent结构如下：
	   ```
	   team-lead # 主agent
         └── summarizer # 总结三方描述，按格式返回给team-lead
             ├── flow-arch-reviewer # 结合训练结果从架构上给经验/教训描述
             ├── math-theorist # 结合训练结果从数学上给经验/教训描述
             └── numerical-debugger # 结合训练结果从数值上给经验/教训描述
	   ```
    要求：
     1. 二级subagent（flow-arch-reviewer、math-theorist、numerical-debugger）信息并行处理
     2. summarizer销毁后，team-lead对比基线方法的实验结果，判断方法是否奏效：
        A. 优于baseline，observer按格式追加至learned.json，更新baseline为当前方法，并写入日志记录**<exp_name>成为新的基线方法**,更新states.json文件的current_step=9，next_step=0
        B. 与baseline持平，observer按格式追加至learned.json，并写入日志记录**<exp_name>经验已收录**,更新states.json文件的current_step=9，next_step=0
     C. 逊于baseline, observer按格式追加至rejected.json，并写入日志记录**<exp_name>经验已收录被否决**,更新states.json文件的current_step=9，next_step=0
3. team-lead进入状态0，observer修改states.json的current_step=0, next_step=1
---


## scripts
### runtime/scripts/generate_launch.sh 

```
#!/usr/bin/env bash

# ==============================================================================

# generate_launch.sh

#

# 从 runtime/states/objective.json + runtime/states/states.json 自动生成

# runtime/scripts/launchscripts/launch_<exp_name>.sh，支持本地/远程训练。

#

# 用法:

# ./runtime/scripts/generate_launch.sh # 默认路径

# ./runtime/scripts/generate_launch.sh path/to/objective.json path/to/states.json

# ==============================================================================

set -euo pipefail

  

# 定位到仓库根目录

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

  

OBJ="${1:-$ROOT_DIR/runtime/states/objective.json}"

STA="${2:-$ROOT_DIR/runtime/states/states.json}"

  

for f in "$OBJ" "$STA"; do

[ -f "$f" ] && continue

echo "❌ 文件不存在: $f"

exit 1

done

  

cd "$ROOT_DIR"

  

# ── 读取 JSON ───────────────────────────────────────────────────────────────

exec uv run python3 - "$OBJ" "$STA" "$ROOT_DIR" <<'PY_SCRIPT'

import json, sys, shlex

from pathlib import Path

  

obj_path, sta_path, root_dir = sys.argv[1], sys.argv[2], sys.argv[3]

root = Path(root_dir).resolve()

obj = json.loads(Path(obj_path).read_text(encoding="utf-8"))

sta = json.loads(Path(sta_path).read_text(encoding="utf-8"))

  

# ── 提取字段（带默认值）───────────────────────────────────────────────────────

project_root = Path(obj.get("project_root", ".")).resolve()

command = obj["command"]

remote = obj.get("remote", False)

hosts = obj.get("hosts", [])

devices = obj.get("devices", ["mps"])

num_steps = obj.get("num_training_steps", 50)

eval_n_steps = obj.get("eval_n_steps", 50)

exp_name = sta.get("exp_name", "exp_0000")

iteration = sta.get("iteration", 0)

current_step = sta.get("current_step", "A")

  

# ── 设备计算 ─────────────────────────────────────────────────────────────────

is_mps = any(d.strip().lower() == "mps" for d in devices)

gpu_ids = [d.strip() for d in devices if d.strip().lower() != "mps"]

cuda_visible = ",".join(gpu_ids) if gpu_ids else ""

  

# ── 参数追加 ────────────────────────────────────────────────────────────────

command_str = str(command)

extra_args = ""

if "--num_training_steps" not in command_str:

extra_args += f" --num_training_steps {num_steps}"

if "--eval_n_steps" not in command_str and "--eval-steps" not in command_str and "--eval-every" not in command_str:

extra_args += f" --eval_n_steps {eval_n_steps}"

extra_args += f" --exp-name {shlex.quote(exp_name)}"

  

full_command = command_str + extra_args

  

# ── 输出路径 ─────────────────────────────────────────────────────────────────

output_dir = root / "runtime/scripts/launchscripts"

output_dir.mkdir(parents=True, exist_ok=True)

output_path = output_dir / f"launch_{exp_name}.sh"

  

lines = [

"#!/usr/bin/env bash",

"# ==============================================================================",

f"# launch_{exp_name}.sh — 由 generate_launch.sh 自动生成",

f"# 实验: {exp_name}",

f"# 迭代: {iteration}",

f"# 步数: {num_steps} 步, 每 {eval_n_steps} 步验证",

f"# 设备: {', '.join(devices)}",

"# ==============================================================================",

"set -euo pipefail",

"",

]

  

# ── 本地模式 ─────────────────────────────────────────────────────────────────

if not remote:

lines += [

f'SCRIPT_DIR="{shlex.quote(str(project_root))}"',

'cd "$SCRIPT_DIR"',

"",

'# ── 激活 uv 环境 ─────────────────────────────────────────────────────',

'VENV_DIR="$SCRIPT_DIR/.venv"',

'if [ ! -d "$VENV_DIR" ]; then',

' echo "❌ 未找到 uv 虚拟环境: $VENV_DIR"',

' exit 1',

'fi',

'export PATH="$VENV_DIR/bin:$PATH"',

'export VIRTUAL_ENV="$VENV_DIR"',

"",

]

  

if is_mps:

lines += [

'# ── MPS (Apple Silicon) ───────────────────────────────────────────',

'export CUDA_VISIBLE_DEVICES=""',

]

elif cuda_visible:

lines += [

'# ── NVIDIA GPU ────────────────────────────────────────────────────',

f'export CUDA_VISIBLE_DEVICES="{cuda_visible}"',

]

else:

lines += [

'# ── GPU 检测（未显式指定） ────────────────────────────────────────',

'if [ -z "${CUDA_VISIBLE_DEVICES:-}" ]; then',

' if command -v nvidia-smi &>/dev/null && nvidia-smi -L &>/dev/null; then',

' GPU_COUNT=$(nvidia-smi -L | wc -l)',

' if [ "$GPU_COUNT" -eq 0 ]; then',

' export CUDA_VISIBLE_DEVICES=""',

' else',

' export CUDA_VISIBLE_DEVICES=$(seq -s, 0 $((GPU_COUNT - 1)))',

' fi',

' else',

' export CUDA_VISIBLE_DEVICES=""',

' fi',

'fi',

]

  

lines += [

"",

'# ── 打印环境 ──────────────────────────────────────────────────────────',

'echo "═══ 训练环境 ════════════════════════════════════════════"',

f'echo " 实验 : {exp_name}"',

f'echo " 迭代 : {iteration}"',

f'echo " 步数 : {num_steps} | 验证间隔: {eval_n_steps}"',

f'echo " 设备 : {", ".join(devices)}"',

'echo " CUDA_VISIBLE_DEVICES: ${CUDA_VISIBLE_DEVICES:-<空>}"',

'echo "═══════════════════════════════════════════════════════════"',

"",

'# ── 启动训练 ──────────────────────────────────────────────────────────',

f'echo "➜ {full_command}"',

'exec uv run python ' + shlex.quote(str(command)) + extra_args,

"",

]

  

# ── 远程模式（多级跳板 SSH） ──────────────────────────────────────────────────

else:

if not hosts:

print("❌ remote=true 但 hosts 为空，跳过生成", file=sys.stderr)

sys.exit(1)

  

if len(hosts) == 1:

ssh_target = hosts[0]

jump_list = ""

proxy_opt = ""

else:

jump_list = ",".join(hosts[:-1])

ssh_target = hosts[-1]

proxy_opt = f"-J {jump_list}"

  

proxy_flag = f"-o ProxyJump={jump_list}" if jump_list else ""

  

lines += [

"#!/usr/bin/env bash",

"# ==============================================================================",

f"# launch_{exp_name}.sh — 由 generate_launch.sh 自动生成（远程模式）",

f"# 实验: {exp_name} 迭代: {iteration}",

f"# 跳板链: {' → '.join(hosts)}",

f"# 设备: {', '.join(devices)}",

"# ==============================================================================",

"set -euo pipefail",

"",

f'REMOTE_HOST="{ssh_target}"',

f'PROXY_OPT="{proxy_opt}"',

f'PROXY_FLAG="{proxy_flag}"',

f'EXP_NAME="{exp_name}"',

f'SCRIPT_DIR="{shlex.quote(str(project_root))}"',

f'REMOTE_CMD="{full_command}"',

"",

'# ── 1. 同步代码到远程 ────────────────────────────────────────────────',

'echo "➜ 同步代码到 $REMOTE_HOST ..."',

'RSYNC_OPTS=(-avz --delete --exclude .venv --exclude __pycache__ --exclude .git)',

'if [ -n "$PROXY_FLAG" ]; then',

' rsync "${RSYNC_OPTS[@]}" -e "ssh $PROXY_FLAG" "$SCRIPT_DIR"/ "$REMOTE_HOST":"$SCRIPT_DIR"/',

'else',

' rsync "${RSYNC_OPTS[@]}" "$SCRIPT_DIR"/ "$REMOTE_HOST":"$SCRIPT_DIR"/',

'fi',

"",

'# ── 2. 远程启动训练 ──────────────────────────────────────────────────',

'echo "➜ 在 $REMOTE_HOST 上启动训练..."',

"SSH_CMD=",

'if [ -n "$PROXY_OPT" ]; then',

f' SSH_CMD="ssh $PROXY_OPT $REMOTE_HOST"',

'else',

f' SSH_CMD="ssh $REMOTE_HOST"',

'fi',

"",

]

  

if is_mps:

lines += [

'REMOTE_GPU_ENV="export CUDA_VISIBLE_DEVICES=\\"\\""',

]

elif cuda_visible:

lines += [

f'REMOTE_GPU_ENV="export CUDA_VISIBLE_DEVICES=\\"{cuda_visible}\\""',

]

else:

lines += [

'REMOTE_GPU_ENV="export CUDA_VISIBLE_DEVICES=\\"0\\""',

]

  

lines += [

"",

'REMOTE_FULL_CMD=$(cat <<-REMOTE_SCRIPT',

f' cd {shlex.quote(str(project_root))}',

' $REMOTE_GPU_ENV',

f' mkdir -p {shlex.quote(str(project_root))}/logs',

f' nohup {full_command} > {shlex.quote(str(project_root))}/logs/{exp_name}.train.log 2>&1 &',

' echo "训练进程 PID: $!"',

'REMOTE_SCRIPT',

')',

"",

'echo "═══ 远程训练启动 ═══════════════════════════════════════"',

f'echo " 目标 : {ssh_target}"',

f'echo " 跳板 : {jump_list if jump_list else "<无>"}"',

f'echo " 实验 : {exp_name}"',

f'echo " 设备 : {", ".join(devices)}"',

f'echo " 日志 : {shlex.quote(str(project_root))}/logs/{exp_name}.train.log"',

'echo "═══════════════════════════════════════════════════════════"',

"",

'eval "$SSH_CMD" "$REMOTE_FULL_CMD"',

"",

]

  

# ── 写出文件 ─────────────────────────────────────────────────────────────────

output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

output_path.chmod(0o755)

  

print(f"✅ 生成: {output_path}")

print(f" 模式: {'远程 (' + ' → '.join(hosts) + ')' if remote else '本地'}")

print(f" 设备: {', '.join(devices)}")

print(f" 命令: {full_command}")

PY_SCRIPT
```

