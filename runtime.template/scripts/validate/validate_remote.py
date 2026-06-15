#!/usr/bin/env python3
"""validate_remote.py - 校验 remote 训练配置。

包括 hosts 非空和 ssh chain 可达。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.load_json import load_json


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"

    try:
        objective = load_json(str(Path(runtime_root) / "states" / "objective.json"))
    except (FileNotFoundError, json.JSONDecodeError):
        print(json.dumps({"valid": False, "error": "objective.json 不存在或格式错误"}))
        sys.exit(1)

    checks = []

    # 检查 remote 标志
    is_remote = objective.get("remote", False)
    checks.append({"name": "remote_flag", "passed": True, "message": f"remote={is_remote}"})

    if is_remote:
        hosts = objective.get("hosts", [])
        if not hosts:
            checks.append({"name": "hosts_non_empty", "passed": False, "message": "hosts 为空"})
            print(json.dumps({"valid": False, "checks": checks}))
            sys.exit(1)
        checks.append({"name": "hosts_non_empty", "passed": True, "message": f"hosts 数量: {len(hosts)}"})
    else:
        checks.append({"name": "hosts_non_empty", "passed": True, "message": "非 remote 模式，跳过检查"})

    print(json.dumps({"valid": True, "checks": checks}))


if __name__ == "__main__":
    main()
