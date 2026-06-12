#!/usr/bin/env python3

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compact runtime memory into knowledge files. This command is not implemented yet."
    )
    parser.parse_args()
    print(
        "compact_memory is not implemented yet. "
        "Do not treat chat compaction as runtime memory compaction; preserve runtime files as the source of truth.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
