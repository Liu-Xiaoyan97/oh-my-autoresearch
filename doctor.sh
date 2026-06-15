#!/usr/bin/env bash
set -euo pipefail

# doctor.sh - 环境诊断脚本
# 用法: ./doctor.sh <host-repo-root>

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST_ROOT="${1:-.}"

RUNTIME="$HOST_ROOT/runtime"
CLAUDE="$HOST_ROOT/.claude"
EXIT_CODE=0

echo "=== Doctor 环境诊断 ==="
echo ""

# 1. 检查 Claude Code 配置
echo "→ 检查 .claude 配置 ..."
for f in CLAUDE.md settings.json; do
    if [[ -f "$CLAUDE/$f" ]]; then
        echo "  [OK] $f"
    else
        echo "  [FAIL] $f 不存在"
        EXIT_CODE=1
    fi
done
for f in commands/loop.md agents/orthogonal-direction-scout.md hooks/session-start.sh; do
    if [[ -f "$CLAUDE/$f" ]]; then
        echo "  [OK] $f"
    else
        echo "  [FAIL] $f 不存在"
        EXIT_CODE=1
    fi
done

# 2. 检查 runtime 目录
echo ""
echo "→ 检查 runtime 目录 ..."
for dir in states knowledges schemas scripts observer; do
    if [[ -d "$RUNTIME/$dir" ]]; then
        echo "  [OK] $dir/"
    else
        echo "  [FAIL] $dir/ 不存在"
        EXIT_CODE=1
    fi
done

# 3. 检查 observer 是否可启动
echo ""
echo "→ 检查 observer 可启动性 ..."
if [[ -x "$RUNTIME/observer/scripts/lifecycle/start_observer.sh" ]]; then
    echo "  [OK] start_observer.sh 存在且可执行"
else
    echo "  [FAIL] start_observer.sh 不存在或不可执行"
    EXIT_CODE=1
fi

if [[ -f "$RUNTIME/observer/config.json" ]]; then
    echo "  [OK] observer config.json 存在"
else
    echo "  [FAIL] observer config.json 不存在"
    EXIT_CODE=1
fi

# 4. 检查 SQLite 是否可写
echo ""
echo "→ 检查 SQLite 可写性 ..."
DB_FILE="$RUNTIME/db/runtime.sqlite"
if [[ -f "$DB_FILE" ]]; then
    if sqlite3 "$DB_FILE" "SELECT 1;" >/dev/null 2>&1; then
        echo "  [OK] $DB_FILE 可读"
    else
        echo "  [FAIL] $DB_FILE 不可读"
        EXIT_CODE=1
    fi
else
    echo "  [WARN] $DB_FILE 不存在 (可能需要先运行 bootstrap.sh)"
fi

# 5. 检查 JSON schema 校验工具
echo ""
echo "→ 检查 schema 校验工具 ..."
if python3 -c "import jsonschema" 2>/dev/null; then
    echo "  [OK] jsonschema Python 包可用"
else
    echo "  [FAIL] jsonschema Python 包不可用"
    EXIT_CODE=1
fi

# 6. 检查 git 环境
echo ""
echo "→ 检查 git 环境 ..."
if command -v git >/dev/null 2>&1; then
    echo "  [OK] git $(git --version 2>/dev/null | head -1)"
else
    echo "  [FAIL] git 未安装"
    EXIT_CODE=1
fi

# 7. 检查 ssh 环境
echo ""
echo "→ 检查 ssh 环境 ..."
if command -v ssh >/dev/null 2>&1; then
    echo "  [OK] ssh 可用"
else
    echo "  [WARN] ssh 未安装 (远程训练需要)"
fi

# 8. 检查 python 环境
echo ""
echo "→ 检查 python 环境 ..."
if command -v python3 >/dev/null 2>&1; then
    echo "  [OK] python3 $(python3 --version 2>&1)"
else
    echo "  [FAIL] python3 未安装"
    EXIT_CODE=1
fi

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "=== Doctor 诊断完成: 全部通过 ==="
else
    echo "=== Doctor 诊断完成: 存在失败项，请修复 ==="
fi

exit $EXIT_CODE
