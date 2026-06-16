#!/usr/bin/env python3
"""parse_train_log.py - 仅解析训练日志，不修改状态或数据库。

解析约定（train.py 须按此打印）：
- 训练步行：同时含 step 与 loss，例如
    "step    4/5 | loss 1.0000 | lr 1.0e-03 | 2.1s"   或   "train_step=4 train_loss=1.0000"
- 验证行：含 eval/验证关键字，且**验证指标按 <primary_metric> 的名字显式打印**，例如
    "  Eval at step 5: val_loss=1.2345"   （primary_metric == "val_loss"）
  解析器读取名字等于 <primary_metric> 的指标值填入 val_metric（不再使用 val_<primary_metric>）。
"""

import json
import math
import re
import sys
from pathlib import Path

# 训练行：step / train_step（允许 "step 4/5" 这种无等号写法）
TRAIN_STEP_RE = re.compile(r"(?:^|[\s,])(?:train_)?step\s*[=:]?\s*(\d+)", re.IGNORECASE)
# 训练行：loss / train_loss（允许 "loss 1.0" 这种无等号写法）
TRAIN_LOSS_RE = re.compile(
    r"(?:^|[\s,])(?:train_)?loss\s*[=:]?\s*([-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)", re.IGNORECASE
)
# 验证行步号：val_step=N 或 "Eval at step N"
VAL_STEP_RE = re.compile(r"(?:val_step\s*[=:]\s*(\d+))|(?:eval\s+at\s+step\s+(\d+))", re.IGNORECASE)
# 通用 key=value（仅用于验证行提取命名指标，如 val_loss=1.2345）
METRIC_RE = re.compile(
    r"(?:^|[\s,])([A-Za-z_][A-Za-z0-9_.\-]*)\s*[=:]\s*([-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)",
    re.IGNORECASE,
)


def _float(value: str) -> float | None:
    try:
        parsed = float(value)
    except ValueError:
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _is_eval_line(line: str) -> bool:
    return re.search(r"eval|\bval[_ ]", line, re.IGNORECASE) is not None


def parse_lines(lines: list[str], primary_metric: str | None = None) -> dict:
    progress: dict = {}
    losses: list[float] = []
    pm = (primary_metric or "").strip()

    for line in lines:
        if _is_eval_line(line):
            if m := VAL_STEP_RE.search(line):
                progress["val_step"] = int(m.group(1) or m.group(2))
            for key, raw in METRIC_RE.findall(line):
                if key.lower() in ("step", "val_step", "train_step"):
                    continue
                value = _float(raw)
                if value is None:
                    continue
                progress[key] = value
                if pm and key == pm:
                    progress["val_metric"] = value
        else:
            if m := TRAIN_STEP_RE.search(line):
                progress["train_step"] = int(m.group(1))
            if m := TRAIN_LOSS_RE.search(line):
                loss = _float(m.group(1))
                if loss is not None:
                    progress["train_loss"] = loss
                    losses.append(loss)

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
