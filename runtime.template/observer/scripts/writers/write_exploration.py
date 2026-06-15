#!/usr/bin/env python3
"""write_exploration.py - 写入 exploration 表。"""

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


def _get_db_path(runtime_root: str) -> str:
    return str(Path(runtime_root) / "db" / "runtime.sqlite")


def _ensure_table(conn: sqlite3.Connection) -> None:
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


def write(runtime_root: str, payload: dict) -> bool:
    """根据 action 写入 exploration 表。"""
    action = payload.get("action", "")
    exp_name = payload.get("exp_name", "")
    data = payload.get("data", {})

    db_path = _get_db_path(runtime_root)
    conn = sqlite3.connect(db_path)
    _ensure_table(conn)

    now = datetime.now(timezone.utc).isoformat()

    try:
        if not exp_name:
            print("[write_exploration] exp_name 不能为空", file=sys.stderr)
            return False

        conn.execute(
            "INSERT OR IGNORE INTO exploration (exp_name, created_at, updated_at) VALUES (?, ?, ?)",
            (exp_name, now, now),
        )

        if action == "insert_exploration":
            conn.execute("UPDATE exploration SET updated_at = ? WHERE exp_name = ?", (now, exp_name))
            conn.commit()

        elif action == "update_orthogonal_candidates":
            value = data.get("orthogonal_direction_scout", data)
            conn.execute(
                "UPDATE exploration SET orthogonal_direction_scout = ?, updated_at = ? WHERE exp_name = ?",
                (json.dumps(value, ensure_ascii=False), now, exp_name),
            )
            conn.commit()

        elif action == "update_decision":
            value = data.get("decision", data)
            conn.execute(
                "UPDATE exploration SET decision = ?, updated_at = ? WHERE exp_name = ?",
                (json.dumps(value, ensure_ascii=False), now, exp_name),
            )
            conn.commit()

        elif action == "update_commit":
            conn.execute(
                "UPDATE exploration SET commit_id = ?, updated_at = ? WHERE exp_name = ?",
                (data.get("commit_id", ""), now, exp_name),
            )
            conn.commit()

        else:
            print(f"[write_exploration] 未知 action: {action}", file=sys.stderr)
            return False

        return True

    except Exception as e:
        print(f"[write_exploration] 错误: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    write(runtime_root, payload)
