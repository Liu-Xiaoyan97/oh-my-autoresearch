#!/usr/bin/env bash
set -euo pipefail

# bootstrap.sh - 首次初始化脚本
# 用法: ./bootstrap.sh <host-repo-root>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_ROOT="${1:-.}"

RUNTIME="$HOST_ROOT/runtime"
DB_DIR="$RUNTIME/db"
LOGS_DIR="$RUNTIME/logs"
OBS_DIR="$RUNTIME/observations"
EVENTS_DIR="$RUNTIME/observer/events"
OFFSET_DIR="$RUNTIME/observer/offsets"
RUN_DIR="$RUNTIME/observer/run"
LAUNCH_DIR="$RUNTIME/launchscripts"

echo "=== Bootstrap 初始化 ==="

# 1. 创建缺失的 runtime 目录
echo "→ 创建缺失的 runtime 目录 ..."
for dir in "$DB_DIR" "$LOGS_DIR" "$OBS_DIR" "$EVENTS_DIR" "$OFFSET_DIR" "$RUN_DIR" "$LAUNCH_DIR"; do
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        echo "  创建: $dir"
    else
        echo "  已存在: $dir"
    fi
done

# 2. 初始化 SQLite 数据库
echo "→ 初始化 runtime/db/runtime.sqlite ..."
"$SCRIPT_DIR/runtime.template/scripts/database/init_db.py" "$RUNTIME" || true

# 3. 创建 observer 初始化文件
echo "→ 创建 observer 初始化文件 ..."
if [[ ! -f "$EVENTS_DIR/events.jsonl" ]]; then
    touch "$EVENTS_DIR/events.jsonl"
    echo "  创建: events.jsonl"
fi
if [[ ! -f "$EVENTS_DIR/deadletter.jsonl" ]]; then
    touch "$EVENTS_DIR/deadletter.jsonl"
    echo "  创建: deadletter.jsonl"
fi
if [[ ! -f "$OFFSET_DIR/events.offset" ]]; then
    echo "0" > "$OFFSET_DIR/events.offset"
    echo "  创建: events.offset"
fi

# 4. 校验 schema 文件存在
echo "→ 校验 schema 文件 ..."
SCHEMA_COUNT=$(find "$SCRIPT_DIR/runtime.template/schemas" "$RUNTIME/schemas" "$RUNTIME/observer/schemas" -name "*.schema.json" 2>/dev/null | wc -l)
echo "  找到 $SCHEMA_COUNT 个 schema 文件"

# 5. 确认 .claude 配置完整
echo "→ 确认 .claude 配置 ..."
if [[ -f "$HOST_ROOT/.claude/CLAUDE.md" ]]; then
    echo "  CLAUDE.md: OK"
else
    echo "  警告: CLAUDE.md 不存在，请先运行 install.sh"
fi

echo ""
echo "=== Bootstrap 完成 ==="
