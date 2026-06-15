#!/usr/bin/env python3
"""monitor_training.py - 监控训练日志，输出最近训练进度和最近验证记录。

用法:
    python monitor_training.py <repo_root> <exp_name>
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_train_log import parse_lines


def parse_log(log_path: Path, primary_metric: str | None = None) -> dict:
    """解析训练日志，提取最新的训练进度。"""
    if not log_path.exists():
        return {}

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    return parse_lines(lines, primary_metric)


def main():
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    exp_name = sys.argv[2] if len(sys.argv) > 2 else ""

    if not exp_name:
        print(json.dumps({}))
        sys.exit(0)

    objective_path = Path(repo_root) / "states" / "objective.json"
    primary_metric = None
    if objective_path.exists():
        try:
            objective = json.loads(objective_path.read_text(encoding="utf-8"))
            primary_metric = objective.get("primary_metrics", {}).get("name")
        except json.JSONDecodeError:
            primary_metric = None

    log_path = Path(repo_root) / "logs" / f"train-of-{exp_name}.log"
    progress = parse_log(log_path, primary_metric)
    print(json.dumps(progress, indent=2))


if __name__ == "__main__":
    main()
