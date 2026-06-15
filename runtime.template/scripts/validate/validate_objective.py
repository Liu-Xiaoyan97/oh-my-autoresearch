#!/usr/bin/env python3
"""validate_objective.py - 校验 runtime/states/objective.json。"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_schema import validate


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"

    objective_file = Path(runtime_root) / "states" / "objective.json"
    schema_file = Path(runtime_root) / "schemas" / "objective.schema.json"

    if not objective_file.exists():
        print(json.dumps({"valid": False, "error": "objective.json 不存在"}))
        sys.exit(1)

    result = validate(str(objective_file), str(schema_file))
    result["file"] = str(objective_file)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("valid", False) else 1)


if __name__ == "__main__":
    main()
