#!/usr/bin/env python3
"""save_json.py - 保存 JSON 工具。

用法:
    python save_json.py <json_file> '<json_content>'
"""

import json
import sys
from pathlib import Path

from atomic_write import atomic_write


def save_json(file_path: str, data: object) -> None:
    """使用原子写保存 JSON 数据。"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write(path, data)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: save_json.py <json_file> '<json_content>'", file=sys.stderr)
        sys.exit(1)
    data = json.loads(sys.argv[2])
    save_json(sys.argv[1], data)
    print(f"Saved to {sys.argv[1]}")
