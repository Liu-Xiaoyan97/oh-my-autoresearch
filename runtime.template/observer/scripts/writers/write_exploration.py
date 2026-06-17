#!/usr/bin/env python3
"""write_exploration.py - 写入 exploration 表（4 列：exp_name + 三 TEXT 列）。

列：exp_name(PK), "orthogonal-direction-scout", "decision", "commit" 均 TEXT。
- update_orthogonal_candidates → 写 orthogonal-direction-scout
- update_decision               → 写 decision
- update_commit                 → 写 commit
- insert_exploration            → 占位行
- clear_all                     → 清空全表（供 /loop-reset）
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "database"))
from schema_spec import DB_PATH, exploration_ddl, states_exp_name  # noqa: E402


def _get_db_path(runtime_root: str) -> str:
    return str(Path(runtime_root) / DB_PATH)


def _ensure_table(conn: sqlite3.Connection):
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='exploration'"
    ).fetchone()
    if not exists:
        conn.execute(exploration_ddl())
        conn.commit()


def _resolve_decision_name(conn, exp_name, raw_value):
    """若 decision 是 'candidate_N' 形式，解析为 orthogonal-direction-scout 中对应的 name。"""
    if not isinstance(raw_value, str):
        return raw_value
    m = re.match(r'^candidate_(\d+)$', raw_value)
    if not m:
        return raw_value  # 已经是可读名称，保持原样

    row = conn.execute(
        'SELECT "orthogonal-direction-scout" FROM exploration WHERE exp_name = ?',
        (exp_name,),
    ).fetchone()
    if not row or not row[0]:
        return raw_value

    try:
        candidates = json.loads(row[0])
        idx = int(m.group(1))  # candidate_4 → index 4（0-based）
        if 0 <= idx < len(candidates):
            name = candidates[idx].get("name")
            if name:
                return name
    except (json.JSONDecodeError, IndexError, ValueError):
        pass
    return raw_value


def write(runtime_root: str, payload: dict) -> bool:
    action = payload.get("action", "")
    # exp_name 权威来源是 states.json，不依赖主程序在 payload 里给
    exp_name = states_exp_name(runtime_root) or payload.get("exp_name", "")
    data = payload.get("data", {})

    conn = sqlite3.connect(_get_db_path(runtime_root))
    try:
        _ensure_table(conn)

        if action == "clear_all":
            conn.execute("DELETE FROM exploration")
            conn.commit()
            return True

        if not exp_name:
            print("[write_exploration] exp_name 不能为空", file=sys.stderr)
            return False

        conn.execute(
            "INSERT OR IGNORE INTO exploration (exp_name) VALUES (?)", (exp_name,)
        )

        if action == "insert_exploration":
            conn.commit()

        elif action == "update_orthogonal_candidates":
            value = data.get("orthogonal_direction_scout", data)
            conn.execute(
                'UPDATE exploration SET "orthogonal-direction-scout" = ? WHERE exp_name = ?',
                (json.dumps(value, ensure_ascii=False), exp_name),
            )
            conn.commit()

        elif action == "update_decision":
            value = data.get("decision", data)
            value = _resolve_decision_name(conn, exp_name, value)
            conn.execute(
                'UPDATE exploration SET "decision" = ? WHERE exp_name = ?',
                (json.dumps(value, ensure_ascii=False), exp_name),
            )
            conn.commit()

        elif action == "update_commit":
            value = data.get("commit_id", data.get("commit", ""))
            conn.execute(
                'UPDATE exploration SET "commit" = ? WHERE exp_name = ?',
                (value, exp_name),
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
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    write(runtime_root, payload)
