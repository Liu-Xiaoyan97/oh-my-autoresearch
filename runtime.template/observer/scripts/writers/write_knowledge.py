#!/usr/bin/env python3
"""write_knowledge.py - 写入 baseline / learned / rejected JSON。

必须使用原子写，避免 JSON 损坏。
"""

import json
import sys
from pathlib import Path

SCRIPTS_ROOT = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(SCRIPTS_ROOT / "utils"))
from atomic_write import atomic_write


def write(runtime_root: str, payload: dict) -> bool:
    """根据 action 写入 knowledge 文件。"""
    action = payload.get("action", "")
    default_target = {
        "update_baseline": "baseline.json",
        "append_learned": "learned.json",
        "append_rejected": "rejected.json",
    }.get(action, "")
    target_file = payload.get("target_file") or default_target
    data = payload.get("data", {})

    knowledge_dir = Path(runtime_root) / "knowledges"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    if target_file not in {"baseline.json", "learned.json", "rejected.json"}:
        print(f"[write_knowledge] 非法 target_file: {target_file}", file=sys.stderr)
        return False
    file_path = knowledge_dir / target_file

    try:
        if not target_file:
            print(f"[write_knowledge] 未知 action 或 target_file 为空: {action}", file=sys.stderr)
            return False

        if action == "update_baseline":
            atomic_write(file_path, data)

        elif action == "append_learned":
            existing = []
            if file_path.exists():
                existing = json.loads(file_path.read_text(encoding="utf-8"))
            existing.append(data)
            atomic_write(file_path, existing)

        elif action == "append_rejected":
            existing = []
            if file_path.exists():
                existing = json.loads(file_path.read_text(encoding="utf-8"))
            existing.append(data)
            atomic_write(file_path, existing)

        else:
            print(f"[write_knowledge] 未知 action: {action}", file=sys.stderr)
            return False

        return True

    except Exception as e:
        print(f"[write_knowledge] 错误: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    import sys
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    write(runtime_root, payload)
