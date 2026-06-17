#!/usr/bin/env python3
"""update_exploration_field.py - 更新 exploration 表中的 orthogonal-direction-scout / decision / commit 字段。"""

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema_spec import DB_PATH


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    exp_name = sys.argv[2] if len(sys.argv) > 2 else ""
    field = sys.argv[3] if len(sys.argv) > 3 else ""
    value = sys.argv[4] if len(sys.argv) > 4 else ""

    if not exp_name or not field:
        print("用法: update_exploration_field.py <exp_name> <field> <value>", file=sys.stderr)
        sys.exit(1)

    field_map = {
        "orthogonal_direction_scout": "orthogonal_direction_scout",
        "decision": "decision",
        "commit_id": "commit_id",
    }
    col = field_map.get(field)
    if not col:
        print(f"错误: 未知字段 {field}，可选: {list(field_map.keys())}", file=sys.stderr)
        sys.exit(1)

    db_path = str(Path(runtime_root) / DB_PATH)
    conn = sqlite3.connect(db_path)
    now = datetime.now(timezone.utc).isoformat()

    if col in ("orthogonal_direction_scout", "decision"):
        try:
            json_value = json.dumps(json.loads(value), ensure_ascii=False)
        except json.JSONDecodeError:
            json_value = value
    else:
        json_value = value

    conn.execute(
        f"UPDATE exploration SET {col}=?, updated_at=? WHERE exp_name=?",
        (json_value, now, exp_name),
    )
    conn.commit()
    conn.close()
    print(f"Updated exploration field: {exp_name}.{field}")


if __name__ == "__main__":
    main()
