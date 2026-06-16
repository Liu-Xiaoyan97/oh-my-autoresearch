#!/usr/bin/env bash
set -euo pipefail

# commit_changes.sh - 在 project_root 自身的 git 仓库提交变更
# 用法: commit_changes.sh <project_root> <message>
#
# project_root 是被优化项目，必须用它**自己的** git 仓库管理，
# 绝不把变更提交到宿主 research-runtime 整仓。若 project_root 尚无 .git，则先初始化。

PROJECT_ROOT="${1:-.}"
MESSAGE="${2:-autoresearch experiment update}"

cd "$PROJECT_ROOT"

# 确保 project_root 是独立 git 仓库（无则初始化），避免 git 命令上溯到宿主仓库
if [[ ! -d .git ]]; then
    git init -q
    # 项目级忽略：仅追踪源码，生成物/产物不入库
    if [[ ! -f .gitignore ]]; then
        cat > .gitignore <<'IGN'
__pycache__/
*.pyc
output/
runtime/
launchscripts/
.venv/
IGN
    fi
fi

if [[ -z "$(git status --short)" ]]; then
    echo "无变更可提交" >&2
    exit 1
fi

git add -A
git commit -m "$MESSAGE" >/dev/null
git rev-parse HEAD
