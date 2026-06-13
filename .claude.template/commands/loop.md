# loop

Run the AutoResearch loop continuously.

Steps:

1. Read `CLAUDE.md`.
2. Read `runtime/state/state.json`.
3. Run:

   ```bash
   ./scripts/run_loop.sh
   ```

4. If the workflow is still in phase `A`, `B`, `C`, `D`, `E`, or `F` with
   `workflow_status=running`, run `./scripts/run_loop.sh` again.
5. Stop only when `runtime/state/state.json` reaches `BLOCKED` or `DONE`, or
   when a command fails and the workflow itself cannot recover.

Do not ask the user before advancing from one successful phase to the next.
