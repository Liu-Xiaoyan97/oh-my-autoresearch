#!/usr/bin/env python3
"""observation_store.py - observer 自己的 observation 存储(独立于 runtime.sqlite)。

落两份：runtime/observer/observations/observations.sqlite 与同目录 observations.jsonl。
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def _dir(runtime_root: str) -> Path:
    d = Path(runtime_root) / "observer" / "observations"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _db(runtime_root: str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(_dir(runtime_root) / "observations.sqlite"))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exp_name TEXT,
            iteration INTEGER,
            current_step INTEGER,
            observation TEXT,
            insight TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn


def append(runtime_root: str, record: dict) -> int:
    record = dict(record)
    record.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    conn = _db(runtime_root)
    try:
        cur = conn.execute(
            "INSERT INTO observations (exp_name, iteration, current_step, observation, insight, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (record.get("exp_name"), record.get("iteration"), record.get("current_step"),
             record.get("observation"), record.get("insight"), record["created_at"]),
        )
        conn.commit()
        rid = cur.lastrowid
    finally:
        conn.close()
    with (_dir(runtime_root) / "observations.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({**record, "id": rid}, ensure_ascii=False) + "\n")
    return rid
