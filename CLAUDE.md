# claude-shared-skills

A shared skill marketplace for Claude Code and Codex. Both hosts load the same skill files; host metadata and runtime adapters live alongside them. Discoverable skills add descriptions to enabled sessions, so this repo stays small. AGENTS.md links to this file to keep one source of repository instructions.

## Rules for skills

- Add a skill only when at least two projects need it. A procedure that only one project uses stays in that project.
- Default operator procedures to `disable-model-invocation: true` and matching Codex `allow_implicit_invocation: false`: the operator runs it, and it costs no context until then. A skill is model-invocable only when an agent must find it mid-task. Keep its description to two sentences.
- Long or rarely needed procedure goes in a file next to SKILL.md, linked from it, not inline.
- No project names, hosts or credentials in skills. Projects configure through `BEADWORK_*` env vars and their own AGENTS.md/CLAUDE.md.
- A plugin is only for projects that want all of it. Split a plugin rather than make projects carry skills they don't use.

## Checks before a commit

- `claude plugin validate .` and `claude plugin validate plugins/<name>` pass.
- `python3 plugins/docs/scripts/docs.py check` passes.
- Keep portable `plugin.json` identity/version in sync with `.claude-plugin/plugin.json`, and invocation policy in sync across host metadata.
- Bump `version` in both manifests of a changed plugin. The agent boxes auto-update only when a plugin's version changes, so a change without a bump never reaches them.
- A change to `hooks/session-start.sh` is run by hand in a repo with `.beads/`, both with and without memories.
- Run `python3 -m unittest discover -s plugins/beadwork/scripts/tests -v` for runtime changes and `python3 -m unittest discover -s scripts/tests -v` for packaging changes.

## Where knowledge goes

| Knowledge | Home |
|---|---|
| Why a skill is shaped the way it is | Git: `docs/decisions/` (the `adr` skill) |
| Work in progress, blockers, findings | Beads (prefix `skills`) |
| Short-lived agent context | `bd remember` |
| Agent instructions | This file |
