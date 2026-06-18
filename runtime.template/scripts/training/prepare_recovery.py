#!/usr/bin/env python3
"""Phase 9 前置屏障：将最终实验数据追加到 observer 事件队列。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from monitor_training import _parse_eval_history, parse_log  # noqa: E402


def _load_objective(runtime_root: Path) -> dict:
    return json.loads(
        (runtime_root / "states" / "objective.json").read_text(encoding="utf-8")
    )


def _emit(runtime_root: Path, event_type: str, payload: dict) -> dict:
    script = runtime_root / "observer" / "scripts" / "ingest" / "emit_event.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            event_type,
            json.dumps(payload, ensure_ascii=False),
            str(runtime_root),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"{event_type} emit 失败")
    try:
        return json.loads(result.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError(f"{event_type} emit 返回无法解析: {result.stdout!r}") from exc


def _final_data(runtime_root: Path, exp_name: str) -> dict:
    objective = _load_objective(runtime_root)
    metric_name = objective["primary_metrics"]["name"]
    log_path = runtime_root / "logs" / f"train-of-{exp_name}.log"
    progress = parse_log(log_path, metric_name)
    checkpoints = []
    if log_path.exists():
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        checkpoints = _parse_eval_history(lines, metric_name)
    return {
        "metric_name": metric_name,
        "progress": progress,
        "latest_checkpoint": checkpoints[-1] if checkpoints else None,
        "all_checkpoints": checkpoints,
    }


def _queued(runtime_root: Path, exp_name: str, final_data: dict) -> bool:
    events_path = runtime_root / "observer" / "events" / "events.jsonl"
    try:
        lines = events_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    latest = final_data["latest_checkpoint"]
    metric_queued = latest is None
    recovery_mark_queued = False
    for line in lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("event_type") != "experiments":
            continue
        payload = event.get("payload", {})
        if payload.get("exp_name") != exp_name:
            continue
        data = payload.get("data", {})
        if (
            latest
            and payload.get("action") == "update_metric"
            and data.get("val_step") == latest["val_step"]
            and data.get("val_metric") == latest["val_metric"]
            and data.get("recovery_ready") is True
        ):
            metric_queued = True
        if (
            payload.get("action") == "mark_complete"
            and data.get("recovery_ready") is True
        ):
            recovery_mark_queued = True
    return metric_queued and recovery_mark_queued


def prepare(runtime_root: Path, exp_name: str) -> dict:
    final_data = _final_data(runtime_root, exp_name)
    progress = final_data["progress"]
    latest = final_data["latest_checkpoint"]
    emitted = []

    # 发射所有未写入的 eval 检查点（不仅 latest——训练可能短于 cron 间隔，
    # 导致 monitor_training.py 从未触发，中间步骤全部缺失）
    all_checkpoints = final_data.get("all_checkpoints", [])
    if not all_checkpoints and latest:
        all_checkpoints = [latest]
    emitted_steps: set[int] = set()
    for cp in all_checkpoints:
        step = cp["val_step"]
        if step in emitted_steps:
            continue
        emitted_steps.add(step)
        emitted.append(
            _emit(
                runtime_root,
                "experiments",
                {
                    "action": "update_metric",
                    "exp_name": exp_name,
                    "data": {
                        "train_step": progress.get("train_step", step),
                        "train_loss": progress.get("train_loss", 0.0),
                        "val_step": step,
                        "val_metric": cp["val_metric"],
                        "recovery_ready": True,
                    },
                },
            )
        )
    emitted.append(
        _emit(
            runtime_root,
            "experiments",
            {
                "action": "mark_complete",
                "exp_name": exp_name,
                "data": {**progress, "recovery_ready": True},
            },
        )
    )
    return {
        "emitted": True,
        "exp_name": exp_name,
        "final_metrics": progress,
        "latest_checkpoint": latest,
        "emitted_events": emitted,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runtime_root")
    parser.add_argument("exp_name")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    runtime_root = Path(args.runtime_root).resolve()
    final_data = _final_data(runtime_root, args.exp_name)
    if args.check_only:
        queued = _queued(runtime_root, args.exp_name, final_data)
        print(
            json.dumps(
                {
                    "emitted": queued,
                    "exp_name": args.exp_name,
                    "final_metrics": final_data["progress"],
                    "latest_checkpoint": final_data["latest_checkpoint"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if queued else 2

    try:
        print(
            json.dumps(
                prepare(runtime_root, args.exp_name),
                ensure_ascii=False,
            )
        )
        return 0
    except (OSError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"ready": False, "error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
