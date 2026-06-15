#!/usr/bin/env bash
set -euo pipefail

# commit_changes.sh - 提交研究仓库变更
# 用法: commit_changes.sh <project_root> <message>

PROJECT_ROOT="${1:-.}"
MESSAGE="${2:-autoresearch experiment update}"

cd "$PROJECT_ROOT"

if [[ -z "$(git status --short)" ]]; then
    echo "无变更可提交" >&2
    exit 1
fi

git add -A
git commit -m "$MESSAGE" >/dev/null
git rev-parse HEAD
