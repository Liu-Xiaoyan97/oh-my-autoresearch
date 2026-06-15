#!/usr/bin/env bash
set -euo pipefail

# session-start.sh - Claude Code session 启动时执行
# 启动 observer sidecar，初始化 observer 环境

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="${SCRIPT_DIR}/../../runtime"

echo "[session-start] 启动 observer sidecar ..."

# 启动 observer
if [[ -x "$RUNTIME_ROOT/observer/scripts/lifecycle/start_observer.sh" ]]; then
    "$RUNTIME_ROOT/observer/scripts/lifecycle/start_observer.sh" "$RUNTIME_ROOT" 2>/dev/null || true
fi

"$SCRIPT_DIR/../scripts/emit_log_event.sh" INFO "Claude Code session started" "session-start" 2>/dev/null || true

echo "[session-start] 完成"
