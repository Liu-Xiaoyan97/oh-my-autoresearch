#!/usr/bin/env python3

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from runtime_manifest import DEFAULT_WORKFLOW, ManifestError, load_manifest, repository_root_from_script
from validate_workflow import validate_runtime


def sync_runtime(
    target_root: Path,
    workflow: str = DEFAULT_WORKFLOW,
    workflow_root: Path | None = None,
    dry_run: bool = False,
) -> list[str]:
    root = workflow_root or repository_root_from_script()
    manifest = load_manifest(workflow=workflow, workflow_root=root)
    target = target_root.resolve()
    actions: list[str] = []

    for rel_dir in manifest.ensure_dirs:
        destination = target / rel_dir
        if destination.is_dir():
            continue
        actions.append(f"create missing dir {rel_dir}")
        if not dry_run:
            destination.mkdir(parents=True, exist_ok=True)

    for item in manifest.copy_if_missing:
        source = root / item["from"]
        destination = target / item["to"]
        if destination.exists():
            actions.append(f"preserve existing {item['to']}")
            continue
        actions.append(f"restore missing {item['to']}")
        if not dry_run:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    if not dry_run:
        errors = validate_runtime(target, workflow=workflow, workflow_root=root)
        if errors:
            raise RuntimeError("Synced runtime failed validation:\n" + "\n".join(f"- {e}" for e in errors))

    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize a runtime repository without overwriting runtime state.")
    parser.add_argument("--root", default=".", help="Path to the research-runtime repository root.")
    parser.add_argument("--workflow", default=DEFAULT_WORKFLOW, help="Workflow manifest name.")
    parser.add_argument(
        "--workflow-root",
        default=None,
        help="Path to the oh-my-autoresearch repository. Defaults to this script's repository.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without writing files.")
    args = parser.parse_args()

    workflow_root = Path(args.workflow_root).resolve() if args.workflow_root else None
    try:
        actions = sync_runtime(
            target_root=Path(args.root),
            workflow=args.workflow,
            workflow_root=workflow_root,
            dry_run=args.dry_run,
        )
    except (ManifestError, RuntimeError, OSError) as exc:
        print(f"Runtime sync failed: {exc}", file=sys.stderr)
        return 1

    for action in actions:
        print(action)
    print("Runtime sync dry-run complete." if args.dry_run else "Runtime sync complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
