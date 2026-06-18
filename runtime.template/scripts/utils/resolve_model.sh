#!/usr/bin/env bash
# resolve_model.sh — 从 objective.json 读取 model 字段并输出。
# 用法: resolve_model.sh [runtime_root]
# 输出: model 字段的短名称（sonnet / opus / haiku / fable），默认 haiku
#
# team-lead 在 spawn subagent 前调用此脚本，将结果作为 Agent 调用的 model 参数。
# 所有 agent prompt 中的 ${model} 占位符由 team-lead 在 spawn 时填入此值。
# Agent tool 的 model 参数优先级高于 agent .md 定义中的 model frontmatter。

set -uo pipefail

RUNTIME_ROOT="${1:-runtime}"
OBJECTIVE_FILE="${RUNTIME_ROOT}/states/objective.json"

if [ ! -f "$OBJECTIVE_FILE" ]; then
    echo "haiku"
    exit 0
fi

python3 -c "
import json, sys
valid = {'sonnet', 'opus', 'haiku', 'fable'}
try:
    obj = json.load(open('${OBJECTIVE_FILE}'))
    model = obj.get('model', 'haiku')
    if isinstance(model, str) and model.strip().lower() in valid:
        print(model.strip().lower())
    else:
        print('haiku')
except Exception:
    print('haiku')
"
