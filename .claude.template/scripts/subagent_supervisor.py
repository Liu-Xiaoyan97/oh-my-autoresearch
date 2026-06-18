#!/usr/bin/env python3
"""Reviewer subagent 去重、心跳租约与有限重试监督器。"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


REVIEWER_ROLES = {
    "flow-arch-reviewer",
    "math-theorist",
    "numerical-debugger",
}
RECOVERY_PHASE_PATTERN = re.compile(r"(?:\[phase=9\]|phase\s*[=:]\s*9)", re.IGNORECASE)

FIRST_LAYER_ROLES = {
    "orthogonal-direction-scout",
    "summarizer",
    "coder",
}


def _resolve_heartbeat_interval() -> int:
    """从 runtime/states/objective.json 读取 subagent_heartbeat_interval。

    脚本在 .claude/scripts/subagent_supervisor.py，
    runtime 在项目根下的 runtime/。
    """
    script = Path(__file__).resolve()
    objective = script.parents[2] / "runtime" / "states" / "objective.json"
    try:
        obj = json.loads(objective.read_text(encoding="utf-8"))
        val = obj.get("subagent_heartbeat_interval", 300)
        return int(val) if val else 300
    except Exception:
        return 300


DEFAULT_HEARTBEAT_TIMEOUT = _resolve_heartbeat_interval()
DEFAULT_POLL_INTERVAL = 15
DEFAULT_MAX_ATTEMPTS = 2


def _now() -> float:
    return time.time()


def _iso(timestamp: float | None = None) -> str:
    return datetime.fromtimestamp(timestamp or _now(), timezone.utc).isoformat()


def _state_root() -> Path:
    configured = os.environ.get("AUTORESEARCH_SUPERVISOR_DIR")
    if configured:
        return Path(configured)
    return Path(tempfile.gettempdir()) / "oh-my-autoresearch-subagents"


def _safe_key(value: str, fallback: str) -> str:
    if value:
        tail = Path(value).stem
        if re.fullmatch(r"[A-Za-z0-9._-]+", tail):
            return tail
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]
    return fallback


def _session_dir(event: dict[str, Any]) -> Path:
    session_id = str(event.get("session_id") or "unknown-session")
    parent_key = _safe_key(
        str(event.get("transcript_path") or ""),
        str(event.get("agent_id") or "root"),
    )
    return _state_root() / _safe_key(session_id, "unknown-session") / parent_key


def _record_path(directory: Path, role: str) -> Path:
    return directory / f"{role}.json"


@contextmanager
def _locked(directory: Path) -> Iterator[None]:
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / ".lock"
    with lock_path.open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _load(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".tmp.{os.getpid()}")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _clean_records_for_parent(parent_agent_id: str) -> None:
    """删除指定父 agent 下所有 reviewer 子记录。

    通过比对 reviewer 记录的 parent_transcript 重建父目录名，
    与父 agent 的 agent_id 配对后找到目标目录删除。
    """
    root = _state_root()
    if not root.exists():
        return
    import shutil

    to_delete: set[Path] = set()
    for path, data in _all_records():
        if data.get("role") in REVIEWER_ROLES:
            parent_transcript = data.get("parent_transcript", "")
            expected_key = _safe_key(parent_transcript, parent_agent_id)
            if expected_key == path.parent.name:
                to_delete.add(path.parent)
    for dir_path in to_delete:
        if dir_path.exists():
            shutil.rmtree(dir_path)


def _all_records() -> Iterator[tuple[Path, dict[str, Any]]]:
    root = _state_root()
    if not root.exists():
        return
    for path in root.glob("*/*/*.json"):
        data = _load(path)
        if data:
            yield path, data


def _find_record(
    *,
    agent_id: str | None = None,
    tool_use_id: str | None = None,
    session_id: str | None = None,
    role: str | None = None,
) -> tuple[Path, dict[str, Any]] | None:
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path, data in _all_records():
        if agent_id and data.get("agent_id") != agent_id:
            continue
        if tool_use_id and data.get("tool_use_id") != tool_use_id:
            continue
        if session_id and data.get("session_id") != session_id:
            continue
        if role and data.get("role") != role:
            continue
        matches.append((path, data))
    if not matches:
        return None
    return max(matches, key=lambda item: float(item[1].get("updated_at_epoch", 0)))


def _extract_agent_id(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("agentId", "agent_id", "taskId", "task_id"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate:
                return candidate
        for child in value.values():
            found = _extract_agent_id(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _extract_agent_id(child)
            if found:
                return found
    elif isinstance(value, str):
        match = re.search(r"(?:agentId|taskId):\s*([A-Za-z0-9_-]+)", value)
        if match:
            return match.group(1)
    return None


def _extract_output_file(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("outputFile", "output_file"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate:
                return candidate
        for child in value.values():
            found = _extract_output_file(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _extract_output_file(child)
            if found:
                return found
    elif isinstance(value, str):
        match = re.search(r"output_file:\s*(\S+)", value)
        if match:
            return match.group(1)
    return None


def _activity_epoch(data: dict[str, Any]) -> float:
    activity = float(data.get("last_heartbeat_epoch", data.get("updated_at_epoch", 0)))
    output_file = data.get("output_file")
    if isinstance(output_file, str) and output_file:
        try:
            activity = max(activity, Path(output_file).stat().st_mtime)
        except OSError:
            pass
    return activity


def _refresh_status(data: dict[str, Any], timeout: int) -> dict[str, Any]:
    refreshed = dict(data)
    activity = _activity_epoch(refreshed)
    age = max(0.0, _now() - activity)
    refreshed["last_activity_epoch"] = activity
    refreshed["last_activity_at"] = _iso(activity)
    refreshed["heartbeat_age_seconds"] = round(age, 3)
    if refreshed.get("status") in {"claimed", "running"} and age > timeout:
        refreshed["status"] = "stale"
        refreshed["stale_at"] = _iso()
    refreshed["retry_allowed"] = (
        refreshed.get("status") in {"failed", "stale", "completed"}
        and int(refreshed.get("attempt", 1)) < int(refreshed.get("max_attempts", DEFAULT_MAX_ATTEMPTS))
    )
    return refreshed


def _deny(reason: str) -> int:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )
    return 0


def _recovery_data_ready(tool_input: dict[str, Any]) -> tuple[bool, str]:
    prompt = str(tool_input.get("prompt") or "")
    if not RECOVERY_PHASE_PATTERN.search(prompt):
        return True, ""
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    runtime_root = project_dir / "runtime"
    try:
        state = json.loads(
            (runtime_root / "states" / "states.json").read_text(encoding="utf-8")
        )
        exp_name = str(state.get("exp_name") or "")
    except (OSError, json.JSONDecodeError):
        return False, "无法读取 runtime/states/states.json"
    if not exp_name:
        return False, "states.json 缺少 exp_name"
    events_path = runtime_root / "observer" / "events" / "events.jsonl"
    try:
        events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    except (OSError, json.JSONDecodeError):
        return False, "无法读取 observer 事件队列"
    queued = any(
        event.get("event_type") == "experiments"
        and event.get("payload", {}).get("action") == "mark_complete"
        and event.get("payload", {}).get("exp_name") == exp_name
        and event.get("payload", {}).get("data", {}).get("recovery_ready") is True
        for event in events
    )
    return (True, "") if queued else (False, f"{exp_name} 的恢复实验数据尚未 emit")


def _handle_pre_tool(event: dict[str, Any]) -> int:
    if event.get("tool_name") not in {"Agent", "Task"}:
        return 0
    tool_input = event.get("tool_input") or {}
    role = tool_input.get("subagent_type") or tool_input.get("subagentType")
    if role == "summarizer":
        ready, detail = _recovery_data_ready(tool_input)
        if not ready:
            return _deny(
                "Phase 9 summarizer 创建前必须先运行 "
                "`python3 runtime/scripts/training/prepare_recovery.py runtime <exp_name>` "
                f"将实验数据追加到 observer 队列。当前检查失败: {detail}"
            )
    if role not in REVIEWER_ROLES:
        return 0
    if tool_input.get("run_in_background") is not True:
        return _deny(
            f"{role} 必须使用 run_in_background=true；前台调用会阻塞父 agent，无法执行心跳检测。"
        )

    directory = _session_dir(event)
    path = _record_path(directory, role)
    with _locked(directory):
        existing = _load(path)
        if existing and existing.get("status") != "retryable":
            return _deny(
                f"同一父 agent 已创建过 {role}（attempt={existing.get('attempt', 1)}, "
                f"status={existing.get('status', 'unknown')}）。禁止通过补数量或等待再次创建；"
                "仅当 supervisor 判定失败/心跳超时并执行 retry 后，才允许重试一次。"
            )

        attempt = int(existing.get("attempt", 0)) + 1 if existing else 1
        max_attempts = int(existing.get("max_attempts", DEFAULT_MAX_ATTEMPTS)) if existing else DEFAULT_MAX_ATTEMPTS
        if attempt > max_attempts:
            return _deny(f"{role} 已达到最大尝试次数 {max_attempts}，禁止继续创建。")

        timestamp = _now()
        record = {
            "session_id": str(event.get("session_id") or ""),
            "parent_transcript": str(event.get("transcript_path") or ""),
            "parent_key": directory.name,
            "role": role,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "tool_use_id": str(event.get("tool_use_id") or ""),
            "status": "claimed",
            "created_at": _iso(timestamp),
            "updated_at": _iso(timestamp),
            "updated_at_epoch": timestamp,
            "last_heartbeat_at": _iso(timestamp),
            "last_heartbeat_epoch": timestamp,
        }
        _save(path, record)
    return 0


def _handle_post_tool(event: dict[str, Any], failed: bool = False) -> int:
    if event.get("tool_name") not in {"Agent", "Task"}:
        return 0
    tool_input = event.get("tool_input") or {}
    role = tool_input.get("subagent_type") or tool_input.get("subagentType")
    if role not in REVIEWER_ROLES:
        # 第一层 agent（scout/summarizer/coder）结束后清理其下所有 subagent 记录
        if role in FIRST_LAYER_ROLES:
            response = event.get("tool_response")
            parent_agent_id = _extract_agent_id(response) or ""
            if parent_agent_id:
                _clean_records_for_parent(parent_agent_id)
        return 0

    found = _find_record(
        tool_use_id=str(event.get("tool_use_id") or ""),
        session_id=str(event.get("session_id") or ""),
        role=role,
    )
    if not found:
        return 0
    path, data = found
    timestamp = _now()
    response = event.get("tool_response")
    data["agent_id"] = _extract_agent_id(response) or data.get("agent_id")
    data["output_file"] = _extract_output_file(response) or data.get("output_file")
    data["status"] = "failed" if failed else "running"
    data["updated_at"] = _iso(timestamp)
    data["updated_at_epoch"] = timestamp
    data["last_heartbeat_at"] = _iso(timestamp)
    data["last_heartbeat_epoch"] = timestamp
    if failed:
        data["failure_reason"] = str(event.get("error") or "Agent tool call failed")
    _save(path, data)
    return 0


def _handle_subagent_start(event: dict[str, Any]) -> int:
    role = event.get("agent_type")
    agent_id = event.get("agent_id")
    if role not in REVIEWER_ROLES or not agent_id:
        return 0
    found = _find_record(
        session_id=str(event.get("session_id") or ""),
        role=str(role),
    )
    if not found:
        return 0
    path, data = found
    timestamp = _now()
    data.update(
        {
            "agent_id": str(agent_id),
            "status": "running",
            "updated_at": _iso(timestamp),
            "updated_at_epoch": timestamp,
            "last_heartbeat_at": _iso(timestamp),
            "last_heartbeat_epoch": timestamp,
        }
    )
    _save(path, data)
    return 0


def _handle_subagent_stop(event: dict[str, Any]) -> int:
    agent_id = str(event.get("agent_id") or "")
    role = event.get("agent_type")
    if role not in REVIEWER_ROLES or not agent_id:
        return 0
    found = _find_record(agent_id=agent_id)
    if not found:
        return 0
    path, data = found
    timestamp = _now()
    result = str(event.get("last_assistant_message") or "")
    lowered = result.lower()
    failed = any(
        marker in lowered
        for marker in (
            "insufficient account balance",
            "rate limit",
            "network error",
            "api error",
            "timed out",
        )
    )
    data["status"] = "failed" if failed else "completed"
    data["updated_at"] = _iso(timestamp)
    data["updated_at_epoch"] = timestamp
    data["last_heartbeat_at"] = _iso(timestamp)
    data["last_heartbeat_epoch"] = timestamp
    if failed:
        data["failure_reason"] = result[-1000:]
    _save(path, data)
    return 0


def handle_hook(event: dict[str, Any]) -> int:
    hook = event.get("hook_event_name")
    if hook == "PreToolUse":
        return _handle_pre_tool(event)
    if hook == "PostToolUse":
        return _handle_post_tool(event)
    if hook == "PostToolUseFailure":
        return _handle_post_tool(event, failed=True)
    if hook == "SubagentStart":
        return _handle_subagent_start(event)
    if hook == "SubagentStop":
        return _handle_subagent_stop(event)
    return 0


def _status(agent_id: str, timeout: int) -> tuple[Path, dict[str, Any]]:
    found = _find_record(agent_id=agent_id)
    if not found:
        raise SystemExit(f"未找到 agent_id={agent_id} 的监督记录")
    path, data = found
    refreshed = _refresh_status(data, timeout)
    if refreshed != data:
        refreshed["updated_at"] = _iso()
        refreshed["updated_at_epoch"] = _now()
        _save(path, refreshed)
    return path, refreshed


def command_status(args: argparse.Namespace) -> int:
    _, data = _status(args.agent_id, args.timeout)
    print(json.dumps(data, ensure_ascii=False))
    return 0


def command_wait(args: argparse.Namespace) -> int:
    while True:
        statuses = []
        for agent_id in args.agent_id:
            _, data = _status(agent_id, args.timeout)
            statuses.append(data)
        active = [item for item in statuses if item.get("status") in {"claimed", "running"}]
        if not active:
            print(json.dumps({"agents": statuses}, ensure_ascii=False))
            return 2 if any(item.get("status") in {"failed", "stale"} for item in statuses) else 0
        time.sleep(args.poll)


def command_clean(args: argparse.Namespace) -> int:
    _clean_records_for_parent(args.agent_id)
    print(json.dumps({"cleaned": True, "agent_id": args.agent_id}))
    return 0


def command_retry(args: argparse.Namespace) -> int:
    path, data = _status(args.agent_id, args.timeout)
    if data.get("status") not in {"failed", "stale", "completed"}:
        raise SystemExit(
            f"{data.get('role')} 当前状态为 {data.get('status')}，未失败且心跳未超时，禁止重试"
        )
    if int(data.get("attempt", 1)) >= int(data.get("max_attempts", DEFAULT_MAX_ATTEMPTS)):
        raise SystemExit(f"{data.get('role')} 已达到最大尝试次数")
    data["status"] = "retryable"
    data["retry_reason"] = args.reason
    data["retry_requested_at"] = _iso()
    data["updated_at"] = _iso()
    data["updated_at_epoch"] = _now()
    _save(path, data)
    print(json.dumps(data, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    status = subparsers.add_parser("status")
    status.add_argument("--agent-id", required=True)
    status.add_argument("--timeout", type=int, default=DEFAULT_HEARTBEAT_TIMEOUT)
    status.set_defaults(func=command_status)

    wait = subparsers.add_parser("wait")
    wait.add_argument("--agent-id", action="append", required=True)
    wait.add_argument("--timeout", type=int, default=DEFAULT_HEARTBEAT_TIMEOUT)
    wait.add_argument("--poll", type=int, default=DEFAULT_POLL_INTERVAL)
    wait.set_defaults(func=command_wait)

    retry = subparsers.add_parser("retry")
    retry.add_argument("--agent-id", required=True)
    retry.add_argument("--reason", required=True)
    retry.add_argument("--timeout", type=int, default=DEFAULT_HEARTBEAT_TIMEOUT)
    retry.set_defaults(func=command_retry)

    clean = subparsers.add_parser("clean")
    clean.add_argument("--agent-id", required=True)
    clean.set_defaults(func=command_clean)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command:
        return args.func(args)
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    return handle_hook(event)


if __name__ == "__main__":
    raise SystemExit(main())
