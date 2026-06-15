#!/usr/bin/env bash
set -euo pipefail

# latest_commit.sh - 返回当前仓库最近一次 commit id
# 用法: latest_commit.sh <repo_root>

REPO_ROOT="${1:-.}"

git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo "no-git"
