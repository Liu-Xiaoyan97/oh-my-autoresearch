#!/usr/bin/env bash
set -euo pipefail

# upgrade.sh - 升级 oh-my-autoresearch 模板文件
# 用法: ./upgrade.sh <host-repo-root>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_ROOT="${1:-.}"

CLAUDE_SRC="$SCRIPT_DIR/.claude.template"
CLAUDE_DST="$HOST_ROOT/.claude"
RUNTIME_SRC="$SCRIPT_DIR/runtime.template"
RUNTIME_DST="$HOST_ROOT/runtime"

copy_tree_no_clobber() {
    local src="$1"
    local dst="$2"
    mkdir -p "$dst"
    (
        cd "$src"
        find . -mindepth 1 -print | while IFS= read -r rel; do
            local from="$src/$rel"
            local to="$dst/$rel"
            if [[ -d "$from" ]]; then
                mkdir -p "$to"
            elif [[ -e "$to" ]]; then
                echo "  保留: ${rel#./}"
            else
                mkdir -p "$(dirname "$to")"
                cp "$from" "$to"
                echo "  新增: ${rel#./}"
            fi
        done
    )
}

echo "=== Upgrade oh-my-autoresearch ==="

# 1. 同步新增模板文件到 .claude
echo ""
echo "→ 同步 .claude 模板 ..."
copy_tree_no_clobber "$CLAUDE_SRC" "$CLAUDE_DST"

# 2. 同步 runtime 模板
echo ""
echo "→ 同步 runtime 模板 ..."
copy_tree_no_clobber "$RUNTIME_SRC" "$RUNTIME_DST"

# 3. 不执行数据库迁移
echo ""
echo "→ 跳过数据库迁移 (保持用户数据不变)"

# 4. 不覆盖用户数据
echo "→ 不覆盖用户数据: states/, knowledges/, logs/, observations/"

echo ""
echo "=== Upgrade 完成 ==="
