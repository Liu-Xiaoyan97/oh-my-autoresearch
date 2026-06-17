#!/usr/bin/env python3
"""validate_subagent_result.py - 校验 subagent 返回 JSON，校验成功后自动发射对应事件。

根据 agent 名称和阶段选择对应的 schema:
    runtime/agents/<agent>/schemas/*.schema.json

校验通过后自动 emit 对应事件（无需 LLM 手动调用 emit_event.py）：
    orthogonal-direction-scout (phase=1) → exploration update_orthogonal_candidates
    summarizer (phase=1)                  → exploration update_decision
    coder                                 → exploration update_commit
    summarizer (phase=9)                  → 跳过（需 LLM 对比 baseline 后决定）

用法:
    python validate_subagent_result.py <agent_name> <phase> <json_file> [runtime_root]
"""

import json
import subprocess
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    jsonschema = None


# ── 自动发射映射 ──────────────────────────────────────────────────
# 在 schema 校验通过后自动调用 emit_event.py，LLM 无需再手动发射
EMIT_MAP = {
    "orthogonal-direction-scout": {
        1: ("exploration", {"action": "update_orthogonal_candidates"}),
    },
    "summarizer": {
        1: ("exploration", {"action": "update_decision"}),
        # phase=9 由 LLM 对比 baseline 后手动处理 knowledge 事件，不自动发射
    },
    "coder": {
        # coder phase=1: patch-plan 无 commit 信息，不自动发射
        # coder phase=5: commit-result，发射 update_commit
        5: ("exploration", {"action": "update_commit"}),
    },
}
# ────────────────────────────────────────────────────────────────


def _emit_path(runtime_root: str) -> str:
    return str(Path(runtime_root) / "observer" / "scripts" / "ingest" / "emit_event.py")


def _auto_emit(agent_name: str, phase: int, data: dict, runtime_root: str) -> dict:
    """校验通过后自动发射对应事件。返回 emitted 信息，失败时返回 error。"""
    # 查找匹配的发射配置
    agent_config = EMIT_MAP.get(agent_name, {})
    emit_config = agent_config.get(phase, agent_config.get("*"))
    if not emit_config:
        return {"emitted": False, "reason": f"agent={agent_name} phase={phase} 无自动发射映射"}

    event_type, payload_template = emit_config
    payload = json.loads(json.dumps(payload_template))  # deep copy

    # 根据 event_type 填充 payload
    try:
        if event_type == "exploration":
            action = payload["action"]
            if action == "update_orthogonal_candidates":
                # orthogonal-set.schema.json → candidates 数组
                candidates = (
                    data.get("candidates", data)
                    if isinstance(data, dict)
                    else data
                )
                payload["data"] = {"orthogonal_direction_scout": candidates}
            elif action == "update_decision":
                # decision.schema.json → 提取 decision 字符串 + reason
                decision_name = data.get("decision", "")
                if not decision_name and "selected_candidate" in data:
                    idx = data["selected_candidate"]
                    decision_name = f"candidate_{idx}"
                payload["data"] = {
                    "decision": decision_name,
                    "reason": data.get("reason", ""),
                }
            elif action == "update_commit":
                # commit-result.schema.json → commit_id + 摘要
                payload["data"] = {
                    "commit_id": data.get("commit_id", ""),
                    "changes_summary": data.get("changes_summary", ", ".join(data.get("files_changed", []))),
                    "smoke_test_status": "passed" if data.get("smoke_test_passed") else "",
                }
        else:
            return {"emitted": False, "reason": f"未知 event_type: {event_type}"}
    except Exception as e:
        return {"emitted": False, "error": str(e)}

    # 调用 emit_event.py
    emit_py = _emit_path(runtime_root)
    if not Path(emit_py).exists():
        return {"emitted": False, "error": f"emit_event.py 不存在: {emit_py}"}

    payload_str = json.dumps(payload, ensure_ascii=False)
    try:
        result = subprocess.run(
            ["python3", emit_py, event_type, payload_str, runtime_root],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return {"emitted": True, "event_type": event_type, "action": payload.get("action")}
        else:
            return {"emitted": False, "error": result.stderr.strip() or result.stdout.strip()}
    except Exception as e:
        return {"emitted": False, "error": str(e)}


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
        5: {
            "coder": "commit-result.schema.json",
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
        result = {"valid": True, "schema": str(schema_path)}

        # ── 校验通过，自动发射事件 ──
        emit_result = _auto_emit(agent_name, phase, data, runtime_root)
        result["auto_emitted"] = emit_result

        return result
    except jsonschema.ValidationError as e:
        return {"valid": False, "error": str(e.message)}


def main():
    if len(sys.argv) < 4:
        print("用法: validate_subagent_result.py <agent_name> <phase> <json_file> [runtime_root]", file=sys.stderr)
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
    sys.exit(0 if result.get("valid") else 1)


if __name__ == "__main__":
    main()
