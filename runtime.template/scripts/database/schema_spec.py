#!/usr/bin/env python3
"""schema_spec.py - experiments / exploration 两表的唯一 schema 真相源。

依据 objective.json 动态推导 experiments 的列：
    exp_name (PK) + <{primary_metrics.name}_step_{(i+1)*eval_n_steps}>
        for i in range(num_training_steps // eval_n_steps)
exploration 固定 4 列：
    exp_name (PK) + orthogonal-direction-scout + decision + commit (均 TEXT)
"""

import json
from pathlib import Path

EXPLORATION_COLUMNS = ["exp_name", "orthogonal-direction-scout", "decision", "commit"]


def load_objective(runtime_root: str) -> dict:
    base = Path(runtime_root) / "states"
    for name in ("objective.json", "objective.example.json"):
        p = base / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"objective.json 不存在于 {base}")


def states_exp_name(runtime_root: str) -> str:
    """从 states.json 读取当前 exp_name（权威来源）。读不到返回空串。"""
    p = Path(runtime_root) / "states" / "states.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("exp_name", "") or ""
        except Exception:
            return ""
    return ""


def metric_step_columns(objective: dict) -> list:
    metric = objective["primary_metrics"]["name"]
    num = int(objective["num_training_steps"])
    ev = int(objective["eval_n_steps"])
    if ev <= 0:
        raise ValueError("eval_n_steps 必须 > 0")
    n = num // ev
    return [f"{metric}_step_{(i + 1) * ev}" for i in range(n)]


def experiments_columns(objective: dict) -> list:
    return ["exp_name"] + metric_step_columns(objective)


def _q(ident: str) -> str:
    return '"' + ident.replace('"', '""') + '"'


def experiments_ddl(objective: dict) -> str:
    cols = [f'{_q("exp_name")} TEXT PRIMARY KEY']
    for c in metric_step_columns(objective):
        cols.append(f'{_q(c)} REAL DEFAULT 0')
    return "CREATE TABLE experiments (\n  " + ",\n  ".join(cols) + "\n)"


def exploration_ddl() -> str:
    cols = [f'{_q("exp_name")} TEXT PRIMARY KEY']
    for c in EXPLORATION_COLUMNS[1:]:
        cols.append(f'{_q(c)} TEXT')
    return "CREATE TABLE exploration (\n  " + ",\n  ".join(cols) + "\n)"
