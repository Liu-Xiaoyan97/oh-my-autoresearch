#!/usr/bin/env python3
"""monitor_training.py - 监控训练日志，自动向 observer 发射指标事件。

流程：
1. 解析训练日志，提取最新进度和所有 eval 检查点。
2. 用 tracker 文件（runtime/logs/.emitted_eval_steps.json）追踪已发射的步号，
   只对未发射的 eval 检查点自动 emit `experiments update_metric` 事件。
3. 输出 training-progress JSON 给调用方（供模型判断训练是否结束）。

用法:
    python monitor_training.py <repo_root> <exp_name>
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_train_log import parse_lines


def _tracker_path(repo_root: str) -> Path:
    return Path(repo_root) / "logs" / ".emitted_eval_steps.json"


def _load_tracker(repo_root: str) -> dict:
    """读取已发射步号追踪文件。返回 {exp_name: max_emitted_step}。"""
    p = _tracker_path(repo_root)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def _save_tracker(repo_root: str, tracker: dict):
    p = _tracker_path(repo_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(tracker, ensure_ascii=False), encoding="utf-8")


def _emit_event(repo_root: str, event_type: str, payload: dict):
    """调用 emit_event.py 发射事件。"""
    import subprocess
    script = str(Path(repo_root) / "observer" / "scripts" / "ingest" / "emit_event.py")
    payload_str = json.dumps(payload, ensure_ascii=False)
    result = subprocess.run(
        [sys.executable, script, event_type, payload_str, repo_root],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"[monitor_training] emit 失败: {result.stderr.strip()}", file=sys.stderr)
    return result.returncode == 0


def _parse_eval_history(lines: list[str], primary_metric: str | None) -> list[dict]:
    """从日志行中提取所有 eval 检查点。返回按步号排序的列表。"""
    import re
    from parse_train_log import _build_eval_re, _float as _pfloat

    eval_re = _build_eval_re(primary_metric)
    if not eval_re:
        return []

    checkpoints: list[dict] = []
    for line in lines:
        m = eval_re.search(line)
        if not m:
            continue
        step = int(m.group(1))
        value = _pfloat(m.group(2))
        if value is None:
            continue
        checkpoints.append({"val_step": step, "val_metric": value})

    # 按步号排序去重
    seen = set()
    deduped = []
    for cp in sorted(checkpoints, key=lambda x: x["val_step"]):
        if cp["val_step"] not in seen:
            seen.add(cp["val_step"])
            deduped.append(cp)
    return deduped


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

    # ── 自动发射未写入的 eval 指标事件 ──────────────────────────────────
    if log_path.exists():
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        all_checkpoints = _parse_eval_history(lines, primary_metric)
        tracker = _load_tracker(repo_root)
        last_emitted = tracker.get(exp_name, 0)

        new_checkpoints = [cp for cp in all_checkpoints if cp["val_step"] > last_emitted]
        for cp in new_checkpoints:
            payload = {
                "action": "update_metric",
                "exp_name": exp_name,
                "data": {
                    "train_step": progress.get("train_step", cp["val_step"]),
                    "train_loss": progress.get("train_loss", 0.0),
                    "val_step": cp["val_step"],
                    "val_metric": cp["val_metric"],
                },
            }
            ok = _emit_event(repo_root, "experiments", payload)
            if ok:
                print(f"[monitor_training] 自动发射 step_{cp['val_step']} metric={cp['val_metric']:.4f}")
            else:
                print(f"[monitor_training] 发射 step_{cp['val_step']} 失败", file=sys.stderr)

        if new_checkpoints:
            max_step = max(cp["val_step"] for cp in new_checkpoints)
            tracker[exp_name] = max(last_emitted, max_step)
            _save_tracker(repo_root, tracker)

    print(json.dumps(progress, indent=2))


if __name__ == "__main__":
    main()
