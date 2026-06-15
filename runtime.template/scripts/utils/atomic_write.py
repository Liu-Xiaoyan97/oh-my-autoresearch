#!/usr/bin/env python3
"""atomic_write.py - 原子写文件工具。

先写到临时文件，再 mv 到目标路径，避免部分写入导致数据损坏。
"""

import json
import os
import tempfile
from pathlib import Path


def atomic_write(file_path: Path, data) -> None:
    """原子地写入 JSON 数据到文件。"""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(file_path.parent), suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            if isinstance(data, str):
                f.write(data)
            else:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
        os.replace(tmp_path, str(file_path))
    except Exception:
        os.unlink(tmp_path)
        raise


if __name__ == "__main__":
    import sys
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("test.json")
    data = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {"test": True}
    atomic_write(target, data)
    print(f"Written to {target}")
