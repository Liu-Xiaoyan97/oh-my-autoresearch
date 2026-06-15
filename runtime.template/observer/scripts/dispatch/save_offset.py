#!/usr/bin/env python3
"""save_offset.py - 保存当前消费偏移。"""

from pathlib import Path


def save_offset(offsets_file: Path, offset: int) -> None:
    """保存 offset 到文件。"""
    offsets_file.parent.mkdir(parents=True, exist_ok=True)
    offsets_file.write_text(str(offset), encoding="utf-8")


if __name__ == "__main__":
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("runtime/observer/offsets/events.offset")
    offset = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    save_offset(path, offset)
