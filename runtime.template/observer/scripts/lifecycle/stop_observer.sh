#!/usr/bin/env bash
set -euo pipefail

# stop_observer.sh - 停止 observer daemon
# 用法: stop_observer.sh <runtime_root>

RUNTIME_ROOT="${1:-.}"
RUN_DIR="$RUNTIME_ROOT/observer/run"
PID_FILE="$RUN_DIR/observer.pid"

if [[ ! -f "$PID_FILE" ]]; then
    echo "Observer PID 文件不存在"
    exit 0
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
    echo "发送 SIGTERM 到 observer (PID: $PID) ..."
    kill -TERM "$PID"
    # 等待退出
    for i in $(seq 1 10); do
        if ! kill -0 "$PID" 2>/dev/null; then
            break
        fi
        sleep 1
    done
    # 强制终止
    if kill -0 "$PID" 2>/dev/null; then
        kill -9 "$PID" 2>/dev/null || true
    fi
    echo "Observer 已停止"
else
    echo "Observer 进程不存在 (PID: $PID)"
fi

rm -f "$PID_FILE"
