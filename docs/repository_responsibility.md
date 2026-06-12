# Repository Responsibility

本系统维护三个仓库：

## 1. oh-my-autoresearch

职责：

- 工作流模板
- Claude Code commands
- Claude Code hooks
- Runtime Contract
- AgentTeam 协议
- 同步脚本
- Schema 校验

不得保存：

- 实验运行状态
- 训练结果
- 模型代码

## 2. nn-architecture

职责：

- 模型代码
- 训练代码
- 数据处理代码
- 实验配置
- 测试代码

不得保存：

- Claude Code hooks
- AgentTeam 辩论记录
- Runtime 状态文件

## 3. research-runtime

职责：

- 工作流部署侧
- workflow engine submodule
- model repo submodule
- runtime 状态
- agent 辩论历史
- 实验状态索引
- 同步记录

不得保存：

- workflow engine 源模板
- 模型源码的主副本