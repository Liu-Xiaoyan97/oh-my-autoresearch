#!/usr/bin/env python3
"""write_log.py - 写入 observations log。

格式: [YYYY-MM-DD HH:MM:SS]|[LEVEL]-{Message}
"""

from datetime import datetime, timezone
from pathlib import Path


def write(runtime_root: str, payload: dict) -> bool:
    """写入 log 事件到 observations/<exp_name>.log。"""
    exp_name = payload.get("exp_name", "default")
    timestamp_value = payload.get("timestamp", datetime.now(timezone.utc).isoformat())
    level = payload.get("level", "INFO")
    message = payload.get("message", "")

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
    import json
    import sys
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    write(runtime_root, payload)
