#!/usr/bin/env python3
"""jsonl.py - JSONL 读写工具。"""

import json
from pathlib import Path


def read_jsonl(file_path: str) -> list:
    """读取 JSONL 文件，返回所有行的列表。"""
    path = Path(file_path)
    if not path.exists():
        return []
    results = []
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        line = line.strip()
        if line:
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return results


def append_jsonl(file_path: str, record: dict) -> None:
    """追加一条记录到 JSONL 文件。"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    import sys
    action = sys.argv[1] if len(sys.argv) > 1 else "read"
    filepath = sys.argv[2] if len(sys.argv) > 2 else "data.jsonl"

    if action == "read":
        records = read_jsonl(filepath)
        for r in records:
            print(json.dumps(r, ensure_ascii=False))
    elif action == "append":
        if len(sys.argv) < 3:
            print("用法: jsonl append <file> '<record_json>'", file=sys.stderr)
            sys.exit(1)
        record = json.loads(sys.argv[3])
        append_jsonl(filepath, record)
        print(f"Appended to {filepath}")
