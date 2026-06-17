#!/usr/bin/env bash
set -euo pipefail

# pre-tool-use.sh - 工具调用前拦截器
#
# 守卫 1: 检测并阻止对 runtime/states/states.json 的直接写入，
#         强制 team-lead 用 emit_event.py state 事件推进状态机。
#             ("echo ... > states.json", "cat ... > states.json", "write ... states.json", etc.)
#
# 守卫 2: 检测并阻止对 runtime/observer/observations/ 下文件的直接操作，
#         这些应由 observer 自主管理。
#
# 守卫 3: 检测并阻止直接调用 observer 内部 lifecycle 脚本
#         （team-lead 只能通过 emit_event.py 控制 observer）。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="${SCRIPT_DIR}/../../runtime"

# 尝试获取当前工具调用的命令内容
# 方式1: 通过环境变量 CLAUDE_TOOL_INPUT（Claude Code > 3.7+）
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"
# 方式2: 通过 stdin（部分版本）
if [[ -z "$TOOL_INPUT" ]] && [[ ! -t 0 ]]; then
    STDIN_DATA="$(cat /dev/stdin 2>/dev/null || true)"
    if [[ -n "$STDIN_DATA" ]]; then
        TOOL_INPUT="$STDIN_DATA"
    fi
fi

# 方式3: 通过命令行参数（部分版本传给 hook 脚本）
if [[ -z "$TOOL_INPUT" ]] && [[ $# -gt 0 ]]; then
    TOOL_INPUT="$*"
fi

BLOCKED=false
BLOCK_REASON=""

# ── 守卫 1: 直接写入 states.json ──────────────────────────────────
STATES_JSON="$(cd "$RUNTIME_ROOT" 2>/dev/null && realpath "states/states.json" 2>/dev/null || echo "$RUNTIME_ROOT/states/states.json")"

# 检测各类写入模式
if echo "$TOOL_INPUT" | grep -qiE '(>|>>|cat |echo |printf|tee ).*states\.json' 2>/dev/null; then
    BLOCKED=true
    BLOCK_REASON="检测到直接写入 states.json 的 Bash 命令。请使用 observer state 事件推进状态机：\n  python3 runtime/observer/scripts/ingest/emit_event.py state '<payload_json>' runtime"
fi

if echo "$TOOL_INPUT" | grep -qiE '(write|edit|overwrite).*states\.json' 2>/dev/null; then
    BLOCKED=true
    BLOCK_REASON="检测到可能直接写 states.json 的操作。请使用 observer state 事件推进状态机。"
fi

# ── 守卫 2: 直接操作 observer/observations/ 产物 ──────────────────
if echo "$TOOL_INPUT" | grep -qiE '(rm |del |truncate|> ).*observer/(observations|run|offsets)' 2>/dev/null; then
    BLOCKED=true
    BLOCK_REASON="检测到直接操作 observer 产物的命令。请使用 control reset 事件由 observer 自清。"
fi

# ── 守卫 3: 直接调用 observer lifecycle 脚本 ──────────────────────
if echo "$TOOL_INPUT" | grep -qiE '(start_observer|stop_observer|restart_observer|reset_observer|healthcheck)\.(sh|py)' 2>/dev/null; then
    BLOCKED=true
    BLOCK_REASON="检测到直接调用 observer lifecycle 脚本。observer 由 session hook 管理，team-lead 不得直接控制。"
fi

# ── 守卫 4: 拦截用 general-purpose / general_purpose subagent 的 Agent 调用 ──────
if echo "$TOOL_INPUT" | grep -qiE '"subagent_type"[[:space:]]*:[[:space:]]*"general.purpose"' 2>/dev/null; then
    BLOCKED=true
    BLOCK_REASON="检测到尝试用 general-purpose/general_purpose 类型创建 Agent。CLAUDE.md 明确禁止使用未注册 agent 类型，只能使用已在 .claude/agents/ 注册的类型。"
fi

# ── 守卫 5: 拦截未在 .claude/agents/ 注册的 subagent_type ──────────────────
REGISTERED_AGENTS="orthogonal-direction-scout|summarizer|coder|flow-arch-reviewer|math-theorist|numerical-debugger"
if echo "$TOOL_INPUT" | grep -qiE '"subagent_type"' 2>/dev/null; then
    EXTRACTED=$(echo "$TOOL_INPUT" | grep -oE '"subagent_type"[[:space:]]*:[[:space:]]*"[^"]*"' 2>/dev/null | grep -oE '"[^"]*"$' | tr -d '"' 2>/dev/null || true)
    if [[ -n "$EXTRACTED" ]] && ! echo "$EXTRACTED" | grep -qiE "^($REGISTERED_AGENTS)$" 2>/dev/null; then
        BLOCKED=true
        BLOCK_REASON="检测到未注册的 subagent_type: '$EXTRACTED'。CLAUDE.md 明确禁止使用未注册 agent 类型，只能使用已在 .claude/agents/ 注册的类型：${REGISTERED_AGENTS//|/、}"
    fi
fi

if [[ "$BLOCKED" == "true" ]]; then
    echo "[pre-tool-use] ⛔ 拦截: $BLOCK_REASON" >&2
    exit 1
fi

exit 0
