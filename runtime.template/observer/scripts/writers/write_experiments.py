#!/usr/bin/env python3
"""write_experiments.py - 写入 experiments 表。

可通过 runtime/scripts/database/* helper 调用，但外部入口必须是 observer event。
"""

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


def _get_db_path(runtime_root: str) -> str:
    return str(Path(runtime_root) / "db" / "runtime.sqlite")


def _ensure_table(conn: sqlite3.Connection) -> None:
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
    conn.commit()


def _ensure_step_column(conn: sqlite3.Connection, step: int) -> str:
    col = f"step_{step}"
    columns = {row[1] for row in conn.execute("PRAGMA table_info(experiments)")}
    if col not in columns:
        conn.execute(f"ALTER TABLE experiments ADD COLUMN {col} REAL")
    return col


def write(runtime_root: str, payload: dict) -> bool:
    """根据 action 写入 experiments 表。"""
    action = payload.get("action", "")
    exp_name = payload.get("exp_name", "")
    data = payload.get("data", {})

    db_path = _get_db_path(runtime_root)
    conn = sqlite3.connect(db_path)
    _ensure_table(conn)

    now = datetime.now(timezone.utc).isoformat()

    try:
        if action == "insert_experiment":
            conn.execute(
                "INSERT OR IGNORE INTO experiments (exp_name, created_at, updated_at) VALUES (?, ?, ?)",
                (exp_name, now, now),
            )
            conn.commit()

        elif action == "update_metric":
            fields = []
            values = []
            for key in ["train_step", "train_loss", "val_step", "val_metric", "status"]:
                if key in data:
                    fields.append(f"{key} = ?")
                    values.append(data[key])
            if "val_step" in data and "val_metric" in data:
                step_col = _ensure_step_column(conn, int(data["val_step"]))
                fields.append(f"{step_col} = ?")
                values.append(data["val_metric"])
            if fields:
                fields.append("updated_at = ?")
                values.append(now)
                values.append(exp_name)
                conn.execute(
                    f"UPDATE experiments SET {', '.join(fields)} WHERE exp_name = ?",
                    values,
                )
                conn.commit()

        elif action == "mark_complete":
            conn.execute(
                "UPDATE experiments SET status = ?, updated_at = ? WHERE exp_name = ?",
                ("completed", now, exp_name),
            )
            conn.commit()

        return True

    except Exception as e:
        print(f"[write_experiments] 错误: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    write(runtime_root, payload)
