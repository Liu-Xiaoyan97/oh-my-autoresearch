#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score AgentTeam research proposals. This command is not implemented yet."
    )
    parser.parse_args()
    print(
        "score_proposals is not implemented yet. "
        "Record proposal scoring in runtime/debates/<exp_name>.md until a deterministic scorer exists.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
