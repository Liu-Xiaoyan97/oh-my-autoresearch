#!/usr/bin/env python3
"""init_db.py - 初始化 SQLite。

只创建两个表:
    experiments
    exploration
"""

import sqlite3
import sys
from pathlib import Path


def init_db(db_path: str) -> None:
    """初始化数据库，创建 experiments 和 exploration 表。"""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))

    conn.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            exp_name TEXT PRIMARY KEY,
            train_step INTEGER DEFAULT 0,
            train_loss REAL DEFAULT 0.0,
            val_step INTEGER DEFAULT 0,
            val_metric REAL DEFAULT 0.0,
            status TEXT DEFAULT 'running',
            pid INTEGER,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS exploration (
            exp_name TEXT PRIMARY KEY,
            orthogonal_direction_scout TEXT,
            decision TEXT,
            commit_id TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    db_path = str(Path(runtime_root) / "db" / "runtime.sqlite")
    init_db(db_path)
    print(f"Database initialized at {db_path}")
