#!/usr/bin/env python3
"""validate_event_chain.py - 校验事件链完整性，可选自动修复。

在 Phase 0 中检测当前状态对应的必需事件是否已在 events.jsonl 中发射。
若缺失且有 --fix 参数，自动 emit 缺失事件（placeholder 标记）。

校验映射（来自 states.json current_step 推导）：
    current_step >= 3 → exploration update_orthogonal_candidates
    current_step >= 4 → exploration update_decision
    current_step >= 5 → exploration update_commit
    current_step >= 7 → experiments insert_experiment
    current_step >= 8 → experiments mark_complete

用法:
    python validate_event_chain.py [runtime_root] [--fix]
"""

import json
import subprocess
import sys
from pathlib import Path

REQUIREMENTS_MAP = [
    # (min_step, event_type, action_predicate, label)
    (3, "exploration", lambda a: a == "update_orthogonal_candidates", "正交候选集"),
    (4, "exploration", lambda a: a == "update_decision", "票选决策"),
    (5, "exploration", lambda a: a == "update_commit", "commit"),
    (7, "experiments", lambda a: a == "insert_experiment", "实验记录"),
    (8, "experiments", lambda a: a == "mark_complete", "实验完成"),
]


def _load_events(runtime_root: str) -> list:
    """读取 events.jsonl 并返回事件列表。"""
    path = Path(runtime_root) / "observer" / "events" / "events.jsonl"
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def _emit_event(runtime_root: str, event_type: str, payload: dict) -> bool:
    """调用 emit_event.py 发射事件。"""
    emit_py = Path(runtime_root) / "observer" / "scripts" / "ingest" / "emit_event.py"
    if not emit_py.exists():
        return False
    payload_str = json.dumps(payload, ensure_ascii=False)
    try:
        result = subprocess.run(
            ["python3", str(emit_py), event_type, payload_str, runtime_root],
            capture_output=True, text=True, timeout=15,
        )
        return result.returncode == 0
    except Exception:
        return False


def validate(runtime_root: str, fix: bool = False) -> dict:
    """校验事件链完整性，返回校验报告。"""
    # 读取 states.json
    states_path = Path(runtime_root) / "states" / "states.json"
    if not states_path.exists():
        return {"valid": False, "error": "states.json 不存在"}

    try:
        state = json.loads(states_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"valid": False, "error": f"states.json 解析错误: {e}"}

    current_step = state.get("current_step", 0)
    exp_name = state.get("exp_name", "")

    if not exp_name:
        return {"valid": True, "checks": [], "message": "无当前实验，跳过校验"}

    events = _load_events(runtime_root)

    # 按 exp_name 过滤 — states_exp_name 是权威 exp_name
    # 注意：events 的 payload 中可能不包含 exp_name（如 clear_all），
    # 但 exploration/experiments 事件通常会写 payload.exp_name
    def matches(event, desired_type, action_pred):
        if event.get("event_type") != desired_type:
            return False
        payload = event.get("payload", {})
        return action_pred(payload.get("action", ""))

    checks = []
    all_pass = True
    auto_fixed = []

    for min_step, ev_type, action_pred, label in REQUIREMENTS_MAP:
        if current_step < min_step:
            continue  # 状态还没到需要这个事件的程度

        found = any(matches(e, ev_type, action_pred) for e in events)
        check = {
            "check": f"step>={min_step} → {ev_type} {label}",
            "found": found,
            "passed": found,
        }

        if not found:
            all_pass = False
            if fix:
                # 自动修复：emit 缺失事件
                payload = _build_fix_payload(ev_type, action_pred, exp_name)
                if payload:
                    ok = _emit_event(runtime_root, ev_type, payload)
                    check["auto_fixed"] = ok
                    if ok:
                        auto_fixed.append(f"{ev_type}/{payload.get('action', '?')}({label})")

        checks.append(check)

    result = {
        "valid": all_pass,
        "exp_name": exp_name,
        "current_step": current_step,
        "checks": checks,
    }
    if auto_fixed:
        result["auto_fixed"] = auto_fixed
    if not all_pass and not fix:
        result["message"] = "事件链不完整，可加 --fix 自动修复"

    return result


def _build_fix_payload(event_type: str, action_pred, exp_name: str) -> dict | None:
    """为缺失事件构建占位 payload。直接按 event_type + action 构造。"""
    # action → (label, payload_builder)
    builders = {
        "exploration:update_orthogonal_candidates": ("正交候选集", lambda en: {
            "action": "update_orthogonal_candidates", "exp_name": en,
            "data": {"orthogonal_direction_scout": [], "_auto_fixed": True, "_note": "自动修复"},
        }),
        "exploration:update_decision": ("票选决策", lambda en: {
            "action": "update_decision", "exp_name": en,
            "data": {"decision": f"_auto_fixed_{en}", "reason": "自动修复: 事件链校验发现缺失"},
        }),
        "exploration:update_commit": ("commit", lambda en: {
            "action": "update_commit", "exp_name": en,
            "data": {"commit_id": f"_auto_fixed_{en}", "changes_summary": "自动修复", "smoke_test_status": "unknown"},
        }),
        "exploration:insert_exploration": ("探索行", lambda en: {
            "action": "insert_exploration", "exp_name": en,
        }),
        "experiments:insert_experiment": ("实验记录", lambda en: {
            "action": "insert_experiment", "exp_name": en,
            "data": {"status": "auto_fixed"},
        }),
        "experiments:mark_complete": ("实验完成", lambda en: {
            "action": "mark_complete", "exp_name": en,
            "data": {"status": "completed", "_auto_fixed": True},
        }),
    }

    # 尝试所有已知 action 匹配 action_pred
    for _, ev_type, pred, label in REQUIREMENTS_MAP:
        if ev_type != event_type:
            continue
        known_actions = {
            "exploration": ["update_orthogonal_candidates", "update_decision", "update_commit", "insert_exploration"],
            "experiments": ["insert_experiment", "mark_complete"],
        }
        for action in known_actions.get(event_type, []):
            if action_pred(action):
                key = f"{event_type}:{action}"
                if key in builders:
                    _, builder = builders[key]
                    return builder(exp_name)
    return None


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "runtime"
    fix = "--fix" in sys.argv

    result = validate(runtime_root, fix=fix)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("valid") else 1)


if __name__ == "__main__":
    main()
