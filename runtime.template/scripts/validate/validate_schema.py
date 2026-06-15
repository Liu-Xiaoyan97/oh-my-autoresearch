#!/usr/bin/env python3
"""validate_schema.py - 通用 JSON schema 校验器。

用法:
    python validate_schema.py <json_file> <schema_file>
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("警告: jsonschema 未安装，使用基本校验", file=sys.stderr)
    jsonschema = None


def validate(json_file: str, schema_file: str) -> dict:
    """校验 JSON 文件是否符合 schema。"""
    data = json.loads(Path(json_file).read_text(encoding="utf-8"))
    schema = json.loads(Path(schema_file).read_text(encoding="utf-8"))

    if jsonschema is None:
        required = schema.get("required", [])
        missing = [field for field in required if field not in data]
        if missing:
            return {"valid": False, "error": f"缺少必填字段: {', '.join(missing)}"}
        return {"valid": True, "note": "jsonschema 未安装，仅做 required 字段检查"}

    try:
        jsonschema.validate(instance=data, schema=schema)
        return {"valid": True}
    except jsonschema.ValidationError as e:
        return {"valid": False, "error": str(e.message)}


def main():
    if len(sys.argv) < 3:
        print("用法: validate_schema.py <json_file> <schema_file>", file=sys.stderr)
        sys.exit(1)

    result = validate(sys.argv[1], sys.argv[2])
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
