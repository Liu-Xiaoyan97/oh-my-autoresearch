#!/usr/bin/env python3
"""consume_events.py - 根据 offset 从 events.jsonl 中读取未消费事件。"""

import json
from pathlib import Path


def consume_next_events(events_file: Path, offset: int, count: int = 10) -> list:
    """读取从 offset 开始的 count 个未消费事件。"""
    if not events_file.exists():
        return []

    lines = events_file.read_text(encoding="utf-8").strip().split("\n")
    remaining = lines[offset:offset + count]

    events = []
    for line in remaining:
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return events


if __name__ == "__main__":
    import sys

    events_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runtime/observer/events/events.jsonl")
    offset = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    events = consume_next_events(events_path, offset, count)
    for e in events:
        print(json.dumps(e, ensure_ascii=False))
