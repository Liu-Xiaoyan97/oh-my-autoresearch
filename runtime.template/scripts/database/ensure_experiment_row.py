#!/usr/bin/env python3
"""ensure_experiment_row.py - 保证 experiments 表中存在某个 exp_name 行。"""

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    exp_name = sys.argv[2] if len(sys.argv) > 2 else ""

    if not exp_name:
        print("用法: ensure_experiment_row.py <exp_name>", file=sys.stderr)
        sys.exit(1)

    db_path = str(Path(runtime_root) / "db" / "runtime.sqlite")
    conn = sqlite3.connect(db_path)
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT OR IGNORE INTO experiments (exp_name, created_at, updated_at) VALUES (?, ?, ?)",
        (exp_name, now, now),
    )
    conn.commit()
    conn.close()
    print(f"Ensured experiment row: {exp_name}")


if __name__ == "__main__":
    main()
