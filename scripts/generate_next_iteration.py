#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the next experiment iteration. This command is not implemented yet."
    )
    parser.parse_args()
    print(
        "generate_next_iteration is not implemented yet. "
        "Use AgentTeam Phase B output and update runtime/state/current_iteration.json explicitly.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
