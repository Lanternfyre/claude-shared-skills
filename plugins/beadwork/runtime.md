# Running beadwork in Claude Code and Codex

Both hosts use the same skills and scripts. Use the host's own shell, question and delegation tools; tool names in examples describe capabilities, not mandatory APIs.

## Invoke and resolve paths

In Claude Code, run `/beadwork:slice`, `/beadwork:grill` or `/beadwork:review-chunk`. In Codex, select the corresponding skill with `$` or `/skills`, or ask for it by name. Operator-run skills keep `disable-model-invocation: true` for Claude and `policy.allow_implicit_invocation: false` in `agents/openai.yaml` for Codex. The `bead` and `question` skills remain discoverable during work.

`<plugin-root>` is the absolute plugin directory containing the loaded `skills/` tree, `scripts/`, `hooks/` and this page. From the skill directory, move up through `skills/` to that plugin directory. Replace that placeholder before running a command; quote paths. Resolve from the actual loaded file, including a plugin cache, rather than guessing a repository checkout or reusing another plugin's environment variable. Run helpers with the project as the working directory. `CLAUDE_PLUGIN_ROOT` or `PLUGIN_ROOT` may be used when the host supplies the matching plugin's value.

Claude supplies `$ARGUMENTS`; in Codex use the arguments in the invocation text. For example, selecting `slice` with `night` means the same mode in either host. A `/beadwork:…` reference in shared text names the procedure; it is not a Codex shell command.

## Start a session

Read project instructions from `AGENTS.md` in Codex and `CLAUDE.md` in Claude Code. Projects can share one source through a symlink when the rules are identical. Host-enforced instructions and permissions keep their precedence.

The SessionStart hook prints Beads context. Codex requires users to review and trust bundled hooks; do not bypass that requirement. If startup context is absent, run `bash "<plugin-root>/hooks/session-start.sh"` explicitly once through the normal shell approval flow. No Beads workspace means the hook prints nothing and changes nothing. A skipped optional hook is not a reason to reinstall the plugin or stop independent work.

Role-card resolution is shared: `BEADWORK_ROLE_CARD`, then `BEADWORK_ROLE_DIR/<role>.md`, then an existing `.beads/roles/<role>.md`, then the legacy `.claude/roles/<role>.md`. Use that selected path wherever the skill says `<role-card>`. At night, an automatic path change cannot replace an existing approved card until the new path is reviewed on the default branch; an explicit operator path override remains available. Expected paths are advisory; explicit protections and project rules still bind.

auq remains optional for attended sessions. Use the host's question tool or chat when it is unavailable and record answers in Beads. Unattended questions stay queued. Delegation depends on the host's available tools; a missing delegation tool is not permission to stop an otherwise feasible task.

## Unattended execution

The same `scripts/night-run.sh` supports `BEADWORK_ENGINE=claude` (default) and `codex`. Each engine uses its own model and effort fields from the role card; see the project's card and the repository's role template. Never translate a Claude model alias or reasoning level into a guessed Codex value.

Codex runs through `codex exec` with workspace-write sandboxing and its existing approval policy. The runner loads the exact slice file, requests night mode, and reads the final result from `--output-last-message`; transcript examples do not count as completed handoffs. It does not install credentials, connect an auq service, grant network access or bypass hook trust. The project must already have the required tools and permissions for its work.
