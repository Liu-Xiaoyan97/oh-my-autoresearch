#!/usr/bin/env python3
"""validate_log_event.py - 校验 log event payload。"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    jsonschema = None


def validate(event: dict) -> dict:
    """校验 log event 是否符合 schema。"""
    schema_path = Path(__file__).parents[2] / "schemas" / "log-event.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    if jsonschema is None:
        # 没有 jsonschema 包时做基本字段检查
        required = ["exp_name", "timestamp", "level", "source", "message"]
        missing = [f for f in required if f not in event]
        return {"valid": len(missing) == 0, "missing_fields": missing}

    try:
        jsonschema.validate(instance=event, schema=schema)
        return {"valid": True}
    except jsonschema.ValidationError as e:
        return {"valid": False, "error": str(e.message)}


def main():
    if len(sys.argv) < 2:
        print("用法: validate_log_event.py '<event_json>'", file=sys.stderr)
        sys.exit(1)

    event = json.loads(sys.argv[1])
    result = validate(event)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
