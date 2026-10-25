# claude-shared-skills

A Claude Code plugin marketplace of skills shared across our projects. Every model-invocable skill puts its description into every session of every project that enables its plugin, so this repo stays small.

## Rules for skills

- Add a skill only when at least two projects need it. A procedure that only one project uses stays in that project.
- Default to `disable-model-invocation: true`: the operator runs it, and it costs no context until then. A skill is model-invocable only when an agent must find it mid-task. Keep its description to two sentences.
- Long or rarely needed procedure goes in a file next to SKILL.md, linked from it, not inline.
- No project names, hosts or credentials in skills. Projects configure through `BEADWORK_*` env vars and their own CLAUDE.md.
- A plugin is only for projects that want all of it. Split a plugin rather than make projects carry skills they don't use.

## Checks before a commit

- `claude plugin validate .` and `claude plugin validate plugins/<name>` pass.
- Bump `version` in the changed plugin's `plugin.json`.
- A change to `hooks/session-start.sh` is run by hand in a repo with `.beads/`, both with and without memories.

## Where knowledge goes

| Knowledge | Home |
|---|---|
| Why a skill is shaped the way it is | Git: `docs/decisions/` (the `adr` skill) |
| Work in progress, blockers, findings | Beads (prefix `skills`) |
| Short-lived agent context | `bd remember` |
| Agent instructions | This file |
