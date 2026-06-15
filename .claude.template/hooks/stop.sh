#!/usr/bin/env bash
set -euo pipefail

# stop.sh - Claude Code session 停止时执行
# 发出 session stop log event，停止 observer sidecar

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="${SCRIPT_DIR}/../../runtime"

echo "[stop] 发出 session stop log event ..."
"$SCRIPT_DIR/../scripts/emit_log_event.sh" INFO "Claude Code session stopping" "session-stop" 2>/dev/null || true

echo "[stop] 停止 observer sidecar ..."
if [[ -x "$RUNTIME_ROOT/observer/scripts/lifecycle/stop_observer.sh" ]]; then
    "$RUNTIME_ROOT/observer/scripts/lifecycle/stop_observer.sh" "$RUNTIME_ROOT" 2>/dev/null || true
fi

echo "[stop] 清理 observer.pid ..."
rm -f "$RUNTIME_ROOT/observer/run/observer.pid" 2>/dev/null || true

echo "[stop] 完成"
