#!/usr/bin/env python3
"""write_experiments.py - 写入 experiments 表（宽表 schema）。

schema 由 objective 推导：exp_name(PK) + <{metric}_step_{(i+1)*eval}> 各列(REAL 默认 0)。
- insert_experiment: 建/占位当前实验行。
- update_metric: data 含 val_step + val_metric 时，写入列 <{metric}_step_{val_step}>。
- mark_complete: 宽表无 status 列，仅确保行存在（完成状态由 states.json 跟踪）。
- clear_all: 清空全表（供 /loop-reset）。
"""

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "database"))
from schema_spec import DB_PATH, load_objective, experiments_ddl, states_exp_name  # noqa: E402


def _get_db_path(runtime_root: str) -> str:
    return str(Path(runtime_root) / DB_PATH)


def _ensure_table(conn: sqlite3.Connection, runtime_root: str):
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='experiments'"
    ).fetchone()
    if not exists:
        conn.execute(experiments_ddl(load_objective(runtime_root)))
        conn.commit()


def _metric_name(runtime_root: str) -> str:
    return load_objective(runtime_root)["primary_metrics"]["name"]


def write(runtime_root: str, payload: dict) -> bool:
    action = payload.get("action", "")
    # exp_name 权威来源是 states.json，不依赖主程序在 payload 里给
    exp_name = states_exp_name(runtime_root) or payload.get("exp_name", "")
    data = payload.get("data", {})

    conn = sqlite3.connect(_get_db_path(runtime_root))
    try:
        _ensure_table(conn, runtime_root)

        if action == "clear_all":
            conn.execute("DELETE FROM experiments")
            conn.commit()
            return True

        if not exp_name:
            print("[write_experiments] exp_name 不能为空", file=sys.stderr)
            return False

        conn.execute(
            "INSERT OR IGNORE INTO experiments (exp_name) VALUES (?)", (exp_name,)
        )

        if action == "insert_experiment":
            conn.commit()

        elif action == "update_metric":
            if "val_step" in data and "val_metric" in data:
                col = f'{_metric_name(runtime_root)}_step_{int(data["val_step"])}'
                cols = {r[1] for r in conn.execute('PRAGMA table_info(experiments)')}
                if col not in cols:
                    conn.execute(f'ALTER TABLE experiments ADD COLUMN "{col}" REAL DEFAULT 0')
                conn.execute(
                    f'UPDATE experiments SET "{col}" = ? WHERE exp_name = ?',
                    (data["val_metric"], exp_name),
                )
                conn.commit()

        elif action == "mark_complete":
            conn.commit()  # 宽表无 status 列；确保行已存在即可

        else:
            print(f"[write_experiments] 未知 action: {action}", file=sys.stderr)
            return False

        return True

    except Exception as e:
        print(f"[write_experiments] 错误: {e}", file=sys.stderr)
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    import json
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    write(runtime_root, payload)
