---
name: bead
description: Write, split or review a Beads work item (task, bug, chore, spike, epic) so an agent with none of your context can finish it. Use before any `bd create` of work, when a bead turns out too big or wrongly cut, and when cutting a plan or epic into beads.
---

# Writing a bead

A bead is a contract with an agent that has none of your context. If it cannot be finished from its text and the docs it links, it is not ready.

## Sections

`bd create --validate` refuses a bead without them (the lint config comes from `scripts/configure-beads.sh`).

```markdown
## Task
What and why, in plain words and the project's glossary terms. One outcome.
Never how: the approach belongs to whoever builds it. If it matters, link the ADR that decided it.
Links: the requirement, objective (OBJ-n), ADR or spec it implements.

## Guardrails
- Scope fence: the paths or areas it may touch; what must not change.
- Banned approaches, and any project rule that applies.
- Size: expected PR count and hand-written lines, under the project's cap.

## Acceptance Criteria
Machine-checkable only: a named test or command and its expected result, a gate
that goes green, a benchmark scenario if a hot path changes, a demo if a user sees it.

## Evidence
Empty at creation. Filled at close: PRs, CI runs, demo, benchmark deltas.
```

"Works", "clean", "robust" and "well tested" are not acceptance criteria.

Per type:
- **bug:** add `## Steps to Reproduce` as a Given/When/Then scenario that fails today.
- **spike:** add `## Variants` (2–3) and `## Measurements` (identical for every variant). Results go in the notes.
- **epic:** `## Goal`, `## Scope`, `## Success Criteria` (the exit table) and `## Tripwires` (what stops the epic). When to make one, labels, tripwires and closing: [epic.md](epic.md).
- **decision:** use the `question` skill.

## Size

One bead is one checkable outcome, with PRs small enough to review. It may take several sessions, because the progress record carries it across, and several PRs stacked on each other. Split only when the outcome itself splits, at seams where each child can be verified on its own. Make the parent an epic (`--parent`) or chain the children with deps. Never split into "write the code" and "write the tests".

**Re-cut instead of forcing.** If a bead turns out too big, wrongly cut, or built on a wrong assumption, don't push it through. Propose the re-cut through the `question` skill: the new beads with their outcomes, and what this bead keeps. The default is to file the new beads with `--deps discovered-from:<id>` and carry on with what this bead keeps. Never weaken a bead's Acceptance Criteria yourself. Moving a criterion to a new bead is part of the proposal.

To cut a whole plan, epic or milestone into beads, follow [cutting.md](cutting.md).

## Links and labels

- `--deps blocked-by:<id>` only for real ordering. `discovered-from:<id>` for work found while doing another bead.
- Labels: `role:<role>` (who may claim it), `topic:<area>`, plus the project's own (milestone, objective).
- Priority 0–4, default 2. Defer what isn't needed yet (`--defer`), so `bd ready` stays honest.

## Create

```bash
bd create --title "Reject expired refresh tokens" -t task -l role:impl,topic:auth \
  --deps blocked-by:proj-a1b --body-file bead.md --validate --silent
```

## Example

Bad: *"Fix login"*, with acceptance *"login works"*.

Bad Task, because it says how: *"Add `if (token.ExpiresAt < now) throw` to `RefreshHandler` before it issues the token."* The builder may find a better place, such as the validator every token already passes through.

Good: *"Reject expired refresh tokens"*.
- **Task:** a refresh token past its expiry still issues an access token. It must be refused (OBJ-2: no session outlives logout).
- **Guardrails:** only `auth/token/*`. No schema change. One PR, under 150 lines.
- **Acceptance Criteria:** `RefreshTokenTests.Expired_token_is_rejected` is green and was red before the fix. `verify.sh fast` is green.
