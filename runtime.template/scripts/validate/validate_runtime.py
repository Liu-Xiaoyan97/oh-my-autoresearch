#!/usr/bin/env python3
"""validate_runtime.py - Phase 0 综合校验入口。

应调用 states、objective、baseline、remote 等校验。
"""

import json
import subprocess
import sys
from pathlib import Path


def main():
    runtime_root = sys.argv[1] if len(sys.argv) > 1 else "runtime"
    scripts_dir = Path(runtime_root) / "scripts" / "validate"

    checks = []
    all_pass = True

    validators = [
        ("states", "validate_states.py"),
        ("objective", "validate_objective.py"),
        ("baseline", "validate_baseline.py"),
        ("remote", "validate_remote.py"),
        ("db_schema", "validate_db_schema.py"),
    ]

    for name, script in validators:
        script_path = scripts_dir / script
        if not script_path.exists():
            checks.append({"name": name, "passed": False, "message": f"脚本不存在: {script}"})
            all_pass = False
            continue

        try:
            result = subprocess.run(
                ["python3", str(script_path), runtime_root],
                capture_output=True, text=True, timeout=30,
            )
            output = json.loads(result.stdout.strip()) if result.stdout.strip() else {}
            passed = output.get("valid", False) and result.returncode == 0
            checks.append({
                "name": name,
                "passed": passed,
                "message": output.get("error", output.get("message", "")) if not passed else "OK",
            })
            if not passed:
                all_pass = False
        except Exception as e:
            checks.append({"name": name, "passed": False, "message": str(e)})
            all_pass = False

    # 事件链完整性校验（warning 级别，不阻断 Phase 0）
    chain_check = _check_event_chain(runtime_root)
    checks.append(chain_check)

    print(json.dumps({"pass": all_pass, "checks": checks}, indent=2))
    sys.exit(0 if all_pass else 1)


def _check_event_chain(runtime_root: str) -> dict:
    """子校验：事件链完整性（非阻塞，仅有 warning）。返回 check 结构。"""
    validator_path = Path(__file__).resolve().parent / "validate_event_chain.py"
    if not validator_path.exists():
        return {"name": "event_chain", "passed": True, "message": "validate_event_chain.py 不存在，跳过"}

    try:
        result = subprocess.run(
            ["python3", str(validator_path), runtime_root],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(result.stdout.strip()) if result.stdout.strip() else {}
        if data.get("valid", True):
            return {"name": "event_chain", "passed": True, "message": "OK"}
        # 缺失事件时用 warning 而非 failure（Phase 0 不阻断）
        missing = [c["check"] for c in data.get("checks", []) if not c.get("passed")]
        return {
            "name": "event_chain",
            "passed": True,  # warning 级别，不阻断
            "message": f"事件链不完整，缺失: {', '.join(missing)}（建议运行 validate_event_chain.py --fix 修复）",
        }
    except Exception as e:
        return {"name": "event_chain", "passed": True, "message": f"事件链校验异常: {e}"}


if __name__ == "__main__":
    main()
