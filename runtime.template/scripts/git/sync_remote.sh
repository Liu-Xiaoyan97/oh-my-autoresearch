#!/usr/bin/env bash
set -euo pipefail

# sync_remote.sh - 根据 objective hosts 配置同步远端代码
# 用法: sync_remote.sh <repo_root> <hosts_file>

REPO_ROOT="${1:-.}"
HOSTS_FILE="${2:-}"

if [[ -z "$HOSTS_FILE" ]]; then
    echo "用法: sync_remote.sh <repo_root> <hosts_file>"
    exit 1
fi

echo "→ 同步代码到远端 hosts..."
echo "  (实际实现需要根据 objective 配置和 hosts 文件执行 rsync/SCP)"

# TODO: 根据 hosts 链执行远端同步

echo "→ 同步完成"
