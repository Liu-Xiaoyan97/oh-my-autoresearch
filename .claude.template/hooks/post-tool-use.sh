#!/usr/bin/env bash
set -euo pipefail

# post-tool-use.sh - 工具调用后执行
# 记录 tool post-use event，包含 exit code、耗时、工具名称

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="${SCRIPT_DIR}/../../runtime"

TOOL_NAME="${TOOL_NAME:-unknown}"
EXIT_CODE="${EXIT_CODE:-0}"
DURATION="${DURATION:-0}"

"$SCRIPT_DIR/../scripts/emit_log_event.sh" DEBUG "Tool $TOOL_NAME completed with exit_code=$EXIT_CODE, duration=${DURATION}ms" "tool-post-use" 2>/dev/null || true
