#!/usr/bin/env python3
"""load_json.py - 读取 JSON 工具。

用法:
    python load_json.py <json_file>
"""

import json
import sys
from pathlib import Path


def load_json(file_path: str) -> object:
    """读取 JSON 文件并返回解析后的对象。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: load_json.py <json_file>", file=sys.stderr)
        sys.exit(1)
    data = load_json(sys.argv[1])
    print(json.dumps(data, indent=2, ensure_ascii=False))
