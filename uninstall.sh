#!/usr/bin/env bash
set -euo pipefail

# uninstall.sh - 卸载 research-loop-agent 注入的文件
# 用法: ./uninstall.sh <host-repo-root>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_ROOT="${1:-}"

if [[ -z "$HOST_ROOT" ]]; then
    echo "错误: 请提供宿主仓库根目录路径"
    echo "用法: $0 <host-repo-root>"
    exit 1
fi

RUNTIME_TARGET="$HOST_ROOT/runtime"
CLAUDE_TARGET="$HOST_ROOT/.claude"

echo "=== research-loop-agent 卸载 ==="

# 1. 移除 .claude 中本 submodule 注入的文件
if [[ -d "$CLAUDE_TARGET" ]]; then
    echo ""
    echo "→ 移除 .claude 中的 submodule 文件 ..."
    for item in commands agents schemas scripts hooks; do
        if [[ -d "$CLAUDE_TARGET/$item" ]]; then
            rm -rf "$CLAUDE_TARGET/$item"
            echo "  移除: $item/"
        fi
    done
fi

# 2. 可选择移除 runtime/observer
echo ""
echo "→ 移除 runtime/observer ..."
if [[ -d "$RUNTIME_TARGET/observer" ]]; then
    rm -rf "$RUNTIME_TARGET/observer"
    echo "  已移除: observer/"
else
    echo "  跳过: observer 不存在"
fi

# 3. 默认不删除用户数据
echo ""
echo "→ 保留用户数据 (不删除):"
echo "  runtime/states/"
echo "  runtime/knowledges/"
echo "  runtime/db/"
echo "  runtime/logs/"
echo "  runtime/observations/"

echo ""
echo "=== 卸载完成 ==="
