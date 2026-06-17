#!/usr/bin/env python3
"""emit_event.py - Observer 事件入口。

接收 event_type 和 payload，补充 event_id、created_at，然后调用 append_event.py。
每次发射事件前自动检查 observer 存活状态，dead 则自动重启。

用法:
    python emit_event.py <event_type> '<payload_json>'
"""

import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _ensure_observer_alive(runtime_root: str) -> dict:
    """检查 observer 是否存活，dead 则自动重启。返回检查结果。"""
    run_dir = Path(runtime_root) / "observer" / "run"
    pid_file = run_dir / "observer.pid"
    status_file = run_dir / "observer.status"

    pid = None
    alive_by_pid = False
    alive_by_heartbeat = False
    status_info = {}

    # 1) PID 文件检查
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            alive_by_pid = True
        except (ValueError, ProcessLookupError, OSError):
            alive_by_pid = False

    # 2) 心跳检查
    if status_file.exists():
        try:
            status_info = json.loads(status_file.read_text())
            last_poll_str = status_info.get("last_poll", "")
            if last_poll_str:
                last_poll = datetime.fromisoformat(last_poll_str)
                age_seconds = (datetime.now(timezone.utc) - last_poll).total_seconds()
                alive_by_heartbeat = age_seconds < 60
        except (json.JSONDecodeError, ValueError):
            alive_by_heartbeat = False

    # 双层判定：PID 存活且心跳未超时
    healthy = alive_by_pid and alive_by_heartbeat

    if healthy:
        return {"healthy": True, "pid": pid}

    # ── 自动重启 ──
    # 清理残留 pid 文件
    if pid_file.exists():
        pid_file.unlink()

    daemon_script = Path(runtime_root) / "observer" / "scripts" / "dispatch" / "observer_daemon.py"
    events_dir = Path(runtime_root) / "observer" / "events"
    offsets_dir = Path(runtime_root) / "observer" / "offsets"

    events_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    offsets_dir.mkdir(parents=True, exist_ok=True)

    # 确保事件文件和偏移量文件存在
    (events_dir / "events.jsonl").touch()
    (events_dir / "deadletter.jsonl").touch()
    if not (offsets_dir / "events.offset").exists():
        (offsets_dir / "events.offset").write_text("0")

    log_file = str(run_dir / "observer.log")
    try:
        with open(log_file, "a") as log:
            proc = subprocess.Popen(
                ["python3", str(daemon_script), runtime_root],
                stdout=log, stderr=log,
            )
        new_pid = proc.pid
        (run_dir / "observer.pid").write_text(str(new_pid))

        # 等待心跳文件更新（最多 5 秒）
        for _ in range(10):
            time.sleep(0.5)
            if status_file.exists():
                try:
                    st = json.loads(status_file.read_text())
                    if st.get("last_poll"):
                        return {"healthy": True, "pid": new_pid, "restarted": True}
                except Exception:
                    pass

        return {"healthy": True, "pid": new_pid, "restarted": True, "warning": "pid 已启动，但心跳尚未确认"}
    except Exception as e:
        return {"healthy": False, "pid": None, "error": str(e)}


def main():
    if len(sys.argv) < 3:
        print("用法: emit_event.py <event_type> '<payload_json>'", file=sys.stderr)
        sys.exit(1)

    event_type = sys.argv[1]
    payload_str = sys.argv[2]
    runtime_root = sys.argv[3] if len(sys.argv) > 3 else "runtime"

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError as e:
        print(f"错误: payload 不是合法 JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # ── 每次发射前检查 observer 存活 ──
    health = _ensure_observer_alive(runtime_root)
    if not health["healthy"]:
        print(json.dumps({"emitted": False, "error": f"observer 守护失败: {health.get('error', '未知错误')}"}),
              file=sys.stderr)
        sys.exit(1)

    if health.get("restarted"):
        print(f"[observer watchdog] 已自动重启 observer (PID: {health['pid']})", file=sys.stderr)

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "payload": payload,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    events_file = Path(runtime_root) / "observer" / "events" / "events.jsonl"
    events_file.parent.mkdir(parents=True, exist_ok=True)

    # 使用 append_event 的逻辑追加
    sys.path.insert(0, str(Path(runtime_root) / "observer" / "scripts" / "ingest"))
    from append_event import append

    append(events_file, event)
    print(json.dumps({"emitted": True, "event_id": event["event_id"]}))


if __name__ == "__main__":
    main()
