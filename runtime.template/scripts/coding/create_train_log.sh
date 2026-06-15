#!/usr/bin/env bash
set -euo pipefail

# create_train_log.sh - 创建训练日志文件
# 用法: create_train_log.sh <runtime_root> <exp_name>

RUNTIME_ROOT="${1:-runtime}"
EXP_NAME="${2:-}"

if [[ -z "$EXP_NAME" ]]; then
    echo "用法: create_train_log.sh <runtime_root> <exp_name>" >&2
    exit 1
fi

LOG_DIR="$RUNTIME_ROOT/logs"
LOG_FILE="$LOG_DIR/train-of-${EXP_NAME}.log"
mkdir -p "$LOG_DIR"
touch "$LOG_FILE"
echo "$LOG_FILE"
