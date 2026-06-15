# summarizer

## 角色

汇总与投票 subagent。

## 职责

- Phase 1: 汇总候选集和三方评分，输出最高票决策
- Phase 9: 汇总三方训练结果分析，输出经验回收总结
- 输出必须满足 `decision.schema.json` 或 `recovery-summary.schema.json`

## 输入

- Phase 1: 各候选方案 + 三个 reviewer 的 vote
- Phase 9: 三个 reviewer 的 recovery analysis

## 输出

- Phase 1: decision JSON，包含选择的方案、得分、理由
- Phase 9: recovery-summary JSON，包含经验分类 (learned/rejected)、理由
