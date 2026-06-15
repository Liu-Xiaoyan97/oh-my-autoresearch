#!/usr/bin/env python3
"""path_resolve.py - 路径解析工具。

用法:
    python path_resolve.py <relative_path> [--base <base_dir>]
"""

import sys
from pathlib import Path


def resolve(base_dir: str, relative_path: str) -> Path:
    """解析相对路径，基于 base_dir。"""
    base = Path(base_dir).resolve()
    resolved = (base / relative_path).resolve()
    return resolved


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: path_resolve.py <relative_path> [--base <base_dir>]", file=sys.stderr)
        sys.exit(1)

    rel_path = sys.argv[1]
    base = "."
    if "--base" in sys.argv:
        idx = sys.argv.index("--base")
        if idx + 1 < len(sys.argv):
            base = sys.argv[idx + 1]

    result = resolve(base, rel_path)
    print(result)
