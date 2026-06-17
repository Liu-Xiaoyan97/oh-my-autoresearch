#!/usr/bin/env python3
"""observer_daemon.py - 自治 Observer 主进程。

职责：
- 轮询 events.jsonl，消费新事件 → dispatch 到确定性 writer（DB/state/knowledge/log）。
- state 事件 current_step==9（一轮收尾）→ best-effort 触发 LLM 观察生成(独立 api/key)。
- control 事件 action==reset → 自清 events/offsets/run（observer 自治, 主程序只 emit 事件）。
- 每轮写 run/observer.status 心跳, 供 /loop-status 只读查看(主程序不调用 observer)。

主程序绝不调用本进程任何函数；唯一接口是向 events.jsonl 追加事件。
"""

import json
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from consume_events import consume_next_events
from dispatch_event import dispatch_one
from load_offset import load_offset
from save_offset import save_offset
from write_deadletter import write_deadletter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "observe"))

SHUTDOWN = False


def handle_signal(signum, frame):
    global SHUTDOWN
    SHUTDOWN = True


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


def _maybe_observe(runtime_root, event):
    """state 收尾事件触发 LLM 观察, best-effort, 任何异常都吞掉。"""
    if event.get("event_type") != "state":
        return
    payload = event.get("payload", {})
    if payload.get("current_step") != 9:
        return
    exp_name = payload.get("exp_name", "")
    if not exp_name:
        return
    try:
        import generate_observation
        result = generate_observation.generate(runtime_root, exp_name)
        print(f"[observer_daemon] observe({exp_name}): {result}")
    except Exception as e:
        print(f"[observer_daemon] 观察生成异常(忽略): {e}", file=sys.stderr)


def _self_reset(runtime_root, events_file, offsets_file, deadletter_file):
    """control:reset —— observer 自清 events/offsets/run（保留 .gitkeep）。"""
    try:
        events_file.write_text("", encoding="utf-8")
        deadletter_file.write_text("", encoding="utf-8")
        offsets_file.write_text("0", encoding="utf-8")
        run_log = Path(runtime_root) / "observer" / "run" / "observer.log"
        if run_log.exists():
            run_log.write_text("", encoding="utf-8")
        print("[observer_daemon] control:reset 已自清 events/offsets/run")
    except Exception as e:
        print(f"[observer_daemon] 自清失败: {e}", file=sys.stderr)


def _write_status(runtime_root, offset, llm_enabled):
    try:
        status = {
            "pid": os.getpid(),
            "alive": True,
            "offset": offset,
            "llm_enabled": llm_enabled,
            "last_poll": datetime.now(timezone.utc).isoformat(),
        }
        sp = Path(runtime_root) / "observer" / "run" / "observer.status"
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps(status, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _llm_enabled(runtime_root) -> bool:
    base = Path(runtime_root) / "observer"
    for name in ("llm.config.json", "llm.config.example.json"):
        p = base / name
        if p.exists():
            try:
                c = json.loads(p.read_text(encoding="utf-8"))
                return bool(c.get("enabled") and c.get("api_key") and c.get("model"))
            except Exception:
                return False
    return False


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    config_path = Path(runtime_root) / "observer" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    events_file = Path(runtime_root) / config["events_path"]
    offsets_file = Path(runtime_root) / config["offsets_path"]
    deadletter_file = Path(runtime_root) / config["deadletter_path"]

    offset = load_offset(offsets_file)
    poll_interval = config.get("poll_interval", 5)
    llm_enabled = _llm_enabled(runtime_root)

    print(f"[observer_daemon] 启动, offset={offset}, poll={poll_interval}s, llm_enabled={llm_enabled}")
    _write_status(runtime_root, offset, llm_enabled)

    while not SHUTDOWN:
        try:
            events = consume_next_events(events_file, offset, count=10)
            if not events:
                _write_status(runtime_root, offset, llm_enabled)
                time.sleep(poll_interval)
                continue

            for event in events:
                if SHUTDOWN:
                    break

                # control 事件不进 writer，由 observer 自治处理
                if event.get("event_type") == "control":
                    if event.get("payload", {}).get("action") == "reset":
                        _self_reset(runtime_root, events_file, offsets_file, deadletter_file)
                        offset = 0
                        save_offset(offsets_file, offset)
                        break  # 重新从空文件轮询
                    else:
                        offset += 1
                        save_offset(offsets_file, offset)
                    continue

                try:
                    success = dispatch_one(runtime_root, event)
                    if success:
                        offset += 1
                        save_offset(offsets_file, offset)
                        _maybe_observe(runtime_root, event)
                    else:
                        write_deadletter(deadletter_file, event)
                        offset += 1
                        save_offset(offsets_file, offset)
                except Exception as e:
                    print(f"[observer_daemon] 事件处理失败: {e}", file=sys.stderr)
                    write_deadletter(deadletter_file, event)
                    offset += 1
                    save_offset(offsets_file, offset)

            _write_status(runtime_root, offset, llm_enabled)

        except Exception as e:
            print(f"[observer_daemon] 轮询错误: {e}", file=sys.stderr)
            time.sleep(poll_interval)

    _write_status(runtime_root, offset, llm_enabled)
    print("[observer_daemon] 已停止")


if __name__ == "__main__":
    main()
