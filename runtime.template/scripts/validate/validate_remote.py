#!/usr/bin/env python3
"""validate_remote.py - 校验 remote 训练配置：hosts 非空 + ssh 链可达。

hosts 每项可为字符串(SSH 别名)或对象({"host","user","port","keyPath"})。
非 remote 模式直接跳过。
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.load_json import load_json


def _dest(h):
    if isinstance(h, str):
        return h.strip()
    host = str(h.get("host", "")).strip()
    user = str(h.get("user", "")).strip()
    return f"{user}@{host}" if user else host


def _reachable(dest: str, jumps: list[str]) -> tuple[bool, str]:
    """检查 dest 可达；jumps 为其前驱跳板链（嵌套 host 经 ProxyJump 到达）。"""
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8"]
    if jumps:
        cmd += ["-J", ",".join(jumps)]
    cmd += [dest, "echo ok"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        return (r.returncode == 0, r.stderr.strip() if r.returncode != 0 else "ok")
    except subprocess.TimeoutExpired:
        return (False, "timeout")
    except Exception as e:  # noqa: BLE001
        return (False, str(e))


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"

    try:
        objective = load_json(str(Path(runtime_root) / "states" / "objective.json"))
    except (FileNotFoundError, json.JSONDecodeError):
        print(json.dumps({"valid": False, "error": "objective.json 不存在或格式错误"}))
        sys.exit(1)

    checks = []
    is_remote = objective.get("remote", False)
    checks.append({"name": "remote_flag", "passed": True, "message": f"remote={is_remote}"})

    if not is_remote:
        checks.append({"name": "hosts_non_empty", "passed": True, "message": "非 remote 模式，跳过检查"})
        print(json.dumps({"valid": True, "checks": checks}, ensure_ascii=False))
        return

    hosts = objective.get("hosts", []) or []
    dests = [d for d in (_dest(h) for h in hosts) if d]
    if not dests:
        checks.append({"name": "hosts_non_empty", "passed": False, "message": "hosts 为空或无效"})
        print(json.dumps({"valid": False, "checks": checks}, ensure_ascii=False))
        sys.exit(1)
    checks.append({"name": "hosts_non_empty", "passed": True, "message": f"hosts: {dests}"})

    all_ok = True
    for i, d in enumerate(dests):
        ok, msg = _reachable(d, dests[:i])  # 经前驱跳板链可达性
        all_ok = all_ok and ok
        via = f" via {','.join(dests[:i])}" if i else ""
        checks.append({"name": f"reachable:{d}{via}", "passed": ok, "message": msg})

    print(json.dumps({"valid": all_ok, "checks": checks}, ensure_ascii=False))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
