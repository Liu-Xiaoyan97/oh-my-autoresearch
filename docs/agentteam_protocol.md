# Agents Protocol

AgentTeam is the research reasoning layer of AutoResearch. It may propose,
critique, deduplicate, debate, synthesize, and evaluate experiment evidence. It
must not directly modify target model code.

## Active Roles

The active project agents are defined in `agents/` and installed into
`.claude/agents/`:

- `team-leader`
- `math-theorist`
- `numerical-debugger`
- `flow-arch-reviewer`
- `orthogonal-direction-scout`

The team-level coordinator lives in `agents/team-leader.md`.

## Communication Protocol

### Message Format

All specialists (`math-theorist`, `numerical-debugger`, `flow-arch-reviewer`,
`orthogonal-direction-scout`) MUST use the following format when sending their
full conclusions to `team-leader` via `SendMessage`:

```
[CONCLUSION] <agent-name>

<full analysis content>
```

The first line MUST be `[CONCLUSION] <agent-name>` (e.g. `[CONCLUSION] math-theorist`).
Messages without this marker will be ignored by `team-leader` and will NOT count
as a received conclusion.

### Cron-Based Polling

- **`team-leader`** creates a 60-second recurring cron (`*/1 * * * *`) via
  `CronCreate` on startup. When the cron fires, it checks which required
  specialists are still missing, and sends a brief reminder via `SendMessage`
  ONLY to missing specialists. Reminders are sent through the cron trigger only
  — NOT on every message receipt.
- The orchestrator does NOT create a default recurring monitor cron in
  in-process mode. It waits for `team-leader` to send `[TEAM_COMPLETE]`, then
  performs teardown synchronously and runs the included `NEXT_COMMAND`.
- All `team-leader` polling cron jobs MUST be cancelled (`CronDelete`) before
  `[TEAM_COMPLETE]` is sent.

### Team Uniqueness

Only ONE team may exist per phase step. The orchestrator MUST verify no active
team exists before creating a new one. After receiving `[TEAM_COMPLETE]`, the
orchestrator MUST send `shutdown_request` to every member from
`~/.claude/teams/<team>/config.json` (including `team-leader`), ping-confirm exit,
call `TeamDelete`, and verify `~/.claude/teams/<team>/` plus
`~/.claude/tasks/<team>/` are gone before advancing. In in-process mode, any
remaining metadata directory keeps the old agent visible in the CLI panel, so
the final fallback is:

```bash
./scripts/cleanup_agentteam_metadata.py --yes --remove-team <team> --stale-only
```

Also run `./scripts/cleanup_agentteam_metadata.py --yes --stale-only` before
creating the next team. If the CLI panel still shows old in-process sessions
after metadata cleanup, those sessions are still alive in the current Claude
process; send `shutdown_request` to the visible old members and wait for them to
disappear, or restart Claude CLI before continuing.

### Completion Signal

`team-leader` signals completion by sending a structured message via
`SendMessage` to the orchestrator. The first line MUST be `[TEAM_COMPLETE]`:

```text
[TEAM_COMPLETE]
TEAM_NAME: <team_name>
PHASE_STEP: <B1|B2|B3|F1>
RELEASE_SESSIONS: true
TEARDOWN_REQUIRED: Send shutdown_request to every member, ping-confirm exit, TeamDelete, and remove stale team/task metadata if still present.
NEXT_COMMAND: <command-or-next-team-action>
```

This is the ONLY signal the orchestrator uses to determine readiness to advance.
The orchestrator must run `NEXT_COMMAND` only after teardown has removed the
team from the CLI panel/session list.

## Phase Ownership

| Phase step | Agents | Required result |
|---|---|---|
| `B1` | `team-leader`, `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` | Candidate directions with theory, numerical, and architecture-risk notes. |
| `B2` | `team-leader`, `orthogonal-direction-scout` | Historical-overlap review and deduplicated candidate list. |
| `B3` | `team-leader`, `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` | Final debate and one concrete Phase C modification plan. |
| `F1` | `team-leader`, `math-theorist`, `numerical-debugger`, `flow-arch-reviewer` | Root-cause review and learned/rejected/inconclusive verdict. |

## Phase B Protocol

### B1: Candidate Generation and First Review

Inputs:

- `runtime/objective/objective.yaml`
- `runtime/state/val_loss.json`
- `runtime/experiments/best.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`
- `runtime/history/timeline.json`

Responsibilities:

- `team-leader` coordinates the B1 discussion, confirms each role contributed,
  reconciles disagreements, and checks the output shape before the workflow
  advances.
- `math-theorist` checks mathematical validity and hidden assumptions.
- `numerical-debugger` checks empirical plausibility, diagnostic needs, and
  numerical failure modes.
- `flow-arch-reviewer` synthesizes trade-offs and proposes prioritized
  architecture-level directions.

Required B1 output:

- 3-5 candidate directions;
- known assumptions and risks for each candidate;
- minimum evidence required before implementation;
- initial recommendation ranking.

### B2: Orthogonality Review

`team-leader` and `orthogonal-direction-scout` review B1 candidates against the
runtime record.

Required checks:

- overlap with prior validation-loss records;
- overlap with timeline events;
- overlap with learned patterns;
- overlap with rejected ideas;
- overlap with prior debate records when relevant;
- whether the candidate is genuinely new or merely a renamed variation.

Required B2 output:

- accepted candidates;
- rejected duplicates or near-duplicates;
- orthogonality rationale for each accepted candidate;
- missing evidence that would block a confident review.

Candidates rejected in B2 must not reach B3 unless the workflow records an
explicit override reason in the debate log.

### B3: Final Debate and Plan Selection

`team-leader`, `math-theorist`, `numerical-debugger`, and
`flow-arch-reviewer` review the B2 result and select one implementation plan.

Required B3 output:

- selected direction;
- modification plan for Phase C;
- expected validation signal;
- theoretical risk assessment;
- numerical diagnostic checklist;
- implementation cost;
- conditions that should move the workflow to `BLOCKED`.

Write the full B1/B2/B3 debate to:

```text
runtime/debates/<exp_name>.md
```

Write structured summaries to:

```text
runtime/state/current_iteration.json
```

## Phase F Protocol

### F1: Evidence Review and Root-Cause Analysis

After Phase E writes experiment results, the F1 team evaluates what happened.

Inputs:

- `runtime/state/current_iteration.json`
- `runtime/state/val_loss.json`
- `runtime/experiments/<exp_name>.json`
- `runtime/experiments/best.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`

Responsibilities:

- `team-leader` coordinates the F1 review, reconciles votes, and confirms
  `agentteam.f1_evidence_review` and `root_cause_analysis` are schema-complete.
- `math-theorist` evaluates whether the result supports or contradicts the
  original theoretical hypothesis.
- `numerical-debugger` checks whether observed metrics are trustworthy or
  contaminated by implementation, solver, data, or logging issues.
- `flow-arch-reviewer` synthesizes the verdict and decides whether the lesson is
  actionable.

Required F1 output:

- root-cause summary;
- per-agent vote;
- verdict: `learned`, `rejected`, or `inconclusive`;
- update for learned or rejected knowledge;
- missing evidence if inconclusive.

Append the final knowledge update to exactly one of:

```text
runtime/knowledge/learned_patterns.md
runtime/knowledge/rejected_ideas.md
```

If the verdict is `inconclusive`, append a timeline event but do not force the
method into learned or rejected knowledge.

## Runtime Write Locations

AgentTeam may write only through the workflow into these runtime files:

- `runtime/debates/<exp_name>.md`
- `runtime/state/current_iteration.json`
- `runtime/history/timeline.json`
- `runtime/knowledge/learned_patterns.md`
- `runtime/knowledge/rejected_ideas.md`

AgentTeam must not overwrite:

- existing debate logs;
- experiment records;
- objective files;
- target model source code.

## Guardrails

- Runtime files are the source of truth, not chat history.
- AgentTeam recommendations must cite the evidence files they used.
- Missing evidence should produce `BLOCKED` or `inconclusive`, not invented
  certainty.
- Phase C implementation is performed by the coding executor, not by AgentTeam.
