---
name: objectives
description: Capture business objectives in docs/requirements/objectives.md as measurable outcomes written in glossary terms and agreed with the operator, so every requirement, epic and bead can say which objective it serves.
argument-hint: "[source docs or notes]"
disable-model-invocation: true
---

# Business objectives

An objective is an outcome for someone, with a measure. It is not a feature. Agents use objectives to judge trade-offs ("which option serves OBJ-2 better?") and to turn down scope that serves none of them.

## Format (`docs/requirements/objectives.md`)

```markdown
## OBJ-2 No session outlives logout
- **Outcome:** a player who logs out cannot act again from any device until they log in.
- **Measure:** 0 actions accepted after logout in the session-replay suite.
- **Why:** 14 account-theft reports in Q3 came from stale sessions.
- **Non-goals:** single sign-on; a device-management UI.
- **Constraints:** → docs/architecture/auth.md
- **Status:** proposed | committed | met | dropped
```

Ids are stable and never reused. Write in the glossary's terms; a term it lacks becomes a glossary candidate.

## 1. Gather

Sources:
- the files or notes in `$ARGUMENTS`;
- `docs/requirements/`, the README and any plans;
- epics: `bd list -t epic --all --json`.

Collect the stated goals and the implied ones (why does this epic exist?). Separate constraints (they go to `docs/architecture/`) and domain rules (`docs/domain/`).

## 2. Draft

- Rewrite each goal as an Outcome plus a Measure.
- When a goal is really a feature, ask "so that what?" until you reach an outcome.
- Merge duplicates.
- A goal you can't measure stays `proposed`, with the open question noted.

## 3. Ask in one batch

Use auq `ask_user_questions`, or AskUserQuestion when the operator is in this session.
- **For each draft:** `single_select` with "As written ★", "Reword", "Not an objective" and "Go one level deeper". The `context` says where the draft came from.
- **Priority** (`ranked`), when there are more than three objectives.
- **Measures** (`form`: metric, threshold, by when), where they are unclear.
- **Non-goals** (`multi_select`).

Write in business language, with no file paths in the visible text.

## 4. Write and link

- Write the file. Only what the operator confirmed is `committed`.
- When the project uses Beads, label each epic `objective:OBJ-n`. List the epics that serve no objective for the operator: either drop them, or there is a missing objective.
- New terms go to `/domain:glossary`.
