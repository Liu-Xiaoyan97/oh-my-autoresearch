#!/usr/bin/env bash
set -euo pipefail

# terminate_training.sh - 结束训练进程组
# 用法: terminate_training.sh <pid>

PID="${1:-}"
if [[ -z "$PID" ]]; then
    echo "用法: terminate_training.sh <pid>" >&2
    exit 1
fi

if ! kill -0 "$PID" 2>/dev/null; then
    echo "进程不存在: $PID"
    exit 0
fi

PGID="$(ps -o pgid= -p "$PID" | tr -d ' ')"
if [[ -z "$PGID" ]]; then
    kill -TERM "$PID" 2>/dev/null || true
else
    kill -TERM "-$PGID" 2>/dev/null || true
fi

for _ in $(seq 1 10); do
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "训练已终止: $PID"
        exit 0
    fi
    sleep 1
done

if [[ -n "$PGID" ]]; then
    kill -KILL "-$PGID" 2>/dev/null || true
else
    kill -KILL "$PID" 2>/dev/null || true
fi
echo "训练已强制终止: $PID"
