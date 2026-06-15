#!/usr/bin/env python3
"""emit_event.py - Observer 事件入口。

接收 event_type 和 payload，补充 event_id、created_at，然后调用 append_event.py。

用法:
    python emit_event.py <event_type> '<payload_json>'
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


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
