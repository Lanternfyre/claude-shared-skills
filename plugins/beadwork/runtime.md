# Running beadwork in Claude Code and Codex

Both hosts use the same skills and scripts. Use the host's own shell, question and delegation tools; tool names in examples describe capabilities, not mandatory APIs.

## Invoke and resolve paths

In Claude Code, run `/beadwork:slice`, `/beadwork:grill` or `/beadwork:review-chunk`. In Codex, select the corresponding skill with `$` or `/skills`, or ask for it by name. Operator-run skills keep `disable-model-invocation: true` for Claude and `policy.allow_implicit_invocation: false` in `agents/openai.yaml` for Codex. The `bead` and `question` skills remain discoverable during work.

`<plugin-root>` is the absolute plugin directory containing the loaded `skills/` tree, `scripts/`, `hooks/` and this page. From the skill directory, move up through `skills/` to that plugin directory. Replace that placeholder before running a command; quote paths. Resolve from the actual loaded file, including a plugin cache, rather than guessing a repository checkout or reusing another plugin's environment variable. Run helpers with the project as the working directory. `CLAUDE_PLUGIN_ROOT` or `PLUGIN_ROOT` may be used when the host supplies the matching plugin's value.

Claude supplies `$ARGUMENTS`; in Codex use the arguments in the invocation text. For example, selecting `slice` with `unattended` queues questions in either host; `night` remains a compatibility alias. A `/beadwork:…` reference in shared text names the procedure; it is not a Codex shell command.

## Start a session

Read project instructions from `AGENTS.md` in Codex and `CLAUDE.md` in Claude Code. Projects can share one source through a symlink when the rules are identical. Host-enforced instructions and permissions keep their precedence.

The SessionStart hook prints Beads context. Codex requires users to review and trust bundled hooks; do not bypass that requirement. If startup context is absent, run `bash "<plugin-root>/hooks/session-start.sh"` explicitly once through the normal shell approval flow. No Beads workspace means the hook prints nothing and changes nothing. A skipped optional hook is not a reason to reinstall the plugin or stop independent work.

Role-card resolution is shared: `BEADWORK_ROLE_CARD`, then `BEADWORK_ROLE_DIR/<role>.md`, then an existing `.beads/roles/<role>.md`, then the legacy `.claude/roles/<role>.md`. Use that selected path wherever the skill says `<role-card>`. Cards are optional context for a routing role. Expected paths are advisory; explicit protections and project rules still bind. Model, effort and availability are launcher settings.

auq remains optional for attended sessions. Use the host's question tool or chat when it is unavailable and record answers in Beads. Unattended questions stay queued. Delegation depends on the host's available tools; a missing delegation tool is not permission to stop an otherwise feasible task.

## Run a worker

Run the shared supervisor from a dedicated project checkout or worktree. It starts the chosen CLI, claims one exact eligible bead at a time, maintains its lease, and lets the agent choose whether the next turn reuses or refreshes the conversation. A second runner in the same checkout is refused. Use distinct worktrees for concurrent writers; a role can be shared by several workers.

```bash
python3 "<plugin-root>/scripts/run.py" --engine claude --role ops --time-budget 2h
python3 "<plugin-root>/scripts/run.py" --engine codex --bead <id> --max-beads 1 --dry-run
python3 "<plugin-root>/scripts/run.py" --engine codex --bead <id> --max-beads 1
```

`--mode attended` is the default. `--mode unattended` queues questions using the same workflow and authority. Use `--label <label>` to narrow an authorized queue. There is no mandatory role, role card, `night-ok` label or separate unattended permission checklist; explicit project restrictions still apply. Choosing an engine is not permission to access a different project's data.

`--model` and `--effort` are optional and otherwise use that host's defaults. Never translate model names or effort levels between engines. `--delivery auto` lets the agent choose PR, stack or local delivery within project conventions; an explicit mode overrides the default for new work. The review cap counts both PR and local handoffs. `--max-beads 0` means no bead-count limit within the fixed time budget; use `1` for a single-bead trial.

Both engines preserve their host approvals and trust. Codex uses the sandbox and approval defaults configured by its host or project; the runner does not override them. Configure Beads, GitHub, the question inbox and plugin installation in the box before running work that needs them. A headless worker cannot answer a missing interactive login or approval for you. The runner does not grant credentials or bypass host policy.

## Conversations and recovery

The runner records the native conversation ID, unique worker actor, current bead, checkout and deadline under the checkout's Git directory in `beadwork/run.json`, with per-turn logs beside it. This is process state; substantive task progress stays in Beads. The [session protocol](skills/slice/sessions.md) describes the small result the agent returns. Conversation refreshes and compaction keep the same worker identity and deadline.

A clean pause resumes using the recorded state. An unclean stop leaves recovery required: inspect the exact bead, notes, diff and logs, establish that old writers and delegates stopped, and reconcile ownership. Then use the runner's `--recover` option. Recovery is evidence-based and does not require a new operator approval for actions already authorized. Never delete the state file to hide an unresolved claim. An expired budget requires explicit `--new-budget` under a newly authorized run budget; ordinary resumption cannot silently extend it.

Run these commands from the same worktree, using the saved engine (`claude` or `codex`). The checkout selects its saved run; do not supply a different bead, role or queue filter.

```bash
# Resume a clean pause with its original conversation and remaining budget.
python3 "<plugin-root>/scripts/run.py" --engine codex
# After inspecting an interrupted run and stopping its writers:
python3 "<plugin-root>/scripts/run.py" --engine codex --recover
# If the saved native conversation is missing or unusable:
python3 "<plugin-root>/scripts/run.py" --engine codex --recover --fresh-session
# Only when a further 30 minutes is authorized:
python3 "<plugin-root>/scripts/run.py" --engine codex --new-budget --time-budget 30m
```

`--fresh-session` is an explicit recovery choice, available with `--recover` or `--new-budget`. It keeps the exact bead, worker identity and recovery checks; it does not extend the deadline. Use it when a CLI failed before creating its saved conversation or that conversation cannot be resumed.

The managed queue selects independently ready beads. It can maintain an explicitly selected review bead, but does not infer that a blocked stack successor's implementation dependencies are satisfied. Use the interactive slice workflow for that continuation until managed selection supports that evidence.

The runner checks recorded ownership, checkpoints and handoff state. It does not independently prove every acceptance criterion or authorize integration. Report a live trial separately from subprocess tests.

## Existing night launchers

`night-run.sh` delegates to the same runner with unattended availability, the legacy `night-ok` queue filter and the configured night window. Existing scripts can keep that entrypoint. New scheduling can launch `run.py` directly for the authorized queue; availability and the schedule are separate settings. The old automatic morning-summary chore is removed: task evidence stays on the affected beads and held questions remain available to `grill morning`.
