#!/usr/bin/env bash
set -euo pipefail

# smoke_test.sh - 在研究仓库执行轻量冒烟测试
# 用法: smoke_test.sh <project_root> [command]

PROJECT_ROOT="${1:-.}"
COMMAND="${2:-}"

cd "$PROJECT_ROOT"

if [[ -n "$COMMAND" ]]; then
    bash -lc "$COMMAND"
elif [[ -f pyproject.toml ]] || [[ -d tests ]]; then
    python3 -m pytest -q
else
    git status --short >/dev/null
fi
