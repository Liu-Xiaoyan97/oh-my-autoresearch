#!/usr/bin/env python3
"""load_offset.py - 读取当前消费偏移。"""

from pathlib import Path


def load_offset(offsets_file: Path) -> int:
    """读取 offset 文件，返回当前偏移量。"""
    if not offsets_file.exists():
        return 0

    content = offsets_file.read_text(encoding="utf-8").strip()
    try:
        return int(content)
    except ValueError:
        return 0


if __name__ == "__main__":
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runtime/observer/offsets/events.offset")
    print(load_offset(path))
