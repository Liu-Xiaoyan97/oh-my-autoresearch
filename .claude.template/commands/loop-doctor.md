# /loop-doctor

## 描述

触发环境诊断，等价于通过 Claude 调用 `doctor.sh` 和相关 runtime validate scripts。

## 用法

在 Claude Code 中运行 `/loop-doctor`。

## 行为

1. 调用 `./doctor.sh <host-repo-root>` 执行全面环境检查
2. 调用 `runtime/scripts/validate/validate_runtime.py` 执行 Phase 0 校验
3. 输出诊断报告，列出所有 PASS/FAIL/WARN 项
4. 对 FAIL 项给出修复建议
