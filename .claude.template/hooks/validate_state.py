#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_validation(root: Path) -> tuple[bool, str]:
    commands = [
        ["./scripts/validate_runtime.sh"],
        ["./scripts/validate_schema.sh"],
    ]
    output: list[str] = []

    for command in commands:
        completed = subprocess.run(
            command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        output.append(f"$ {' '.join(command)}")
        output.append(completed.stdout.strip())
        if completed.returncode != 0:
            return False, "\n".join(part for part in output if part)

    return True, "\n".join(part for part in output if part)


def main() -> int:
    root = repo_root()
    ok, output = run_validation(root)
    if not ok:
        print(output, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
