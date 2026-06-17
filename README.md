# oh-my-autoresearch

## 项目目的

`oh-my-autoresearch` 是一个面向神经架构搜索/自动研究的 Claude Code 子模块（submodule），提供完整的自动研究循环（Research Loop）能力：

- **team-lead 主程序**：定义 `.claude/CLAUDE.md`，驱动状态机、调度脚本、调用 subagent、控制训练
- **Observer Sidecar**：独立后台进程，负责所有 DB/Knowledge 写入，通过事件驱动架构保证写入安全
- **Observer 独立 LLM**：在每轮迭代收尾时自主总结实验成果，生成自然语言 observation 并更新知识库
- **Subagents**：在 `.claude/agents/` 中定义，仅返回结构化 JSON，不直接写 runtime
- **Runtime 模板**：包含状态机状态、知识文件、Schema 契约、公共脚本、Observer

## 安装方式

```bash
git submodule add <repository-url> agent-system/oh-my-autoresearch
cd agent-system/oh-my-autoresearch
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
5. **Phase 9 - 经验回收**：分析训练结果，更新 knowledge 库；observer 独立 LLM 自动生成 observation

## 角色职责

| 角色 | 职责 | 边界 |
|------|------|------|
| team-lead | 状态机执行、脚本调度、subagent 调用 | 不直接写 DB/knowledge |
| observer | 事件消费、DB 写入、知识管理 | 不读项目源码、不参与推理 |
| observer LLM | 在 Phase 9 自主总结本轮实验为自然语言 observation | 配置独立于主程序 LLM |
| subagents | 方向探索、代码修改、架构/数学/数值评审 | 返回 JSON，不写 runtime |

## Observer 独立 LLM 配置

Observer Sidecar 配备**独立于主程序的 LLM 配置**，在每轮迭代收尾时自主工作：

### 配置文件

```
runtime/observer/llm.config.json
```

由 `llm.config.example.json` 模板复制而来，用户需自行填入：

```json
{
  "enabled": false,
  "base_url": "https://api.anthropic.com",
  "api_key": "",
  "model": "",
  "max_tokens": 1024,
  "temperature": 0.3,
  "timeout": 60,
  "feedback_target": "learned"
}
```

| 字段 | 说明 |
|------|------|
| `enabled` | 是否启用 LLM 生成 observation |
| `base_url` | API 端点（默认 Anthropic） |
| `api_key` | API 密钥（需用户填写） |
| `model` | 模型名（需用户填写，与主程序模型独立） |
| `max_tokens` / `temperature` / `timeout` | 生成参数 |
| `feedback_target` | 观察结果的存储目标（默认 `learned`） |

### 工作时机

在 Phase 9（经验回收阶段），team-lead emit `state` 事件 `current_step=9` 后，observer 自主执行：

1. 读取本轮完整上下文（state、exploration、训练指标）
2. 调用独立 LLM 将实验成果总结为自然语言 observation
3. 持久化到 `runtime/observer/observations/`（sqlite + jsonl）
4. 将洞察追加到 `runtime/knowledges/learned.json` 供下一轮参考

整个过程由 observer 自主完成，team-lead 不参与、不调用、不等待。

## 最小运行示例

```bash
# 1. 初始化 objective
cp runtime/states/objective.example.json runtime/states/objective.json
# 编辑 objective.json 填入你的训练配置

# 2. 首次启动
# 在 Claude Code 中执行
/loop
```

## 常见问题

- 详见 `docs/troubleshooting.md`
- Observer 未启动 → 检查 `runtime/observer/run/observer.status`
- Schema 校验失败 → 检查 `runtime/states/` 下的 JSON 文件
- SQLite 写入失败 → 确认 Observer 进程正在运行
- Observer LLM 未生效 → 检查 `runtime/observer/llm.config.json` 的 `enabled` 和 `api_key`
