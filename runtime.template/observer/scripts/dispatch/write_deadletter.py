#!/usr/bin/env python3
"""write_deadletter.py - 写入失败事件到 deadletter.jsonl。"""

import json
from pathlib import Path


def write_deadletter(deadletter_file: Path, event: dict) -> None:
    """将失败事件追加到 deadletter 文件。"""
    deadletter_file.parent.mkdir(parents=True, exist_ok=True)
    with open(deadletter_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runtime/observer/events/deadletter.jsonl")
    event = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    write_deadletter(path, event)
