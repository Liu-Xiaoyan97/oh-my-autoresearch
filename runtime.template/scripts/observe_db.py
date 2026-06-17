#!/usr/bin/env python3
"""实时 observer.db 终端仪表盘 — 每 2 秒自动刷新"""
import sqlite3, time, os, sys, json
from datetime import datetime
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich import box

_CFG = json.load(open(os.path.join(os.path.dirname(__file__),
                                    "../observer/config.json")))
_RUNTIME = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DB = os.path.join(_RUNTIME, _CFG.get("db_path", "db/observer.db"))

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

def make_table(title, cols, rows):
    t = Table(title=title, box=box.ROUNDED, header_style="bold cyan")
    for c in cols:
        t.add_column(c)
    if not rows:
        t.add_row("(empty)", *([""] * (len(cols) - 1)))
        return t
    for r in rows:
        cells = []
        for i, c in enumerate(cols):
            try:
                cells.append(str(r[c]))
            except (IndexError, KeyError):
                cells.append(str(r[i]) if i < len(r) else "")
        t.add_row(*cells)
    return t

def build_layout():
    exp_cols, exp_rows, expl_cols, expl_rows = fetch_tables()

    layout = Layout()
    layout.split_column(
        Layout(Panel(make_table("📊 experiments", exp_cols, exp_rows),
                     border_style="green")),
        Layout(Panel(make_table("🔍 exploration", expl_cols, expl_rows),
                     border_style="yellow")),
        Layout(Panel(f"⏱ Last refresh: {datetime.now():%H:%M:%S}  |  "
                     f"experiments: {len(exp_rows)} rows  |  "
                     f"exploration: {len(expl_rows)} rows",
                     border_style="dim")),
    )
    return layout

def main():
    try:
        with Live(build_layout(), refresh_per_second=0.5, screen=False) as live:
            while True:
                live.update(build_layout())
                time.sleep(2)
    except KeyboardInterrupt:
        print("\n👋 已退出", file=sys.stderr)

if __name__ == "__main__":
    main()
