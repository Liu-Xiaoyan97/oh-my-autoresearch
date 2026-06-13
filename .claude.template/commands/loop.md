# loop

Run ONE AutoResearch iteration (Phase A..F), then stop at the Phase A boundary
so the context can be compacted before the next iteration.

Steps:

1. Read `CLAUDE.md`.
2. Read `runtime/state/state.json`.
3. Run:

   ```bash
   cd /Users/liuxiaoyan/workspace/research-runtime
   ./scripts/run_loop.sh
   ```

4. If the workflow is in phase `B`, `C`, `D`, `E`, or `F` with
   `workflow_status=running`, stay in `/Users/liuxiaoyan/workspace/research-runtime`
   and run `./scripts/run_loop.sh` again. Do not stop mid-iteration.
5. Stop when the workflow returns to the **Phase A boundary** (Phase F completed,
   one full iteration done), or when it reaches `BLOCKED` / `DONE`, or when a
   command fails and the workflow cannot recover.

At the Phase A boundary, run `/compact` and then `/loop` to start the next
iteration with a clean context. (Claude cannot run `/compact` itself, and
auto-compact does not fire during the hook-forced run — that is why the loop
stops here for you to compact.)

For fully unattended operation, run `./scripts/loop_forever.sh` from a terminal
instead: it starts a fresh `claude` process per iteration (no `/compact`
needed). To run the whole loop in one continuous session without stopping at the
boundary, set `AUTORESEARCH_CONTINUOUS=1` (relies on auto-compact).

Do not ask the user before advancing from one successful phase to the next
within an iteration.
