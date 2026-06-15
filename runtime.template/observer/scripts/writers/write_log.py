#!/usr/bin/env python3
"""write_log.py - 写入 observations log。

格式: [YYYY-MM-DD HH:MM:SS]|[LEVEL]-{Message}
"""

import json
from datetime import datetime, timezone
from pathlib import Path


def _resolve_exp_name(runtime_root: str, payload: dict) -> str:
    """优先用 payload 的真实 exp_name；缺失或为 default 时回退到当前 states.json。"""
    exp_name = str(payload.get("exp_name") or "").strip()
    if exp_name and exp_name != "default":
        return exp_name

    states_path = Path(runtime_root) / "states" / "states.json"
    try:
        state = json.loads(states_path.read_text(encoding="utf-8"))
        current = str(state.get("exp_name") or "").strip()
        if current:
            return current
    except Exception:
        pass

    return "default"


def write(runtime_root: str, payload: dict) -> bool:
    """写入 log 事件到 observations/<exp_name>.log。"""
    exp_name = _resolve_exp_name(runtime_root, payload)
    timestamp_value = payload.get("timestamp", datetime.now(timezone.utc).isoformat())
    level = payload.get("level", "INFO")
    source = payload.get("source", "team-lead")
    message = payload.get("message", "")

    noisy_sources = {"session-start", "session-stop", "tool-pre-use", "tool-post-use"}
    if source in noisy_sources:
        return True

    if exp_name == "default" and source != "team-lead":
        return True

    try:
        timestamp_str = datetime.fromisoformat(timestamp_value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    log_dir = Path(runtime_root) / "observations"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{exp_name}.log"
    line = f"[{timestamp_str}]|[{level}]-{message}\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line)

    return True


if __name__ == "__main__":
    import sys
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    write(runtime_root, payload)
