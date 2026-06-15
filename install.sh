#!/usr/bin/env bash
set -euo pipefail

# install.sh - 安装 research-loop-agent 到宿主 research-runtime 仓库
# 用法: ./install.sh <host-repo-root>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_ROOT="${1:-}"

if [[ -z "$HOST_ROOT" ]]; then
    echo "错误: 请提供宿主仓库根目录路径"
    echo "用法: $0 <host-repo-root>"
    exit 1
fi

if [[ ! -d "$HOST_ROOT/.git" ]] && [[ ! -f "$HOST_ROOT/.git" ]]; then
    echo "错误: $HOST_ROOT 不是一个 git 仓库"
    exit 1
fi

echo "=== research-loop-agent 安装 ==="
echo "子模块目录: $SCRIPT_DIR"
echo "宿主仓库:   $HOST_ROOT"

CLAUDE_TARGET="$HOST_ROOT/.claude"
RUNTIME_TARGET="$HOST_ROOT/runtime"

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
                echo "  跳过 (已存在): ${rel#./}"
            else
                mkdir -p "$(dirname "$to")"
                cp "$from" "$to"
                echo "  安装: ${rel#./}"
            fi
        done
    )
}

# 1. 复制 .claude.template → .claude
echo ""
echo "→ 安装 .claude/template 到 $CLAUDE_TARGET ..."
copy_tree_no_clobber "$SCRIPT_DIR/.claude.template" "$CLAUDE_TARGET"

# 2. 复制 runtime.template → runtime
echo ""
echo "→ 安装 runtime.template 到 $RUNTIME_TARGET ..."
copy_tree_no_clobber "$SCRIPT_DIR/runtime.template" "$RUNTIME_TARGET"

# 3. 复制 pyproject.toml → 宿主根 (no-clobber，不覆盖宿主已有的)
echo ""
echo "→ 安装 pyproject.toml 到 $HOST_ROOT ..."
if [[ -e "$HOST_ROOT/pyproject.toml" ]]; then
    echo "  跳过 (已存在): pyproject.toml"
else
    cp "$SCRIPT_DIR/pyproject.toml" "$HOST_ROOT/pyproject.toml"
    echo "  安装: pyproject.toml"
fi

# 4. 设置脚本执行权限
echo ""
echo "→ 设置脚本执行权限 ..."
find "$SCRIPT_DIR" -name "*.sh" -exec chmod +x {} +
find "$RUNTIME_TARGET" -name "*.sh" -exec chmod +x {} +

# 5. 调用 bootstrap.sh
echo ""
echo "→ 运行 bootstrap.sh ..."
"$SCRIPT_DIR/bootstrap.sh" "$HOST_ROOT"

echo ""
echo "=== 安装完成 ==="
echo "在宿主仓库中运行 /loop 启动研究循环。"
