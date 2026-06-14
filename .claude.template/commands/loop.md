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
   and run `./scripts/run_loop.sh` again. Do not stop between phases or
   iterations.
5. Stop only when `runtime/state/state.json` reaches `BLOCKED` or `DONE`, or when
   a command fails and the workflow cannot recover.

Context is bounded automatically by Claude Code **auto-compact**. Its trigger
threshold is configured via `env` in `.claude/settings.json`
(`CLAUDE_CODE_AUTO_COMPACT_WINDOW` + `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`) so it
fires mid-loop instead of at the unusable ~95%-of-1M default. Env changes apply
to NEW sessions only — restart `claude` after editing. Claude cannot run
`/compact` itself; auto-compact (driven by those env vars) is what keeps context
bounded during a long continuous run. A mid-loop compaction is safe — re-read
runtime/state and continue.

For per-iteration fresh contexts, run `./scripts/loop_forever.sh` from a
terminal: it starts a fresh `claude -p` process per session and drives the loop
via its prompt plus an outer progress/stall guard — there is NO Stop hook and no
env coercion. AgentTeam phases advance through the `[TEAM_COMPLETE]` message's
`NEXT_COMMAND` that `team-leader` sends alongside `任务完成，解散团队`.

Do not ask the user before advancing from one successful phase to the next.
