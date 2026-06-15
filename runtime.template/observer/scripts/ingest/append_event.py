#!/usr/bin/env python3
"""append_event.py - 追加事件到 events.jsonl，使用文件锁保证并发安全。"""

import json
import fcntl
from pathlib import Path


def append(events_file: Path, event: dict) -> None:
    """追加一个事件到 JSONL 文件，使用文件锁保证并发安全。"""
    events_file.parent.mkdir(parents=True, exist_ok=True)
    with open(events_file, "a", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            f.flush()
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


if __name__ == "__main__":
    import sys

    events_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runtime/observer/events/events.jsonl")
    event_data = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    append(events_path, event_data)
