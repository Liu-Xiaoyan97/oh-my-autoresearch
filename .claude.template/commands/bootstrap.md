# bootstrap

Bootstrap or repair the runtime workspace from `oh-my-autoresearch`.

Run:

```bash
./scripts/sync_from_workflow.sh
./scripts/validate_runtime.sh
./scripts/validate_schema.sh
```

Do not overwrite initialized runtime state manually. The sync/install scripts
copy missing files from the workflow manifest and preserve runtime-owned state.
