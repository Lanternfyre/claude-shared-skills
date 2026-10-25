# <Project>

<!-- Starter from claude-shared-skills/templates. Fill the <…> slots and delete what doesn't apply. -->

## Where knowledge goes

| Knowledge | Home |
|---|---|
| Business requirements and objectives | Git: `docs/requirements/` (`objectives.md`) |
| Architectural decisions | Git: `docs/adr/` |
| Technical constraints | Git: `docs/architecture/` |
| Domain rules, invariants, glossary | Git: `docs/domain/` (`glossary.md`) |
| Current task progress | Beads: status and `bd note` |
| Blockers and task dependencies | Beads: deps and decision beads |
| Findings during investigation | Beads first (notes, surprise beads) |
| Short-lived agent context | `bd remember`, tidied at each grill |
| Discoveries worth keeping | Promoted into the Git docs above, in the PR that found them |
| Agent behavioural instructions | This file |

- Beads is the only tracker: no TODO files, no plan files in the repo.
- Nothing durable lives only in chat or in memory.

## Language

- Use the terms in `docs/domain/glossary.md` in code, tests, beads and PRs.
- A missing or ambiguous term is a question (`topic:glossary`), not a guess.
- Work serves an objective in `docs/requirements/objectives.md`, and names it (`OBJ-n`).

## Work (beadwork plugin)

- Verify before every PR: `<command>`.
- PR: under ~<400> hand-written lines. The body starts with `Bead: <id>`.
- must-ask questions here: destructive actions, plus <project categories>.
- Beads close on merge by: <the steward | the operator, through /beadwork:review-chunk>.
- Sub-agents for bead work: <no | allowed for …>.
