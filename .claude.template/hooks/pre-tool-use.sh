#!/usr/bin/env bash
set -euo pipefail

# pre-tool-use.sh - 工具调用前执行
# 记录 tool pre-use event，不阻塞正常工具执行

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="${SCRIPT_DIR}/../../runtime"

TOOL_NAME="${TOOL_NAME:-unknown}"

"$SCRIPT_DIR/../scripts/emit_log_event.sh" DEBUG "Tool about to use: $TOOL_NAME" "tool-pre-use" 2>/dev/null || true
