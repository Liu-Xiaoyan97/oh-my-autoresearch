#!/usr/bin/env python3
"""validate_subagent_result.py - 校验 subagent 返回 JSON。

根据 agent 名称和阶段选择对应的 schema:
    runtime/agents/<agent>/schemas/*.schema.json

用法:
    python validate_subagent_result.py <agent_name> <phase> <json_file>
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("警告: jsonschema 未安装，跳过校验", file=sys.stderr)
    sys.exit(0)


def validate(agent_name: str, phase: int, json_file: str, runtime_root: str) -> dict:
    """校验 subagent 返回的 JSON 是否符合对应 schema。"""
    data = json.loads(Path(json_file).read_text(encoding="utf-8"))

    # 根据 agent 名称查找 schema 目录
    agent_schema_dir = Path(runtime_root) / "agents" / agent_name / "schemas"

    if not agent_schema_dir.exists():
        return {"valid": False, "error": f"Schema 目录不存在: {agent_schema_dir}"}

    # 根据阶段选择 schema 文件
    schema_map = {
        1: {
            "orthogonal-direction-scout": "orthogonal-set.schema.json",
            "summarizer": "decision.schema.json",
            "flow-arch-reviewer": "proposal.schema.json",
            "math-theorist": "proposal.schema.json",
            "numerical-debugger": "proposal.schema.json",
            "coder": "patch-plan.schema.json",
        },
        9: {
            "summarizer": "recovery-summary.schema.json",
            "flow-arch-reviewer": "recovery.schema.json",
            "math-theorist": "recovery.schema.json",
            "numerical-debugger": "recovery.schema.json",
        },
    }

    schema_file = schema_map.get(phase, {}).get(agent_name)
    if not schema_file:
        return {"valid": False, "error": f"无匹配的 schema: agent={agent_name}, phase={phase}"}

    schema_path = agent_schema_dir / schema_file
    if not schema_path.exists():
        return {"valid": False, "error": f"Schema 文件不存在: {schema_path}"}

    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    try:
        jsonschema.validate(instance=data, schema=schema)
        return {"valid": True, "schema": str(schema_path)}
    except jsonschema.ValidationError as e:
        return {"valid": False, "error": str(e.message)}


def main():
    if len(sys.argv) < 4:
        print("用法: validate_subagent_result.py <agent_name> <phase> <json_file>", file=sys.stderr)
        sys.exit(1)

    agent_name = sys.argv[1]
    phase = int(sys.argv[2])
    json_file = sys.argv[3]
    if len(sys.argv) > 4:
        runtime_root = sys.argv[4]
    else:
        runtime_root = str((Path(__file__).resolve().parent / ".." / ".." / "runtime").resolve())

    result = validate(agent_name, phase, json_file, runtime_root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
