# <Project>

<!-- Shared project rules: use as CLAUDE.md, AGENTS.md, or one source with a symlink. Fill the <…> slots and delete what does not apply. -->

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
| Current task progress | Beads: status and current notes |
| Blockers and task dependencies | Beads: deps and decision beads |
| Findings during investigation | Beads first: notes, surprise beads |
| Short-lived agent context | `bd remember`, tidied at each grill |
| Discoveries worth keeping | Promoted into the docs above, in the PR that found them |
| Agent behavioural instructions | This file |

- Beads owns live execution status. Keep design plans and roadmaps in docs and link them; do not duplicate bead status in handover files or plan tables.
- Assume the installed skills and tracker are available. Setup is a separate task, not a repeated phase of every plan.
- Nothing durable lives only in chat or in memory.
- A section folder exists only once it has a real page.

## Language

- Use the terms in `docs/domain/glossary.md` in code, tests, beads and PRs.
- Reuse established domain meanings and record missing glossary entries. Ask when ambiguity changes behavior; ordinary internal names are the agent's choice.
- Link an existing objective when relevant. Authorized maintenance need not wait for a new objective.

## Work (beadwork plugin)

- Verify before every PR: `<command>`.
- Delivery: `BEADWORK_DELIVERY=<auto | pr | stack | local>`; default `auto` (agent chooses mechanics). This selects mechanics, not permission to push or merge. Existing authorization: <what may be pushed/integrated, by whom>.
- Review size: target ~<400> hand-written lines per PR; split at useful seams. Mark a hard cap explicitly if this project needs one. Delivery evidence includes `Bead: <id>` and `Docs impact:`.
- must-ask here: changes to approved intent, protected boundaries or external actions without authorization, plus <project categories>. Existing authorization counts. Reversible preferences within delegated authority may proceed on a recorded default.
- Agents may re-cut approved work while preserving every acceptance criterion, and make necessary adjacent fixes outside expected paths. Explain and verify scope expansions; unrelated work stays separate.
- Protected paths/actions: <explicit boundaries; expected role paths are advisory>.
- Beads close after verified integration: PRs through `close-merged.sh`; local delivery by <owner>. Epic closure: <delegated after evidenced criteria and required sign-offs | operator>.
- Delegation: <implementation and review allowed | project restriction>. One bead owner integrates results and maintains evidence; isolate independent writes and serialize mutations of shared resources.
- Roles are optional queue filters. Several Claude/Codex workers may share a role, with distinct actors and isolated checkouts. Add a card in `.beads/roles/<role>.md` only for useful project context or explicit protections (legacy `.claude/roles/` also works).
- Availability: `BEADWORK_MODE=attended` or `unattended`; current operator instructions take precedence. Agents choose conversation boundaries in either mode and retain durable progress in Beads.
