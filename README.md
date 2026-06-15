# research-loop-agent

## 项目目的

`research-loop-agent` 是一个面向神经架构搜索/自动研究的 Claude Code 子模块（submodule），提供完整的自动研究循环（Research Loop）能力：

- **team-lead 主程序**：定义 `.claude/CLAUDE.md`，驱动状态机、调度脚本、调用 subagent、控制训练
- **Observer Sidecar**：独立后台进程，负责所有 DB/Knowledge 写入，通过事件驱动架构保证写入安全
- **Subagents**：在 `.claude/agents/` 中定义，仅返回结构化 JSON，不直接写 runtime
- **Runtime 模板**：包含状态机状态、知识文件、Schema 契约、公共脚本、Observer

## 安装方式

```bash
git submodule add <repository-url> agent-system/research-loop-agent
cd agent-system/research-loop-agent
./install.sh <host-repo-root>
./bootstrap.sh
```

安装后，`.claude.template/` 内容合并到宿主仓库 `.claude/`，`runtime.template/` 内容合并到宿主仓库 `runtime/`。

## `/loop` 工作流简介

运行 `/loop` 触发完整的状态机循环：

1. **Phase 0 - 初始校验**：验证 states、objective、baseline、remote 配置
2. **Phase 1 - 方向探索**：scout 并行探索正交方向，reviewer 评分，summarizer 投票
3. **Phase 2 - 代码修改**：coder 执行代码变更，冒烟测试，git commit
4. **Phase 3 - 训练监控**：启动训练，监控进度，记录指标
5. **Phase 9 - 经验回收**：分析训练结果，更新 knowledge 库

## 角色职责

| 角色 | 职责 | 边界 |
|------|------|------|
| team-lead | 状态机执行、脚本调度、subagent 调用 | 不直接写 DB/knowledge |
| observer | 事件消费、DB 写入、知识管理 | 不读项目源码、不参与推理 |
| subagents | 方向探索、代码修改、架构/数学/数值评审 | 返回 JSON，不写 runtime |

## 最小运行示例

```bash
# 1. 初始化 objective
cp runtime.template/states/objective.example.json runtime/states/objective.json
# 编辑 objective.json 填入你的训练配置

# 2. 首次启动
# 在 Claude Code 中执行
/loop
```

## 常见问题

- 详见 `docs/troubleshooting.md`
- Observer 未启动 → 检查 `runtime/observer/run/observer.pid`
- Schema 校验失败 → 检查 `runtime/states/` 下的 JSON 文件
- SQLite 写入失败 → 确认 Observer 进程正在运行
