#!/usr/bin/env bash
set -euo pipefail

# call_runtime_script.sh - 轻量 wrapper，调用 runtime/scripts/*
# 用法: call_runtime_script.sh <script_name> [args...]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="${SCRIPT_DIR}/../../runtime"
PYTHON="$(cd "$SCRIPT_DIR/../.." && pwd)/.venv/bin/python3"
SCRIPT_NAME="${1:-}"
shift || true

if [[ -z "$SCRIPT_NAME" ]]; then
    echo "用法: $0 <script_name> [args...]"
    exit 1
fi

SCRIPT_PATH="$RUNTIME_ROOT/scripts/$SCRIPT_NAME"

if [[ ! -x "$SCRIPT_PATH" ]]; then
    echo "错误: 脚本不存在或不可执行: $SCRIPT_PATH"
    exit 1
fi

# 用 mktemp 创建临时文件（/tmp 由系统自动清理）
STDOUT_FILE="$(mktemp)"
STDERR_FILE="$(mktemp)"
set +e
"$SCRIPT_PATH" "$@" >"$STDOUT_FILE" 2>"$STDERR_FILE"
EXIT_CODE=$?
set -e

# 返回统一 tool-result JSON
"$PYTHON" - "$SCRIPT_PATH" "$EXIT_CODE" "$STDOUT_FILE" "$STDERR_FILE" <<'PY'
import json
import sys
from pathlib import Path

command, exit_code, stdout_file, stderr_file = sys.argv[1:5]
stdout = Path(stdout_file).read_text(encoding="utf-8", errors="replace")
stderr = Path(stderr_file).read_text(encoding="utf-8", errors="replace")
payload = {
    "command": command,
    "exit_code": int(exit_code),
    "stdout": "\n".join(stdout.splitlines()[:100]),
    "stderr": "\n".join(stderr.splitlines()[:100]),
    "status": "success" if int(exit_code) == 0 else "failure",
    "parsed_payload": None,
}
print(json.dumps(payload, ensure_ascii=False, indent=2))
PY
rm -f "$STDOUT_FILE" "$STDERR_FILE"
exit "$EXIT_CODE"
