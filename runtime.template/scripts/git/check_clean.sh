#!/usr/bin/env bash
set -euo pipefail

# check_clean.sh - 检查宿主研究仓库是否存在未提交变动
# 用法: check_clean.sh <repo_root>

REPO_ROOT="${1:-.}"

if git -C "$REPO_ROOT" status --porcelain 2>/dev/null | grep -q .; then
    echo "dirty"
    git -C "$REPO_ROOT" status --short
    exit 1
else
    echo "clean"
    exit 0
fi
