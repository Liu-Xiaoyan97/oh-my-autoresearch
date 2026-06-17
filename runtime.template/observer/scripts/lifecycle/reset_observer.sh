#!/usr/bin/env bash
set -euo pipefail

# reset_observer.sh - 清空 observer 的 events / offsets / run 三个目录产物并重启 observer。
# 供 /loop-reset 调用。保留各目录 .gitkeep。
# 安全顺序：停 observer → 清空(无在途事件竞态) → 重启。
# 用法: reset_observer.sh <runtime_root>

RUNTIME_ROOT="${1:-.}"
LIFE="$RUNTIME_ROOT/observer/scripts/lifecycle"
EVENTS_DIR="$RUNTIME_ROOT/observer/events"
OFFSETS_DIR="$RUNTIME_ROOT/observer/offsets"
RUN_DIR="$RUNTIME_ROOT/observer/run"

echo "→ 停止 observer ..."
"$LIFE/stop_observer.sh" "$RUNTIME_ROOT" || true

echo "→ 清空 events/ (保留 .gitkeep) ..."
mkdir -p "$EVENTS_DIR"
find "$EVENTS_DIR" -mindepth 1 -maxdepth 1 ! -name '.gitkeep' -exec rm -f {} +

echo "→ 重置 offsets/ (保留 .gitkeep) ..."
mkdir -p "$OFFSETS_DIR"
find "$OFFSETS_DIR" -mindepth 1 -maxdepth 1 ! -name '.gitkeep' -exec rm -f {} +

echo "→ 清空 run/ (保留 .gitkeep) ..."
mkdir -p "$RUN_DIR"
find "$RUN_DIR" -mindepth 1 -maxdepth 1 ! -name '.gitkeep' -exec rm -f {} +

echo "→ 重启 observer ..."
"$LIFE/start_observer.sh" "$RUNTIME_ROOT"
echo "→ observer events/offsets/run 已清空并重启完成"
