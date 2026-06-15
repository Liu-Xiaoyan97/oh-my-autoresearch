#!/usr/bin/env python3
"""validate_baseline.py - 校验 baseline 是否完整。

应检查 baseline.json 是否包含必要字段。
"""

import json
import sys
from pathlib import Path


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"

    baseline_file = Path(runtime_root) / "knowledges" / "baseline.json"

    # 检查 baseline.json 是否存在且有必要字段
    if not baseline_file.exists():
        print(json.dumps({"valid": False, "error": "baseline.json 不存在"}))
        sys.exit(1)

    baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
    required_fields = ["exp_name", "method_summary"]
    missing = [f for f in required_fields if f not in baseline]

    if missing:
        print(json.dumps({"valid": False, "missing_fields": missing}))
        sys.exit(1)

    print(json.dumps({"valid": True, "message": "baseline.json 校验通过"}))


if __name__ == "__main__":
    main()
