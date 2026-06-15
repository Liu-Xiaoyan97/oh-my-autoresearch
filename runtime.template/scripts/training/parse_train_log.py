#!/usr/bin/env python3
"""parse_train_log.py - 仅解析训练日志，不修改状态或数据库。"""

import json
import math
import re
import sys
from pathlib import Path


STEP_RE = re.compile(r"(?:^|[\s,])(?:train_)?step\s*[=:]\s*(\d+)", re.IGNORECASE)
VAL_STEP_RE = re.compile(r"(?:^|[\s,])val_step\s*[=:]\s*(\d+)", re.IGNORECASE)
LOSS_RE = re.compile(r"(?:^|[\s,])(?:train_)?loss\s*[=:]\s*([-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)", re.IGNORECASE)
VAL_RE = re.compile(r"(?:^|[\s,])(val_[A-Za-z0-9_.-]+)\s*[=:]\s*([-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)", re.IGNORECASE)


def _float(value: str) -> float | None:
    try:
        parsed = float(value)
    except ValueError:
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def parse_lines(lines: list[str], primary_metric: str | None = None) -> dict:
    progress: dict = {}
    losses: list[float] = []

    for line in lines:
        if match := STEP_RE.search(line):
            progress["train_step"] = int(match.group(1))
        if match := VAL_STEP_RE.search(line):
            progress["val_step"] = int(match.group(1))
        if match := LOSS_RE.search(line):
            loss = _float(match.group(1))
            if loss is not None:
                progress["train_loss"] = loss
                losses.append(loss)
        for key, raw in VAL_RE.findall(line):
            if key == "val_step":
                continue
            value = _float(raw)
            if value is not None:
                progress[key] = value
                if primary_metric and key == f"val_{primary_metric}":
                    progress["val_metric"] = value

    if losses:
        latest = losses[-1]
        progress["loss_exploded"] = latest > 1e6 or (
            len(losses) >= 3 and losses[-1] > losses[-2] > losses[-3] and losses[-1] > losses[-3] * 10
        )
    else:
        progress["loss_exploded"] = False

    return progress


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: parse_train_log.py <log_file> [primary_metric]", file=sys.stderr)
        sys.exit(1)

    log_path = Path(sys.argv[1])
    primary_metric = sys.argv[2] if len(sys.argv) > 2 else None
    if not log_path.exists():
        print(json.dumps({}))
        return

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    print(json.dumps(parse_lines(lines, primary_metric), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
