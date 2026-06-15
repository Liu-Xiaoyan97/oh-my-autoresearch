#!/usr/bin/env bash
set -euo pipefail

# stop.sh - Claude Code session 停止时执行
# 只停止 observer sidecar；不写 observation log，避免 session 噪声。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="${SCRIPT_DIR}/../../runtime"

echo "[stop] 停止 observer sidecar ..."
if [[ -x "$RUNTIME_ROOT/observer/scripts/lifecycle/stop_observer.sh" ]]; then
    "$RUNTIME_ROOT/observer/scripts/lifecycle/stop_observer.sh" "$RUNTIME_ROOT" 2>/dev/null || true
fi

echo "[stop] 清理 observer.pid ..."
rm -f "$RUNTIME_ROOT/observer/run/observer.pid" 2>/dev/null || true

echo "[stop] 完成"
