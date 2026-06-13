# loop

Run the AutoResearch loop continuously in this session until `BLOCKED` or `DONE`.

Steps:

1. Read `CLAUDE.md`.
2. Read `runtime/state/state.json`.
3. Run:

   ```bash
   cd /Users/liuxiaoyan/workspace/research-runtime
   ./scripts/run_loop.sh
   ```

4. If the workflow is in phase `A`, `B`, `C`, `D`, `E`, or `F` with
   `workflow_status=running`, stay in `/Users/liuxiaoyan/workspace/research-runtime`
   and run `./scripts/run_loop.sh` again. Do not stop between phases or between
   iterations.
5. Stop only when `runtime/state/state.json` reaches `BLOCKED` or `DONE`, or when
   a command fails and the workflow cannot recover.

Context is kept bounded by Claude Code **auto-compact** — make sure it is enabled
in `/config`. Claude cannot run `/compact` itself; auto-compact is what prevents
context overflow during a long continuous run. Because `runtime/` is the source
of truth, an auto-compaction mid-loop is safe — re-read runtime/state and
continue.

For fully unattended operation with a clean context per iteration, run
`./scripts/loop_forever.sh` from a terminal instead: it sets
`AUTORESEARCH_STOP_AT_A=1` and starts a fresh `claude` process for each
iteration (no `/compact` needed).

Do not ask the user before advancing from one successful phase to the next.
