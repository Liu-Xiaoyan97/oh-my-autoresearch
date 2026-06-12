#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update workflow templates. This command is not implemented yet."
    )
    parser.parse_args()
    print(
        "update_templates is not implemented yet. "
        "Edit templates directly and validate with scripts/validate_workflow.py --root templates/nn_architecture.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
