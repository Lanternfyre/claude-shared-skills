# Epics

An epic holds one outcome that takes several beads. Agents never claim an epic (the work loop excludes them). Its children are ordinary beads, created with `--parent <epic>`.

## When to make one

- A milestone; or
- three or more beads that share one outcome a person could check at the end.

Fewer beads with no shared outcome need no epic: link them with deps instead.

## Sections and labels

- `## Goal`: the outcome, in plain words.
- `## Scope`: what is in, what is out, and any decisions that shaped it.
- `## Success Criteria`: the exit table. Each criterion is checkable, and each will need evidence before closing.
- `## Tripwires`: the observations that stop the epic, each with the action it triggers.

Labels: `milestone:<name>` when it is a milestone, `objective:OBJ-n` for the objective it serves, plus a `topic:`.

Cut the epic into beads with [cutting.md](cutting.md).

## When a tripwire fires

1. `bd update <epic> --status blocked --append-notes "tripwire: <which>, <evidence>"`.
2. File a must-ask decision bead (the `question` skill) with `--deps discovered-from:<epic>`. It asks what happens next.
3. Children already in progress finish or park. Nothing new from the epic is claimed until the operator answers.

## Closing

**Only the operator closes an epic,** and only after each Success Criterion has evidence: a PR, a CI run, a measurement, or a note of the operator's own check. Record the evidence first: `bd note <epic> "<criterion>: <evidence>"` for each one.

`bd epic close-eligible` closes an epic as soon as its children are done, without looking at the Success Criteria. Agents run it only as `bd epic close-eligible --dry-run`, to list candidates for the operator. The grill or review digest can show that list. A run on 2026-10-25, with every epic still having open children, printed `No epics eligible for closure`.

`bd epic status` shows each epic's progress (children closed out of total). Children being closed is a reason to check the Success Criteria; it is not the check.
