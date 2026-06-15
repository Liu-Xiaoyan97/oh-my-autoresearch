#!/usr/bin/env python3
"""write_state.py - 更新 runtime/states/states.json（状态机检查点）。

主程序（team-lead）不直接写 states.json；它 emit `state` 事件，由 observer 在此
原子更新 states.json。只更新 payload 中给出的合法字段，其余保持原值。

payload 形如（两种均可）：
    {"current_step": 3, "next_step": 4}
    {"data": {"current_step": 7, "next_step": 8, "iteration": 2, "exp_name": "exp_2"}}
"""

import json
import sys
from pathlib import Path

ALLOWED_FIELDS = ("current_step", "next_step", "iteration", "exp_name")


def _states_path(runtime_root: str) -> Path:
    return Path(runtime_root) / "states" / "states.json"


def write(runtime_root: str, payload: dict) -> bool:
    path = _states_path(runtime_root)
    try:
        state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        # payload 可直接是字段，也可包在 data 里
        fields = payload.get("data", payload) if isinstance(payload, dict) else {}
        updated = False
        for key in ALLOWED_FIELDS:
            if key in fields and fields[key] is not None:
                state[key] = fields[key]
                updated = True
        if not updated:
            print("[write_state] payload 无可更新字段", file=sys.stderr)
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        # 原子写：先写临时文件再替换
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
        return True
    except Exception as e:
        print(f"[write_state] 错误: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    payload = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    ok = write(runtime_root, payload)
    sys.exit(0 if ok else 1)
