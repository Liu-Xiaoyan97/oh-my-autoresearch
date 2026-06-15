#!/usr/bin/env python3
"""dispatch_event.py - 根据 event_type 分发到对应 writer。

event_type → writer:
    log          -> writers/write_log.py
    experiments  -> writers/write_experiments.py
    exploration  -> writers/write_exploration.py
    knowledge    -> writers/write_knowledge.py
"""

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def dispatch_one(runtime_root: str, event: dict) -> bool:
    """分发一个事件到对应 writer，返回是否成功。"""
    event_type = event.get("event_type", "")
    payload = event.get("payload", {})

    # 加载 writer 模块
    writers_dir = SCRIPT_DIR.parent / "writers"

    writer_map = {
        "log": "write_log",
        "experiments": "write_experiments",
        "exploration": "write_exploration",
        "knowledge": "write_knowledge",
    }

    module_name = writer_map.get(event_type)
    if not module_name:
        print(f"[dispatch] 未知 event_type: {event_type}", file=sys.stderr)
        return False

    writer_path = writers_dir / f"{module_name}.py"
    if not writer_path.exists():
        print(f"[dispatch] Writer 不存在: {writer_path}", file=sys.stderr)
        return False

    # 动态导入并执行
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, writer_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    try:
        return module.write(runtime_root, payload)
    except Exception as e:
        print(f"[dispatch] Writer 执行失败: {e}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 2:
        print("用法: dispatch_event.py [runtime_root] '<event_json>'", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) >= 3:
        runtime_root = sys.argv[1]
        event_arg = sys.argv[2]
    else:
        runtime_root = "runtime"
        event_arg = sys.argv[1]

    event = json.loads(event_arg)
    success = dispatch_one(runtime_root, event)
    print(json.dumps({"dispatched": success}))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
