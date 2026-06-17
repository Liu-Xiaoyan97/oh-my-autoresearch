#!/usr/bin/env bash
# revert_to_baseline.sh — 将 project_root 重置到 baseline.json 对应的 commit。
#
# 读取 runtime/knowledges/baseline.json，从中获取 commit_id 和 exp_name，
# 将 project_root checkout 到该基线 commit，确保每轮实验从干净基线开始。
#
# 处理两种 commit_id：
#   1. 真实 SHA（40 位 hex）→ 直接 git checkout
#   2. sentinel 值（如 remote-sync:xxx）→ 按 exp_name 搜索 git log
#
# 用法: revert_to_baseline.sh [runtime_root]
# 返回: 0（成功或跳过）, 1（失败但非阻塞）

set -euo pipefail

RUNTIME_ROOT="${1:-runtime}"
BASELINE_FILE="${RUNTIME_ROOT}/knowledges/baseline.json"
OBJECTIVE_FILE="${RUNTIME_ROOT}/states/objective.json"

# 1) 无 baseline → 跳过（首轮迭代）
if [ ! -f "$BASELINE_FILE" ]; then
    echo "[revert_to_baseline] 无 baseline.json，跳过"
    exit 0
fi

# 2) 从 baseline.json 解析 commit_id 和 exp_name
COMMIT_ID=$(python3 -c "
import json
bl = json.load(open('$BASELINE_FILE'))
print(bl.get('commit_id', '') or '')
" 2>/dev/null || true)

BASELINE_EXP=$(python3 -c "
import json
bl = json.load(open('$BASELINE_FILE'))
print(bl.get('exp_name', '') or '')
" 2>/dev/null || true)

if [ -z "$COMMIT_ID" ] && [ -z "$BASELINE_EXP" ]; then
    echo "[revert_to_baseline] baseline.json 无 commit_id 和 exp_name，跳过"
    exit 0
fi

# 3) 读取 project_root
PROJECT_ROOT=$(python3 -c "
import json
obj = json.load(open('$OBJECTIVE_FILE'))
print(obj.get('project_root', ''))
" 2>/dev/null || true)

if [ -z "$PROJECT_ROOT" ]; then
    echo "[revert_to_baseline] 无法读取 project_root，跳过"
    exit 0
fi

# 4) project_root 无 git 仓库 → 跳过
if [ ! -d "${PROJECT_ROOT}/.git" ]; then
    echo "[revert_to_baseline] project_root 无 git 仓库，跳过"
    exit 0
fi

cd "$PROJECT_ROOT"

TARGET=""

# 5a) 如果 commit_id 是真实 SHA（40 位 hex），直接用它
if echo "$COMMIT_ID" | grep -qE '^[0-9a-f]{40}$'; then
    TARGET="$COMMIT_ID"
# 5b) 否则（sentinel 或空），按 exp_name 搜索 git log
elif [ -n "$BASELINE_EXP" ]; then
    TARGET=$(git log --all --oneline --grep="$BASELINE_EXP" --format='%H' | head -1 || true)
    if [ -z "$TARGET" ]; then
        echo "[revert_to_baseline] 在 git 日志中未找到 '$BASELINE_EXP'，跳过"
        exit 0
    fi
    echo "[revert_to_baseline] 从 git log 匹配 '$BASELINE_EXP' → commit $TARGET"
else
    echo "[revert_to_baseline] 无法解析目标 commit，跳过"
    exit 0
fi

# 6) 已在目标 commit → 跳过
CURRENT=$(git rev-parse HEAD 2>/dev/null || true)
if [ "$CURRENT" = "$TARGET" ]; then
    echo "[revert_to_baseline] 已在基线 commit，无需回退"
    exit 0
fi

# 7) 重置到基线
echo "[revert_to_baseline] baseline=$BASELINE_EXP commit=$TARGET, 当前=$CURRENT, 执行 reset..."
git reset --hard "$TARGET"
echo "[revert_to_baseline] ✅ project_root 已重置到基线 commit $TARGET"
