#!/usr/bin/env bash
set -euo pipefail

# restart_observer.sh - 重启 observer
# 用法: restart_observer.sh <runtime_root>

RUNTIME_ROOT="${1:-.}"

echo "→ 停止 observer ..."
"$RUNTIME_ROOT/observer/scripts/lifecycle/stop_observer.sh" "$RUNTIME_ROOT"

echo "→ 启动 observer ..."
"$RUNTIME_ROOT/observer/scripts/lifecycle/start_observer.sh" "$RUNTIME_ROOT"

echo "→ 重启完成"
