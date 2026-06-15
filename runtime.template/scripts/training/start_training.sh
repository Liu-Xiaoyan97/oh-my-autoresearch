#!/usr/bin/env bash
set -euo pipefail

# start_training.sh - 通过 nohup 启动训练
# nohup <objective.project_root>/launchscripts/launch_<exp_name>.sh > runtime/logs/train-of-<exp_name>.log 2>&1 &
# 返回 PID
# 用法: start_training.sh <runtime_root> <exp_name>

RUNTIME_ROOT="${1:-runtime}"
EXP_NAME="${2:-}"

if [[ -z "$EXP_NAME" ]]; then
    echo "用法: start_training.sh <repo_root> <exp_name>"
    exit 1
fi

PROJECT_ROOT="$(python3 - "$RUNTIME_ROOT" <<'PY'
import json
import sys
from pathlib import Path

runtime_root = Path(sys.argv[1]).resolve()
host_root = runtime_root.parent
objective = json.loads((runtime_root / "states" / "objective.json").read_text(encoding="utf-8"))
project_root = Path(objective.get("project_root", "."))
if not project_root.is_absolute():
    project_root = host_root / project_root
print(project_root.resolve())
PY
)"

LAUNCH_SCRIPT="$PROJECT_ROOT/launchscripts/launch_${EXP_NAME}.sh"
LOG_DIR="$RUNTIME_ROOT/logs"
LOG_FILE="$LOG_DIR/train-of-${EXP_NAME}.log"

mkdir -p "$LOG_DIR"

if [[ ! -x "$LAUNCH_SCRIPT" ]]; then
    echo "错误: launch script 不存在或不可执行: $LAUNCH_SCRIPT"
    exit 1
fi

nohup "$LAUNCH_SCRIPT" > "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID"
