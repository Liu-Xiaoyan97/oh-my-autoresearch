#!/usr/bin/env bash
set -euo pipefail

# start_training.sh - 通过 nohup 启动训练
# nohup runtime/launchscripts/launch_<exp_name>.sh > runtime/logs/train-of-<exp_name>.log 2>&1 &
# 返回 PID
# 用法: start_training.sh <repo_root> <exp_name>

REPO_ROOT="${1:-.}"
EXP_NAME="${2:-}"

if [[ -z "$EXP_NAME" ]]; then
    echo "用法: start_training.sh <repo_root> <exp_name>"
    exit 1
fi

LAUNCH_SCRIPT="$REPO_ROOT/launchscripts/launch_${EXP_NAME}.sh"
LOG_DIR="$REPO_ROOT/logs"
LOG_FILE="$LOG_DIR/train-of-${EXP_NAME}.log"

mkdir -p "$LOG_DIR"

if [[ ! -x "$LAUNCH_SCRIPT" ]]; then
    echo "错误: launch script 不存在或不可执行: $LAUNCH_SCRIPT"
    exit 1
fi

nohup "$LAUNCH_SCRIPT" > "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID"
