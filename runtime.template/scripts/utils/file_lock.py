#!/usr/bin/env python3
"""file_lock.py - 文件锁工具。

基于 fcntl.flock 实现简单的文件锁。
"""

import fcntl
import os
import sys
from pathlib import Path


class FileLock:
    """文件锁上下文管理器。"""

    def __init__(self, lock_file: Path) -> None:
        self.lock_file = lock_file
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self._fd = None

    def __enter__(self):
        self._fd = open(self.lock_file, "w", encoding="utf-8")
        fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._fd:
            fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            self._fd.close()
        return False


def acquire(lock_file: Path) -> int:
    """获取文件锁，返回文件描述符。调用者需自行 release。"""
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_file, "w", encoding="utf-8")
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return handle


def release(fd) -> None:
    """释放文件锁。"""
    fcntl.flock(fd, fcntl.LOCK_UN)
    fd.close()


if __name__ == "__main__":
    import os
    lock_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("test.lock")
    fd = acquire(lock_path)
    print(f"Lock acquired: fd={fd}")
    release(fd)
    print("Lock released")
