---
name: adr
description: Write, supersede, review or audit an architecture decision record in docs/decisions/. Use whenever an architectural decision is settled or reversed, and to check whether one is worth recording at all.
argument-hint: "[new <title> | supersede <id> | review <id> | audit]"
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/docs.py *)
---

# Architecture decision records

Use the [host runtime guide](../../runtime.md) for invocation, helper paths and startup context.

`docs.py` mints ids, rebuilds the decision index (`docs/decisions/README.md`) and checks the docs. For pre-commit and CI, copy it into the repo (for example `tools/docs.py`) and run `docs.py check`.

```bash
python3 "<plugin-root>/scripts/docs.py" adr "<title>"   # ADR-YYYYMMDD-HHMMSS-xxxx-<slug>.md, status Proposed
python3 "<plugin-root>/scripts/docs.py" index
python3 "<plugin-root>/scripts/docs.py" check
```

The page's heading is the decision's title; the id lives in the header block and the index. A consequential design proposal can be an ADR with status Proposed. Preserve an established proposal process; do not create a second document solely to satisfy this skill.

## Is it an ADR?

Write one only when all three are true. Otherwise it belongs somewhere else.
1. **Hard to reverse:** changing your mind later costs real work.
2. **Surprising without context:** a future reader would ask "why on earth this way?"
3. **A real trade-off:** there were genuine alternatives, and one was picked for stated reasons.

Where the rest goes:
- domain rules and values → `docs/domain/`;
- technical constraints → `docs/architecture/`;
- what a bead decided for itself → its PR.

**An ADR records the decision and links its evidence.** Include enough context to understand the trade-off; avoid copying detailed facts maintained elsewhere.

## Header and sections

`docs.py adr` writes the header. Keep it accurate: `status` is Proposed, Accepted, Superseded or Deprecated. Record `supersedes`/`superseded_by` and `amends`/`amended_by` on both ADRs. `refs` lists the ADRs this one depends on.

- **Context:** the forces at play and the constraints. It may quote the operator's own words.
- **Decision:** what is decided, with concrete values, in "we will" form. Each point is one of:
  - **decided:** a value and the reason for it;
  - **open:** listed under `### Open questions`, with a decision bead;
  - **deferred:** a bead id and the trigger that reopens it.

  No "probably", "should", "for now", "TBD" or placeholders.
- **Consequences:** both the positives and the negatives, given equal treatment. Include what becomes harder.
- **Alternatives considered:** each option rejected for a real reason ("no support for X", not "less clean"), and what choosing it would have ruled out.
- **What would prove this wrong:** the observation that should trigger a review.

Keep an ADR short: one decision per ADR, and no tutorials on the technology.

## new

1. Apply the three-part test. Read the ADRs, glossary and objectives the decision touches.
2. Check the decision authority. Record an existing operator decision or one made under explicit delegation without asking again. Otherwise draft the recommendation as Proposed and ask through the available decision channel; do not present it as accepted.
3. Run `docs.py adr`, fill in the sections, then `docs.py index` and `docs.py check`. Commit the ADR together with the regenerated index.
4. Status is `Accepted` only with operator approval or explicit delegated authority. Record the source of that authority in Context.

## supersede

**Once an ADR is Accepted, its Decision is frozen.** Never append an "Update" section that reverses it. That was the commonest defect in v1: a reader working top-down implemented the dead design.

1. Write the new ADR, with `supersedes: [<old>]`.
2. In the old ADR, set `status: Superseded` and `superseded_by: <new>`. Leave its text alone.
3. Run `docs.py index` and `docs.py check`.

An `amends` ADR may only add or clarify. Anything that changes the outcome is a supersede. Fixing typos and wording in place is fine.

## review

Does `<id>` still describe reality?
- Check the code for every type, flow or value it names.
- Report what still holds, and what has drifted, with file:line.
- Recommend one of: keep, deprecate, or supersede. A supersede goes through `new`.

## audit

Read the whole corpus and report findings by severity:
- **ambiguity:** hedged decisions, and "Accepted" ADRs whose text says pending;
- **contradiction:** two ADRs deciding the same thing differently;
- **status integrity:** what `docs.py check` reports, plus reversals hidden in update sections;
- **reachability:** ADRs nothing links to.

Each finding becomes a bead, or a `supersede`.
