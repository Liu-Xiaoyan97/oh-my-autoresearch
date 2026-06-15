# Subagents

## 定义位置

所有 subagent 定义在 `.claude/agents/` 目录下。

## 约束

- 只返回结构化 JSON
- 不直接写 runtime
- 不写 DB
- 不写日志
- 不改 states

## 各 Subagent 职责

### orthogonal-direction-scout

接收 baseline、learned、rejected、objective、模型上下文，并行参考三个 reviewer 的建议，输出去重后的正交候选集。

**输入上下文**: objective, baseline, learned, rejected, 模型元信息

**输出 schema**: `runtime/agents/orthogonal-direction-scout/schemas/orthogonal-set.schema.json`

### summarizer

Phase 1: 汇总候选集和三方评分，输出最高票决策。
Phase 9: 汇总三方训练结果分析，输出经验回收总结。

**输入上下文**: 各 reviewer 的 proposal/vote/recovery

**输出 schema**: `decision.schema.json` / `recovery-summary.schema.json`

### coder

根据 summarizer 的 decision 修改研究仓库代码，生成 patch plan，执行冒烟测试，调用 runtime coding/training/git 脚本，输出 commit result。

**输入上下文**: decision, patch plan schema

**输出 schema**: `commit-result.schema.json`

### flow-arch-reviewer

从模型结构、数据流、模块边界角度提出优化候选，对候选方案评分。Phase 9 从架构角度总结经验或教训。

**输入上下文**: baseline, candidate proposals

**输出 schema**: `proposal.schema.json`, `vote.schema.json`, `recovery.schema.json`

### math-theorist

从目标函数、正则化、优化理论、表示空间角度提出候选，对候选方案评分。Phase 9 从数学角度总结经验或教训。

**输入上下文**: baseline, candidate proposals

**输出 schema**: `proposal.schema.json`, `vote.schema.json`, `recovery.schema.json`

### numerical-debugger

从 loss、梯度、初始化、归一化、精度、爆炸/消失等数值角度提出候选，对候选方案评分。Phase 9 从数值稳定性角度总结经验或教训。

**输入上下文**: baseline, training logs, candidate proposals

**输出 schema**: `proposal.schema.json`, `vote.schema.json`, `recovery.schema.json`
