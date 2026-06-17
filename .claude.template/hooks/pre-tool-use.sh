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

# ── 守卫 6: 拦截 Agent 调用未指定 subagent_type（默认降级为 general-purpose）──
# 模型常通过省略 subagent_type 绕过 Guard 4&5，因为工具定义中 subagent_type 非必填，
# 省略后 Claude Code 自动默认使用 general-purpose，这是被禁止的。
if echo "$TOOL_INPUT" | grep -qiE '"description"' 2>/dev/null && \
   echo "$TOOL_INPUT" | grep -qiE '"prompt"' 2>/dev/null && \
   ! echo "$TOOL_INPUT" | grep -qiE '"subagent_type"' 2>/dev/null && \
   ! echo "$TOOL_INPUT" | grep -qiE '"subagentType"' 2>/dev/null; then
    BLOCKED=true
    BLOCK_REASON="Agent 调用必须指定 subagent_type（已注册类型：orthogonal-direction-scout、summarizer、coder、flow-arch-reviewer、math-theorist、numerical-debugger）。省略 subagent_type 会默认降级到 general-purpose，这是被禁止的。"
fi

# ── 守卫 7: 拦截 Write/Edit 写入非 project/ 路径（剥夺 team-lead 直接写权）──
# CLAUDE.md: "team-lead 没有任何直接写权：不使用 Write / Edit 落盘"
# 仅 coder 可写 project/ 下的被优化项目代码；其它所有路径（runtime/、.claude/、
# 根目录 JSON、agent-system/ 等）禁止直接写入。
# 检测 Write 工具：有 file_path + content
# 检测 Edit 工具：有 file_path + new_string + old_string
# 排除 Read 工具：有 file_path 但无 content/new_string
TOOL_HAS_FILEPATH=$(echo "$TOOL_INPUT" | grep -cE '"file_path"[[:space:]]*:' 2>/dev/null || true)
TOOL_HAS_CONTENT=$(echo "$TOOL_INPUT" | grep -cE '"content"[[:space:]]*:' 2>/dev/null || true)
TOOL_HAS_NEWSTR=$(echo "$TOOL_INPUT" | grep -cE '"new_string"[[:space:]]*:' 2>/dev/null || true)

IS_WRITE=false
IS_EDIT=false
if [[ "$TOOL_HAS_FILEPATH" -gt 0 ]] && [[ "$TOOL_HAS_CONTENT" -gt 0 ]]; then
    IS_WRITE=true
fi
if [[ "$TOOL_HAS_FILEPATH" -gt 0 ]] && [[ "$TOOL_HAS_NEWSTR" -gt 0 ]]; then
    IS_EDIT=true
fi

if [[ "$IS_WRITE" == "true" ]] || [[ "$IS_EDIT" == "true" ]]; then
    WRITE_PATH=$(echo "$TOOL_INPUT" | grep -oE '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | grep -oE '"[^"]*"$' | tr -d '"' 2>/dev/null || true)
    if [[ -n "$WRITE_PATH" ]]; then
        # 允许的路径前缀：/project/（被优化项目目录）
        ALLOWED=false
        case "$WRITE_PATH" in
            */project/*) ALLOWED=true ;;
        esac
        if [[ "$ALLOWED" != "true" ]]; then
            BLOCKED=true
            BLOCK_REASON="检测到禁止的直接写入操作（路径: $WRITE_PATH）。CLAUDE.md 规定 team-lead 没有任何直接写权，只能通过 observer event 持久化。仅有 coder 可向 project/ 下写入被优化项目代码。"
        fi
    fi
fi

# ── 守卫 8: 禁止在仓库目录内通过 Bash 创建文件（允许 /tmp、>& 描述符重定向）──
# 检测模式：> 后跟一个相对路径（不以 / 开头，不是 & 文件描述符）。
# 不匹配：2>&1、>/dev/null、>/tmp/xxx 等系统路径。
# 注意：coder 对 project/ 下代码的 Write/Edit 由守卫 7 判定，不在此拦截。
DEST_PATH=$(echo "$TOOL_INPUT" | grep -oE '(>|>>)[[:space:]]*[a-zA-Z0-9_./-]+' 2>/dev/null | head -1 | sed 's/^[>[:space:]]*//')
# 只当目标路径是相对路径、非 fd 描述符、且包含字母（看起来像文件名）时拦截
if [[ -n "$DEST_PATH" ]] && [[ "$DEST_PATH" != /* ]] && [[ "$DEST_PATH" != &* ]] && [[ "$DEST_PATH" =~ [a-zA-Z] ]]; then
    BLOCKED=true
    BLOCK_REASON="检测到在仓库目录内创建文件：$DEST_PATH。临时文件统一使用 /tmp 目录。"
fi

if [[ "$BLOCKED" == "true" ]]; then
    echo "[pre-tool-use] ⛔ 拦截: $BLOCK_REASON" >&2
    exit 1
fi

exit 0
