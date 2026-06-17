#!/usr/bin/env python3
"""init_db.py - 初始化 SQLite，按 objective 推导的新 schema 建 experiments / exploration。"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema_spec import DB_PATH, load_objective, experiments_ddl, exploration_ddl  # noqa: E402


def init_db(runtime_root: str) -> str:
    db_path = Path(runtime_root) / DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    objective = load_objective(runtime_root)
    conn = sqlite3.connect(str(db_path))
    try:
        existing = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if "experiments" not in existing:
            conn.execute(experiments_ddl(objective))
        if "exploration" not in existing:
            conn.execute(exploration_ddl())
        conn.commit()
    finally:
        conn.close()
    return str(db_path)


if __name__ == "__main__":
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    print(f"Database initialized at {init_db(runtime_root)}")
