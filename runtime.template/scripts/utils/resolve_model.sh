#!/usr/bin/env bash
# resolve_model.sh — 从 objective.json 的 model 映射中按 subagent 名称查找模型。
# 用法: resolve_model.sh <runtime_root> <subagent_name>
# 示例: resolve_model.sh runtime orthogonal-direction-scout  # → haiku
# 输出: model 短名称（haiku / sonnet / opus / fable），供 Agent tool 的 model 参数使用。
#
# 查找顺序：
#   1. objective.json["model"]["<subagent_name>"]
#   2. objective.json["model"]["default"]
#   3. 硬编码默认值 "haiku"

set -uo pipefail

RUNTIME_ROOT="${1:-runtime}"
SUBAGENT="${2:-default}"
OBJECTIVE_FILE="${RUNTIME_ROOT}/states/objective.json"

if [ ! -f "$OBJECTIVE_FILE" ]; then
    echo "haiku"
    exit 0
fi

python3 -c "
import json, sys

subagent = '${SUBAGENT}'

try:
    obj = json.load(open('${OBJECTIVE_FILE}'))
    models = obj.get('model', {})
    if isinstance(models, str):
        # 兼容旧格式：model 为单个字符串时作为所有 subagent 的模型
        model = models.strip()
        print(model.lower() if model else 'haiku')
    elif isinstance(models, dict):
        model = (models.get(subagent) or models.get('default') or 'haiku')
        model = model.strip() if isinstance(model, str) else 'haiku'
        print(model.lower() if model else 'haiku')
    else:
        print('haiku')
except Exception:
    print('haiku')
"
