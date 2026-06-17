#!/usr/bin/env python3
"""validate_db_schema.py - Phase 0 数据表 schema 校验 / 自愈建表。

- experiments / exploration 不存在则按 objective 推导的 schema 创建。
- 存在则校验列集合是否完全匹配；不匹配且表为空则 drop 重建(自愈)，非空则校验不通过。
- 数据完整性校验：
    * experiments 非空但每行除 exp_name 外全为 0 → 不通过。
    * experiments 记录数必须 == exploration 记录数 或 == exploration 记录数 - 1，否则不通过。

输出 {"valid": bool, "error"/"message": str}，供 validate_runtime.py 汇总。
"""

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "database"))
from schema_spec import (  # noqa: E402
    load_objective, experiments_columns, experiments_ddl,
    exploration_ddl, EXPLORATION_COLUMNS,
)


def _out(valid: bool, msg: str):
    key = "message" if valid else "error"
    print(json.dumps({"valid": valid, key: msg}, ensure_ascii=False))
    sys.exit(0 if valid else 1)


def _table_exists(conn, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _columns(conn, name: str) -> list:
    return [r[1] for r in conn.execute(f'PRAGMA table_info("{name}")')]


def _count(conn, name: str) -> int:
    return conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]


def _ensure_table(conn, name: str, expected_cols: list, ddl: str) -> str:
    """返回 None 表示 ok，否则返回错误信息。"""
    if not _table_exists(conn, name):
        conn.execute(ddl)
        conn.commit()
        return None
    actual = _columns(conn, name)
    if actual == expected_cols:
        return None
    # schema 不匹配：空表则 drop 重建自愈，非空则报错
    if _count(conn, name) == 0:
        conn.execute(f'DROP TABLE "{name}"')
        conn.execute(ddl)
        conn.commit()
        return None
    return (f'{name} 表 schema 不匹配且非空：期望列 {expected_cols}，'
            f'实际列 {actual}。请先 /loop-reset 清表。')


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    try:
        objective = load_objective(runtime_root)
        exp_cols = experiments_columns(objective)
        expl_cols = list(EXPLORATION_COLUMNS)
    except Exception as e:
        _out(False, f"读取 objective 失败: {e}")

    db_path = Path(runtime_root) / "db" / "runtime.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        err = _ensure_table(conn, "experiments", exp_cols, experiments_ddl(objective))
        if err:
            _out(False, err)
        err = _ensure_table(conn, "exploration", expl_cols, exploration_ddl())
        if err:
            _out(False, err)

        exp_count = _count(conn, "experiments")
        expl_count = _count(conn, "exploration")

        # 完整性 1：experiments 非空但每行除 exp_name 外全为 0
        metric_cols = exp_cols[1:]
        if exp_count > 0 and metric_cols:
            cond = " AND ".join(f'COALESCE("{c}",0)=0' for c in metric_cols)
            zero_rows = conn.execute(
                f'SELECT COUNT(*) FROM experiments WHERE {cond}').fetchone()[0]
            if zero_rows > 0:
                _out(False, f"experiments 表存在 {zero_rows} 行指标全为 0（未写入），校验不通过。")

        # 完整性 2：experiments 记录数必须 == exploration 或 == exploration-1
        diff = expl_count - exp_count
        if diff not in (0, 1):
            _out(False, f"记录数不一致：experiments={exp_count} 与 exploration={expl_count} "
                        f"差值必须为 0 或 1。")

        _out(True, f"experiments({exp_count}) / exploration({expl_count}) schema 与数据校验通过。")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
