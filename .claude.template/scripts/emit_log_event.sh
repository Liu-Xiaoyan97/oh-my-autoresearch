#!/usr/bin/env bash
set -euo pipefail

# emit_log_event.sh - 轻量 wrapper，向 observer 发送 log event
# 用法: emit_log_event.sh <level> <message> [source]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ROOT="${SCRIPT_DIR}/../../runtime"

LEVEL="${1:-INFO}"
MESSAGE="${2:-}"
SOURCE="${3:-team-lead}"

if [[ -z "$MESSAGE" ]]; then
    echo "用法: $0 <level> <message>"
    exit 1
fi

PAYLOAD="$(python3 - "$LEVEL" "$MESSAGE" "$SOURCE" "$RUNTIME_ROOT" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

level, message, source, runtime_root = sys.argv[1:5]
states_path = Path(runtime_root) / "states" / "states.json"
exp_name = "default"
if states_path.exists():
    try:
        exp_name = json.loads(states_path.read_text(encoding="utf-8")).get("exp_name", exp_name)
    except json.JSONDecodeError:
        pass

print(json.dumps({
    "exp_name": exp_name,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "level": level,
    "source": source,
    "message": message,
}, ensure_ascii=False))
PY
)"

python3 "$RUNTIME_ROOT/observer/scripts/ingest/emit_event.py" log "$PAYLOAD" "$RUNTIME_ROOT"
