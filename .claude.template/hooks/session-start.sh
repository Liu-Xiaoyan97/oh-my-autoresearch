#!/usr/bin/env bash
# session-start.sh - Claude Code session 启动时执行
# 职责：1) 模板解析填充  2) observer sidecar 存活守卫 + 自动恢复

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="${SCRIPT_DIR}/../../runtime"

# Step 0: 解析模板占位符（幂等可重复）
RESOLVE_SCRIPT="$RUNTIME_ROOT/scripts/utils/resolve_templates.sh"
if [[ -x "$RESOLVE_SCRIPT" ]]; then
    "$RESOLVE_SCRIPT" "$RUNTIME_ROOT"
fi

# Step 1-5: observer sidecar 存活守卫 + 自动恢复
START_SCRIPT="$RUNTIME_ROOT/observer/scripts/lifecycle/start_observer.sh"
STOP_SCRIPT="$RUNTIME_ROOT/observer/scripts/lifecycle/stop_observer.sh"
STATUS_FILE="$RUNTIME_ROOT/observer/run/observer.status"

echo "[session-start] observer sidecar 存活检查 ..."

# ── 工具函数 ─────────────────────────────────────────────────────

# 检查 observer 是否健康（last_poll 在 60s 以内 + alive=true）
# 返回 0=健康, 1=无状态文件/解析错误, 2=last_poll 过期, 3=alive=false
_check_health() {
    if [[ ! -f "$STATUS_FILE" ]]; then
        return 1
    fi
    python3 -c "
import json, time
try:
    s = json.load(open('$STATUS_FILE'))
    last = s.get('last_poll', '')
    if not last:
        exit(1)
    from datetime import datetime, timezone
    t = datetime.fromisoformat(last)
    age = (datetime.now(timezone.utc) - t).total_seconds()
    if not s.get('alive', False):
        exit(3)
    if age > 60:
        exit(2)
    exit(0)
except Exception:
    exit(4)
" 2>/dev/null
    local rc=$?
    return $rc
}

# 重启 observer（先停后起）
_restart() {
    if [[ -x "$STOP_SCRIPT" ]]; then
        "$STOP_SCRIPT" "$RUNTIME_ROOT" 2>/dev/null || true
    fi
    sleep 1
    if [[ -x "$START_SCRIPT" ]]; then
        "$START_SCRIPT" "$RUNTIME_ROOT" 2>/dev/null || true
    fi
}

# 等待并验证（最多等 N 秒）
_wait_and_verify() {
    local max_wait="${1:-6}"
    local waited=0
    while [[ $waited -lt $max_wait ]]; do
        if _check_health; then
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done
    _check_health  # 最后一次检查
    return $?
}

# ── 主流程 ───────────────────────────────────────────────────────

# Step 1: 检查 observer 健康状态
_check_health
case $? in
    0)
        echo "[session-start] observer 正常运行 (last_poll < 60s)"
        exit 0
        ;;
    1|4)
        echo "[session-start] observer 状态文件异常或不存在，清理重启 ..."
        ;;
    2)
        echo "[session-start] observer last_poll 过期（>60s 无心跳），进程可能挂死，清理重启 ..."
        ;;
    3)
        echo "[session-start] observer 标记为不存活，清理重启 ..."
        ;;
esac

# Step 2: 重启
_restart

# Step 3: 等待并验证
if _wait_and_verify 6; then
    echo "[session-start] observer 启动并正常运行"
    exit 0
fi

# Step 4: 一次重试
echo "[session-start] 首次启动未通过健康检查，重试一次 ..."
_restart
if _wait_and_verify 8; then
    echo "[session-start] 重试后 observer 启动成功"
    exit 0
fi

# Step 5: 仍失败，报 warning 但不阻止启动
echo "[session-start] ⚠ 无法验证 observer 健康状态（last_poll 仍未更新）—— session 继续，observer 将自行恢复"
exit 0
