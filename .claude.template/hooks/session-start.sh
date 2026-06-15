#!/usr/bin/env bash
set -euo pipefail

# session-start.sh - Claude Code session 启动时执行
# 只启动 observer sidecar；不写 observation log，避免 session 噪声。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="${SCRIPT_DIR}/../../runtime"

echo "[session-start] 启动 observer sidecar ..."

# 启动 observer
if [[ -x "$RUNTIME_ROOT/observer/scripts/lifecycle/start_observer.sh" ]]; then
    "$RUNTIME_ROOT/observer/scripts/lifecycle/start_observer.sh" "$RUNTIME_ROOT" 2>/dev/null || true
fi

echo "[session-start] 完成"
