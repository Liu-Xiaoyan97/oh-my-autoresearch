#!/usr/bin/env bash
set -euo pipefail

# call_runtime_script.sh - 轻量 wrapper，调用 runtime/scripts/*
# 用法: call_runtime_script.sh <script_name> [args...]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="${SCRIPT_DIR}/../../runtime"
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

# 用 python3 subprocess 在内存中捕获 stdout/stderr，零临时文件
set +e
python3 - "$SCRIPT_PATH" "$@" <<'PY' 2>&1
import json, subprocess, sys

script_path = sys.argv[1]
args = sys.argv[2:]
result = subprocess.run([script_path] + args, capture_output=True, text=True, timeout=600)
payload = {
    "command": script_path,
    "exit_code": result.returncode,
    "stdout": "\n".join(result.stdout.splitlines()[:100]),
    "stderr": "\n".join(result.stderr.splitlines()[:100]),
    "status": "success" if result.returncode == 0 else "failure",
    "parsed_payload": None,
}
print(json.dumps(payload, ensure_ascii=False, indent=2))
sys.exit(result.returncode)
PY
EXIT_CODE=$?
set -e
exit "$EXIT_CODE"
