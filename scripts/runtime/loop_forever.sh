#!/usr/bin/env bash
# Unattended AutoResearch driver.
#
# Runs ONE full iteration (Phase A..F) per FRESH `claude` session, so every
# iteration starts with a clean context window — no manual /compact needed and
# no unbounded context growth. This relies on the Stop hook (.claude/hooks/
# stop.py) allowing a session to stop at the Phase A boundary (Phase F returns
# the workflow to A). Because runtime/ is the source of truth, each fresh
# session resumes correctly from runtime/state.
#
# Usage:
#   ./scripts/loop_forever.sh
# Env:
#   CLAUDE_BIN                 claude CLI binary (default: claude)
#   CLAUDE_ARGS                extra args for claude (default: --permission-mode bypassPermissions)
#   AUTORESEARCH_MAX_ITERS     stop after N iterations (default: 0 = until DONE/BLOCKED)
#
# Stops when the workflow reaches DONE or BLOCKED, after MAX_ITERS, or if a
# session makes no progress twice in a row (stall guard).
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then PYTHON_BIN="$(command -v python3 || true)"; fi
cd "$ROOT_DIR"

CLAUDE_BIN="${CLAUDE_BIN:-claude}"
CLAUDE_ARGS="${CLAUDE_ARGS:---dangerously-skip-permissions}"
MAX_ITERS="${AUTORESEARCH_MAX_ITERS:-0}"

# The Stop hook stops each spawned session at the Phase A boundary by default,
# so every loop iteration below runs in a fresh `claude` process (clean context).
# Make sure we do NOT accidentally inherit continuous mode.
unset AUTORESEARCH_CONTINUOUS

if ! command -v "$CLAUDE_BIN" >/dev/null 2>&1; then
  echo "[driver] claude CLI not found (set CLAUDE_BIN). Aborting." >&2
  exit 127
fi

read_state() {
  "$PYTHON_BIN" - "$1" <<'PY'
import json, sys
try:
    d = json.load(open("runtime/state/state.json"))
except Exception as e:
    print(""); raise SystemExit(0)
print(d.get(sys.argv[1]) if d.get(sys.argv[1]) is not None else "")
PY
}

PROMPT='Advance the AutoResearch loop. Read runtime/state first, then run ./scripts/run_loop.sh from the repository root repeatedly until the workflow either returns to the Phase A boundary (one full iteration A..F has completed) or reaches BLOCKED/DONE. Do not stop mid-iteration. Follow CLAUDE.md and the phase scripts; never hand-edit runtime state or fabricate AgentTeam output.'

count=0
stall=0
while :; do
  phase="$(read_state phase)"
  iter="$(read_state iteration)"
  case "$phase" in
    DONE) echo "[driver] workflow DONE after $count session(s)."; exit 0 ;;
    BLOCKED) echo "[driver] workflow BLOCKED — human intervention needed: $(read_state block_reason)" >&2; exit 2 ;;
    "") echo "[driver] cannot read runtime/state/state.json. Aborting." >&2; exit 1 ;;
  esac

  sig_before="${phase}/${iter}"
  echo "[driver] === starting iteration session (phase=$phase iter=$iter) $(date -u +%FT%TZ) ==="

  "$CLAUDE_BIN" -p "$PROMPT" $CLAUDE_ARGS
  rc=$?
  [ "$rc" -ne 0 ] && echo "[driver] claude exited rc=$rc"

  phase="$(read_state phase)"
  iter="$(read_state iteration)"
  sig_after="${phase}/${iter}"

  if [ "$sig_after" = "$sig_before" ]; then
    stall=$((stall + 1))
    echo "[driver] no progress this session (phase=$phase iter=$iter), stall=$stall"
    if [ "$stall" -ge 2 ]; then
      echo "[driver] stalled twice with no progress; aborting for inspection." >&2
      exit 3
    fi
  else
    stall=0
  fi

  count=$((count + 1))
  if [ "$MAX_ITERS" -gt 0 ] && [ "$count" -ge "$MAX_ITERS" ]; then
    echo "[driver] reached AUTORESEARCH_MAX_ITERS=$MAX_ITERS; stopping."
    exit 0
  fi
done
