#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_state import repo_root, run_validation  # noqa: E402


def main() -> int:
    root = repo_root()
    ok, output = run_validation(root)
    if not ok:
        print(
            "AutoResearch schema validation failed after a file write. "
            "Use the phase scripts and workflow schemas before continuing.\n",
            file=sys.stderr,
        )
        print(output, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
