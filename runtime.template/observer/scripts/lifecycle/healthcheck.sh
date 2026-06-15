#!/usr/bin/env bash
set -euo pipefail

# healthcheck.sh - 检查 observer 健康状态
# 用法: healthcheck.sh <runtime_root>

RUNTIME_ROOT="${1:-.}"
RUN_DIR="$RUNTIME_ROOT/observer/run"
PID_FILE="$RUN_DIR/observer.pid"
PASS=0
FAIL=0

check() {
    local name="$1"
    local result="$2"
    if [[ "$result" == "0" ]]; then
        echo "  [OK] $name"
        PASS=$((PASS + 1))
    else
        echo "  [FAIL] $name"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Observer Healthcheck ==="

# 1. pid 是否存在
if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if [[ -n "$PID" ]]; then
        check "PID 文件存在" "0"
    else
        check "PID 文件存在" "1"
    fi
else
    check "PID 文件存在" "1"
fi

# 2. 进程是否存活
if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        check "Observer 进程存活 (PID: $PID)" "0"
    else
        check "Observer 进程存活" "1"
    fi
else
    check "Observer 进程存活" "1"
fi

# 3. events 是否可写
if [[ -w "$RUNTIME_ROOT/observer/events/events.jsonl" ]]; then
    check "Events 文件可写" "0"
else
    check "Events 文件可写" "1"
fi

# 4. DB 是否可写
if [[ -w "$RUNTIME_ROOT/db" ]]; then
    check "DB 目录可写" "0"
else
    check "DB 目录可写" "1"
fi

# 5. Observations 是否可写
if [[ -w "$RUNTIME_ROOT/observations" ]]; then
    check "Observations 目录可写" "0"
else
    check "Observations 目录可写" "1"
fi

# 6. Knowledges 是否可写
if [[ -w "$RUNTIME_ROOT/knowledges" ]]; then
    check "Knowledges 目录可写" "0"
else
    check "Knowledges 目录可写" "1"
fi

echo ""
echo "结果: $PASS OK, $FAIL FAIL"
[[ $FAIL -eq 0 ]]
