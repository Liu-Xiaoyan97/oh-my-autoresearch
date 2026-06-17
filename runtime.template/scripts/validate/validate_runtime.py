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

    print(json.dumps({"pass": all_pass, "checks": checks}, indent=2))
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
