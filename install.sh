#!/usr/bin/env bash
set -euo pipefail

# install.sh - 安装 research-loop-agent 到宿主 research-runtime 仓库
# 用法: ./install.sh <host-repo-root>
#
# 只安装 manifest.json 中列出的文件，且强制覆盖目标。

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

MANIFEST="$SCRIPT_DIR/manifest.json"
if [[ ! -f "$MANIFEST" ]]; then
    echo "错误: 未找到 $MANIFEST"
    exit 1
fi

echo "=== research-loop-agent 安装 ==="
echo "子模块目录: $SCRIPT_DIR"
echo "宿主仓库:   $HOST_ROOT"

# ---------- 助手：安装 manifest 中列出的文件（强制覆盖）----------
install_files_from_manifest() {
    local field="$1"        # manifest JSON 中的字段名，如 "files"
    local section="$2"      # manifest JSON 中的 section，如 "claude_template" / "runtime_template"
    local src_root="$3"     # 源根目录
    local dst_root="$4"     # 目标根目录

    # 用 python3 解析 manifest，避免复杂 bash JSON 解析
    python3 -c "
import json, sys
try:
    m = json.load(open('$MANIFEST'))
    files = m['$section'].get('$field', [])
    for f in files:
        print(f)
except Exception as e:
    sys.stderr.write('解析 manifest 失败: ' + str(e) + '\n')
    sys.exit(1)
" | while IFS= read -r rel; do
        local from="$src_root/$rel"
        local to="$dst_root/$rel"
        if [[ ! -f "$from" ]]; then
            echo "  警告: 源文件不存在，跳过: ${rel}"
            continue
        fi
        mkdir -p "$(dirname "$to")"
        cp "$from" "$to"
        echo "  安装: ${rel}"
    done
}

# 1. 安装 .claude.template → .claude（manifest 列表 + 强制覆盖）
CLAUDE_SRC="$SCRIPT_DIR/.claude.template"
CLAUDE_DST="$HOST_ROOT/.claude"
echo ""
echo "→ 安装 .claude.template 文件到 $CLAUDE_DST ..."
install_files_from_manifest "files" "claude_template" "$CLAUDE_SRC" "$CLAUDE_DST"

# 2. 安装 runtime.template → runtime（manifest 列表 + 强制覆盖）
RUNTIME_SRC="$SCRIPT_DIR/runtime.template"
RUNTIME_DST="$HOST_ROOT/runtime"
echo ""
echo "→ 安装 runtime.template 文件到 $RUNTIME_DST ..."
install_files_from_manifest "files" "runtime_template" "$RUNTIME_SRC" "$RUNTIME_DST"

# 3. 安装 hooks（manifest 中的 hooks 文件也会被上面的 claude_template.files 覆盖，这里单独处理钩子注册）
echo ""
echo "→ 设置 hook 执行权限 ..."
find "$CLAUDE_DST/hooks" -name "*.sh" -exec chmod +x {} + 2>/dev/null || true

# 4. 复制 pyproject.toml → 宿主根（保持 no-clobber，不覆盖宿主已有的）
echo ""
echo "→ 安装 pyproject.toml 到 $HOST_ROOT ..."
if [[ -e "$HOST_ROOT/pyproject.toml" ]]; then
    echo "  跳过 (已存在): pyproject.toml"
else
    cp "$SCRIPT_DIR/pyproject.toml" "$HOST_ROOT/pyproject.toml"
    echo "  安装: pyproject.toml"
fi

# 5. 设置脚本执行权限
echo ""
echo "→ 设置脚本执行权限 ..."
find "$RUNTIME_DST" -name "*.sh" -exec chmod +x {} +
find "$RUNTIME_DST" -name "*.py" -exec chmod +x {} +

# 6. 调用 bootstrap.sh
echo ""
echo "→ 运行 bootstrap.sh ..."
"$SCRIPT_DIR/bootstrap.sh" "$HOST_ROOT"

echo ""
echo "=== 安装完成 ==="
echo "在宿主仓库中运行 /loop 启动研究循环。"
