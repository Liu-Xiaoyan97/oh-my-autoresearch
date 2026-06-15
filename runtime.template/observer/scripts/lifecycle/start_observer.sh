#!/usr/bin/env bash
set -euo pipefail

# start_observer.sh - 启动 observer daemon
# 用法: start_observer.sh <runtime_root>

RUNTIME_ROOT="${1:-.}"
RUN_DIR="$RUNTIME_ROOT/observer/run"
PID_FILE="$RUN_DIR/observer.pid"
DAEMON_SCRIPT="$RUNTIME_ROOT/observer/scripts/dispatch/observer_daemon.py"

mkdir -p "$RUN_DIR"
mkdir -p "$RUNTIME_ROOT/observer/events"
mkdir -p "$RUNTIME_ROOT/observer/offsets"

# 检查是否已有 pid
if [[ -f "$PID_FILE" ]]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Observer 已在运行 (PID: $OLD_PID)"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# 初始化事件文件
touch "$RUNTIME_ROOT/observer/events/events.jsonl"
touch "$RUNTIME_ROOT/observer/events/deadletter.jsonl"
if [[ ! -f "$RUNTIME_ROOT/observer/offsets/events.offset" ]]; then
    echo "0" > "$RUNTIME_ROOT/observer/offsets/events.offset"
fi

# 启动 daemon
nohup python3 "$DAEMON_SCRIPT" "$RUNTIME_ROOT" > "$RUNTIME_ROOT/observer/run/observer.log" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"
echo "Observer 已启动 (PID: $PID)"
