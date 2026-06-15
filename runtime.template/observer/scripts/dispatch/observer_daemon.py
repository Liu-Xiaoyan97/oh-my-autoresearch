#!/usr/bin/env python3
"""observer_daemon.py - Observer 主进程。

职责:
- 读取 config
- 加载 offset
- 轮询 events.jsonl
- 消费新事件
- 调用 dispatch_event
- 成功后保存 offset
- 失败后写 deadletter

用法:
    python observer_daemon.py [runtime_root]
"""

import json
import signal
import sys
import time
from pathlib import Path

from consume_events import consume_next_events
from dispatch_event import dispatch_one
from load_offset import load_offset
from save_offset import save_offset
from write_deadletter import write_deadletter

SHUTDOWN = False


def handle_signal(signum, frame):
    global SHUTDOWN
    SHUTDOWN = True


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    config_path = Path(runtime_root) / "observer" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    events_file = Path(runtime_root) / config["events_path"]
    offsets_file = Path(runtime_root) / config["offsets_path"]
    deadletter_file = Path(runtime_root) / config["deadletter_path"]

    offset = load_offset(offsets_file)
    poll_interval = config.get("poll_interval", 5)

    print(f"[observer_daemon] 启动, offset={offset}, poll_interval={poll_interval}s")

    while not SHUTDOWN:
        try:
            events = consume_next_events(events_file, offset, count=10)
            if not events:
                time.sleep(poll_interval)
                continue

            for event in events:
                if SHUTDOWN:
                    break

                try:
                    success = dispatch_one(runtime_root, event)
                    if success:
                        offset += 1
                        save_offset(offsets_file, offset)
                    else:
                        write_deadletter(deadletter_file, event)
                except Exception as e:
                    print(f"[observer_daemon] 事件处理失败: {e}", file=sys.stderr)
                    write_deadletter(deadletter_file, event)

        except Exception as e:
            print(f"[observer_daemon] 轮询错误: {e}", file=sys.stderr)
            time.sleep(poll_interval)

    print("[observer_daemon] 已停止")


if __name__ == "__main__":
    main()
