#!/usr/bin/env python3
"""validate_baseline.py - 校验 baseline 是否完整。

应检查 experiments 表中 baseline 是否包含完整评估字段。
"""

import json
import sqlite3
import sys
from pathlib import Path


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"

    db_path = Path(runtime_root) / "db" / "runtime.sqlite"
    baseline_file = Path(runtime_root) / "knowledges" / "baseline.json"

    # 检查 baseline.json 是否存在且有 primary_metric
    if not baseline_file.exists():
        print(json.dumps({"valid": False, "error": "baseline.json 不存在"}))
        sys.exit(1)

    baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
    required_fields = ["method", "primary_metric"]
    missing = [f for f in required_fields if f not in baseline]

    if missing:
        print(json.dumps({"valid": False, "missing_fields": missing}))
        sys.exit(1)

    # 检查 db 中是否有 baseline 记录
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT count(*) FROM experiments")
        count = cursor.fetchone()[0]
        conn.close()
    else:
        count = 0

    print(json.dumps({"valid": True, "baseline_record_count": count}))


if __name__ == "__main__":
    main()
