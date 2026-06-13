#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Removal:
    path: Path
    reason: str


def load_team_names(teams_dir: Path) -> set[str]:
    if not teams_dir.exists():
        return set()
    return {p.name for p in teams_dir.iterdir() if p.is_dir()}


def team_has_config(team_dir: Path) -> bool:
    config_path = team_dir / "config.json"
    if not config_path.exists():
        return False
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return bool(data.get("name") and isinstance(data.get("members"), list))


def collect_removals(
    claude_home: Path,
    remove_teams: set[str],
    keep_teams: set[str],
    stale_only: bool,
) -> list[Removal]:
    teams_dir = claude_home / "teams"
    tasks_dir = claude_home / "tasks"
    existing_teams = load_team_names(teams_dir)
    removals: list[Removal] = []

    if teams_dir.exists():
        for team_dir in sorted(p for p in teams_dir.iterdir() if p.is_dir()):
            name = team_dir.name
            if name in keep_teams:
                continue
            if name in remove_teams:
                removals.append(Removal(team_dir, "explicit team removal"))
                continue
            if stale_only and not team_has_config(team_dir):
                removals.append(Removal(team_dir, "stale team metadata without config.json"))

    if tasks_dir.exists():
        for task_dir in sorted(p for p in tasks_dir.iterdir() if p.is_dir()):
            name = task_dir.name
            if name in keep_teams:
                continue
            if name in remove_teams:
                removals.append(Removal(task_dir, "explicit task removal"))
                continue
            if stale_only and name not in existing_teams:
                removals.append(Removal(task_dir, "orphan task metadata without matching team"))

    return removals


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Remove stale Claude AgentTeam metadata after shutdown_request + TeamDelete. "
            "This does not kill in-process agents; it only removes leftover team/task "
            "directories that keep old panels visible."
        )
    )
    parser.add_argument("--claude-home", default=str(Path.home() / ".claude"))
    parser.add_argument("--remove-team", action="append", default=[], help="Exact team name to remove")
    parser.add_argument("--keep-team", action="append", default=[], help="Exact team name to keep")
    parser.add_argument("--stale-only", action="store_true", help="Remove broken/orphan metadata only")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true", help="Actually delete matched metadata")
    args = parser.parse_args()

    if not args.dry_run and not args.yes:
        parser.error("refusing to delete metadata without --yes or --dry-run")

    if not args.stale_only and not args.remove_team:
        parser.error("pass --stale-only and/or at least one --remove-team")

    claude_home = Path(args.claude_home).expanduser()
    removals = collect_removals(
        claude_home=claude_home,
        remove_teams=set(args.remove_team),
        keep_teams=set(args.keep_team),
        stale_only=args.stale_only,
    )

    if not removals:
        print("No AgentTeam metadata matched cleanup criteria.")
        return 0

    for item in removals:
        print(f"{'DRY-RUN remove' if args.dry_run else 'remove'}: {item.path} ({item.reason})")
        if args.yes:
            shutil.rmtree(item.path, ignore_errors=True)

    if args.yes:
        leftovers = [item.path for item in removals if item.path.exists()]
        if leftovers:
            print("ERROR: metadata still exists after cleanup:", file=__import__("sys").stderr)
            for path in leftovers:
                print(f"  {path}", file=__import__("sys").stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
