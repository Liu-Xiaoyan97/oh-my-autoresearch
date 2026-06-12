# Synchronization

Synchronization is intentionally conservative. Runtime repositories contain
state and evidence, so workflow updates must never overwrite initialized
runtime files.

## Source of Truth

- `oh-my-autoresearch` owns templates, schemas, prompts, docs, and scripts.
- `research-runtime/runtime` owns objective, state, history, knowledge, debates,
  and experiment records after initialization.
- `manifests/nn_architecture.yaml` is the copy contract between them.

## Install

Use `scripts/install_runtime.py` when creating a new runtime repository.

```bash
python scripts/install_runtime.py --root /path/to/research-runtime
```

The installer:

- creates required runtime directories;
- copies template files only when the destination is missing;
- preserves existing runtime-owned files;
- validates the resulting runtime contract.

Use `--dry-run` to inspect planned actions before writing files.

## Sync

Use `scripts/sync_runtime.py` after the workflow template gains new required
runtime paths.

```bash
python scripts/sync_runtime.py --root /path/to/research-runtime
```

The synchronizer is repair-oriented. It restores missing directories and
missing template files, but it does not update or replace existing runtime
state.

## Never Overwrite

The workflow must not overwrite these initialized runtime paths:

- `runtime/objective/objective.yaml`
- `runtime/state/state.json`
- `runtime/state/current_iteration.json`
- `runtime/state/val_loss.json`
- `runtime/history/timeline.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`
- `runtime/debates/`
- `runtime/experiments/`

If a future template change requires migration of an existing runtime file, add
an explicit migration script with validation instead of changing sync behavior.
