#!/usr/bin/env python3
"""query_tables.py - 只读查询并打印 experiments / exploration 两表全部记录。

供 /loop-status 调用。team-lead 读 SQLite 允许（只有写须走 observer event）。
长文本列（exploration 的 JSON）按 --width 截断，避免刷屏。
"""

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema_spec import DB_PATH


def _fetch(conn, table):
    try:
        cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]
        rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
        return cols, rows
    except sqlite3.OperationalError:
        return None, None


def _fmt_cell(v, width):
    s = "" if v is None else str(v)
    s = s.replace("\n", " ")
    return s if len(s) <= width else s[: width - 1] + "…"


def _print_table(name, cols, rows, width):
    print(f"=== {name} ({0 if rows is None else len(rows)} 行) ===")
    if cols is None:
        print("  (表不存在)")
        return
    if not rows:
        print("  列: " + ", ".join(cols))
        print("  (无记录)")
        return
    cells = [[_fmt_cell(v, width) for v in row] for row in rows]
    widths = [max(len(c), *(len(r[i]) for r in cells)) for i, c in enumerate(cols)]
    line = lambda vals: "  " + " | ".join(v.ljust(widths[i]) for i, v in enumerate(vals))
    print(line(cols))
    print("  " + "-+-".join("-" * w for w in widths))
    for r in cells:
        print(line(r))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runtime_root", nargs="?", default="runtime")
    ap.add_argument("--width", type=int, default=40, help="单元格最大宽度")
    args = ap.parse_args()

    db = Path(args.runtime_root) / DB_PATH
    if not db.exists():
        print(f"数据库不存在: {db}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db))
    try:
        for t in ("experiments", "exploration"):
            cols, rows = _fetch(conn, t)
            _print_table(t, cols, rows, args.width)
            print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
