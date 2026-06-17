#!/usr/bin/env bash
# resolve_goal.sh — 从 objective.json 读取 goal 字段并输出。
# 用法: resolve_goal.sh [runtime_root]
# 输出: goal 字段的纯文本值（单行，无换行控制字符，无引号）
#
# team-lead 在 spawn subagent 前调用此脚本，将结果注入 subagent 上下文。
# 所有 agent prompt 中的 ${goal} 占位符由 team-lead 在 spawn 时填入此值。

set -euo pipefail

RUNTIME_ROOT="${1:-runtime}"
OBJECTIVE_FILE="${RUNTIME_ROOT}/states/objective.json"

if [ ! -f "$OBJECTIVE_FILE" ]; then
    echo "[resolve_goal] 错误: 未找到 ${OBJECTIVE_FILE}" >&2
    exit 1
fi

python3 -c "
import json, sys
try:
    obj = json.load(open('${OBJECTIVE_FILE}'))
    goal = obj.get('goal', '')
    if goal:
        single = goal.replace('\n', ' ').replace('\r', '')
        print(single)
    else:
        print('[resolve_goal] 警告: objective.json 中无 goal 字段', file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f'[resolve_goal] 错误: {e}', file=sys.stderr)
    sys.exit(1)
"
