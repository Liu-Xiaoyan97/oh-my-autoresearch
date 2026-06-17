#!/usr/bin/env bash
# resolve_poll_interval.sh — 从 objective.json 读取 poll_interval 字段并输出。
# 用法: resolve_poll_interval.sh [runtime_root]
# 输出: poll_interval 字段的整数值（默认 90 秒）
#
# team-lead 在创建 cron 定时任务前调用此脚本，将结果作为 cron 间隔参数。
# 所有 agent prompt 中的 ${poll_interval} 占位符由 team-lead 在 spawn 时填入此值。

set -euo pipefail

RUNTIME_ROOT="${1:-runtime}"
OBJECTIVE_FILE="${RUNTIME_ROOT}/states/objective.json"

if [ ! -f "$OBJECTIVE_FILE" ]; then
    echo "90"
    exit 0
fi

python3 -c "
import json, sys
try:
    obj = json.load(open('${OBJECTIVE_FILE}'))
    interval = obj.get('poll_interval', 90)
    if isinstance(interval, (int, float)):
        print(int(interval))
    else:
        print('90')
except Exception:
    print('90')
"
