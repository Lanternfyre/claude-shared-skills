---
name: grill
description: Operator interview. Gather every open question and night summary from Beads, ask them as one auq batch in plain language, record the answers, file the follow-ups and tidy short-lived memories.
disable-model-invocation: true
---

# Grill

Runs in an operator session. The goal is one sitting and one card, with every open decision answered or consciously deferred.

## 1. Collect

```bash
bd --readonly human list --json     # open beads labelled human: decisions and night summaries
bd --readonly blocked --json        # which of them hold work back
```
- Run `bd show <id>` on each: its sections, its labels (`level:`, `provisional`, `must-ask`/`default-ok`) and its metadata.
- A question already posted (it has `auq_question_id`) is still live. **Never re-post it.** Add its ids to the await list instead.
- A card stored in metadata (`auq_card`) was held overnight. Post it in this batch.
- Read the night summaries. They feed the `context` of the first question; they are not questions.

For each question, read what already bears on it: ADRs, the glossary, objectives and the code. The agent that filed it may have missed a document. A question a document already answers is closed with a pointer (`bd human respond <id> -r "answered by …"`), not asked.

Order the questions: first those that block work, then the rest, grouped by `topic:`.

## 2. Write

Follow the `question` skill's card rules (§4) for every question, including the resolution check. A question answered on a provisional default needs three more things: what was assumed, what has been built on it since, and what changes if it is overturned.

Make one `ask_user_questions` call with `requester_name: "grill"`, then store each bead's ids:
`bd update <id> --set-metadata auq_question_id=… --set-metadata auq_thread_id=…`

## 3. Wait

Blocking is normal. If the call returns `pending`, run `auq await <ids>` in the background and end the turn; the answers resume the work.

## 4. Record

For each answer:
- **An option was chosen:** `bd human respond <id> -r "<option id>: <label>"`. This closes the bead and unblocks the work.
- **"Go one level deeper":** ask again one level up, in the same thread (`parent_question_id`), and update the `level:` label.
- **"Other", or free text:** record it. If it doesn't settle the question, follow up in the same thread.
- **A provisional default was overturned:** file a fix bead (the `bead` skill) with `--deps discovered-from:<id>`.
- **Make it durable**, now or as a chore bead:
  - architecture → an ADR (the `adr` skill);
  - domain rule → `docs/domain/`;
  - term → `docs/domain/glossary.md`;
  - requirement or objective → `docs/requirements/`.
- **Night summaries the operator has read:** `bd close <id> --reason "read in grill"`.

## 5. Memory hygiene

Run `bd memories`. For each memory:
- still needed and short-lived: keep it;
- durable: promote it to the right doc, then `bd forget <key>`;
- stale: `bd forget <key>`.

## 6. Report

Lead with a one-line verdict. Then give one short list: answered, deferred, follow-up beads filed, and what is now ready (`bd ready`). If the operator must still act on something, end with a `What I need from you` list; leave it out when there is nothing.
