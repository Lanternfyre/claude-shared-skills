# <Project>

<!-- Starter from claude-shared-skills/templates. Fill the <…> slots and delete what doesn't apply. -->

## Documentation

- Docs are for people: <the operator, engineers joining, people running it, external users>. Agents are tools that write and read them. If something helps agents but makes a page harder for a person, don't do it, or keep it off the page.
- Every page answers one reader's question. Load the `docs:write` skill before creating or substantially changing a page. Standard: claude-shared-skills `docs` <version>.

## Where knowledge goes

| Knowledge | Home |
|---|---|
| What this is, how to start, where things are | `README.md` |
| Vision, objectives, who it is for | `docs/product/` (`objectives.md`) |
| Features and their requirements | `docs/capabilities/` |
| Journeys across components | `docs/flows/` |
| System-wide quality requirements | `docs/requirements/` |
| Architecture, components, constraints | `docs/architecture/` |
| Domain rules, invariants, glossary | `docs/domain/` (`glossary.md`) |
| Architectural decisions | `docs/decisions/` (the `adr` skill) |
| How-tos, runbooks, reference, first-run tutorial | `docs/guides/`, `docs/operate/`, `docs/reference/`, `docs/start/` |
| Roadmap, open questions | `docs/planning/` |
| Current task progress | Beads: status and `bd note` |
| Blockers and task dependencies | Beads: deps and decision beads |
| Findings during investigation | Beads first: notes, surprise beads |
| Short-lived agent context | `bd remember`, tidied at each grill |
| Discoveries worth keeping | Promoted into the docs above, in the PR that found them |
| Agent behavioural instructions | This file |

- Beads is the only tracker: no TODO files, and no plan files in the repo.
- Nothing durable lives only in chat or in memory.
- A section folder exists only once it has a real page.

## Language

- Use the terms in `docs/domain/glossary.md` in code, tests, beads and PRs.
- A missing or ambiguous term is a question (`topic:glossary`), not a guess.
- Work serves an objective in `docs/product/objectives.md`, and names it (`OBJ-n`).

## Work (beadwork plugin)

- Verify before every PR: `<command>`.
- PR: under ~<400> hand-written lines. The body starts with `Bead: <id>` and ends with a `Docs impact:` line.
- must-ask questions here: destructive actions, plus <project categories>.
- Beads close on merge by: <the steward | the operator, through /beadwork:review-chunk>.
- Sub-agents for bead work: <the default, up to three read-only per bead | none | …>.
- Roles: one card per role in `.claude/roles/<role>.md`, from claude-shared-skills' `templates/role.md`.
