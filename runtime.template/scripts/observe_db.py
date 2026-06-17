#!/usr/bin/env python3
"""实时 observer.db 终端仪表盘 — 每 2 秒自动刷新

用法:
    python3 observe_db.py              # 默认：orthogonal-direction-scout 只显示 name
    python3 observe_db.py --details    # 显示完整 JSON（含 description）
"""
import sqlite3, time, os, sys, json
import argparse
from datetime import datetime
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich import box

_CFG = json.load(open(os.path.join(os.path.dirname(__file__),
                                    "../observer/config.json")))
_RUNTIME = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DB = os.path.join(_RUNTIME, _CFG.get("db_path", "db/runtime.sqlite"))

SHOW_DETAILS = False


def _extract_names(value: str) -> str:
    """从 JSON 数组中提取每个 candidate 的 name，用分号连接。"""
    try:
        candidates = json.loads(value)
        if isinstance(candidates, list):
            names = []
            for c in candidates:
                n = c.get("name", "")
                names.append(n)
            return "; ".join(names)
    except (json.JSONDecodeError, TypeError, AttributeError):
        pass
    return value


def fetch_tables():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # safe: check table existence first
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = {r["name"] for r in cur.fetchall()}

    if "experiments" in existing:
        cur.execute("PRAGMA table_info(experiments)")
        exp_cols = [r["name"] for r in cur.fetchall()]
        cur.execute("SELECT * FROM experiments ORDER BY rowid DESC")
        exp_rows = cur.fetchall()
    else:
        exp_cols, exp_rows = ["(table not yet created)"], []

    if "exploration" in existing:
        cur.execute("PRAGMA table_info(exploration)")
        expl_cols = [r["name"] for r in cur.fetchall()]
        cur.execute("SELECT * FROM exploration ORDER BY rowid DESC")
        expl_rows = cur.fetchall()
    else:
        expl_cols, expl_rows = ["(table not yet created)"], []

    conn.close()
    return exp_cols, exp_rows, expl_cols, expl_rows


def make_table(title, cols, rows, scout_col_idx=None):
    t = Table(title=title, box=box.ROUNDED, header_style="bold cyan", show_lines=True)
    for c in cols:
        t.add_column(c)
    if not rows:
        t.add_row("(empty)", *([""] * (len(cols) - 1)))
        return t
    for r in rows:
        cells = []
        for i, c in enumerate(cols):
            try:
                val = str(r[c])
            except (IndexError, KeyError):
                val = str(r[i]) if i < len(r) else ""

            # orthogonal-direction-scout 列：默认只显示 name 列表
            if not SHOW_DETAILS and scout_col_idx is not None and i == scout_col_idx:
                val = _extract_names(val)

            cells.append(val)
        t.add_row(*cells)
    return t


def build_layout():
    exp_cols, exp_rows, expl_cols, expl_rows = fetch_tables()

    # 找到 orthogonal-direction-scout 在 exploration 中的列索引
    scout_idx = None
    for i, c in enumerate(expl_cols):
        if c == "orthogonal-direction-scout":
            scout_idx = i
            break

    layout = Layout()
    layout.split_column(
        Layout(Panel(make_table("📊 experiments", exp_cols, exp_rows),
                     border_style="green"), ratio=3),
        Layout(Panel(make_table("🔍 exploration", expl_cols, expl_rows, scout_col_idx=scout_idx),
                     border_style="yellow"), ratio=7),
        Layout(Panel(f"⏱ Last refresh: {datetime.now():%H:%M:%S}  |  "
                     f"experiments: {len(exp_rows)} rows  |  "
                     f"exploration: {len(expl_rows)} rows  |  "
                     + ("" if SHOW_DETAILS else "[dim]--details 显示完整 JSON[/]"),
                     border_style="dim"), size=3),
    )
    return layout


def main():
    global SHOW_DETAILS
    ap = argparse.ArgumentParser(description="实时 observer 数据库仪表盘")
    ap.add_argument("--details", action="store_true",
                    help="显示 orthogonal-direction-scout 列的完整 JSON（含 description）")
    args = ap.parse_args()
    SHOW_DETAILS = args.details

    try:
        with Live(build_layout(), refresh_per_second=0.5, screen=False) as live:
            while True:
                live.update(build_layout())
                time.sleep(2)
    except KeyboardInterrupt:
        print("\n👋 已退出", file=sys.stderr)


if __name__ == "__main__":
    main()
