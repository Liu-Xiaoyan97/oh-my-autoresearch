#!/usr/bin/env python3
"""update_experiment_metric.py - 更新 experiments 表中某个 step 的 metric。"""

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


def ensure_step_column(conn: sqlite3.Connection, val_step: int) -> str:
    col = f"step_{val_step}"
    columns = {row[1] for row in conn.execute("PRAGMA table_info(experiments)")}
    if col not in columns:
        conn.execute(f"ALTER TABLE experiments ADD COLUMN {col} REAL")
    return col


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    exp_name = sys.argv[2] if len(sys.argv) > 2 else ""
    train_step = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    train_loss = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    val_step = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    val_metric = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0

    if not exp_name:
        print("用法: update_experiment_metric.py <exp_name> [train_step] [train_loss] [val_step] [val_metric]", file=sys.stderr)
        sys.exit(1)

    db_path = str(Path(runtime_root) / "db" / "runtime.sqlite")
    conn = sqlite3.connect(db_path)
    now = datetime.now(timezone.utc).isoformat()

    step_col = ensure_step_column(conn, val_step)
    conn.execute(
        f"UPDATE experiments SET train_step=?, train_loss=?, val_step=?, val_metric=?, {step_col}=?, updated_at=? WHERE exp_name=?",
        (train_step, train_loss, val_step, val_metric, val_metric, now, exp_name),
    )
    conn.commit()
    conn.close()
    print(f"Updated experiment: {exp_name}")


if __name__ == "__main__":
    main()
