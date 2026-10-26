---
name: grill
description: Operator interview. Gather every open question and night summary from Beads, ask them as one auq batch in plain language, record the answers, file the follow-ups and tidy short-lived memories.
argument-hint: "[morning]"
disable-model-invocation: true
---

# Grill

Use the [host runtime guide](../../runtime.md) for invocation, helper paths and startup context.

Runs in an operator session. The goal is one sitting and one card, with every open decision answered or consciously deferred.

Use the available question channel. auq supplies durable cards and ids when installed; an attended grill can use the session's question tool or chat instead, recording answers in Beads without inventing auq ids. Missing auq does not block the discussion. The scheduled morning mode needs an authorized durable inbox; if unavailable, report held questions once and leave them queued.

**If `$ARGUMENTS` is `morning`, follow only "Morning mode" below.**

## Morning mode

The scheduled job runs `/beadwork:grill morning` when the day starts. It posts **one** card and exits without waiting.

1. For PR/stack delivery, run `"<plugin-root>/scripts/close-merged.sh"`; skip it in `BEADWORK_DELIVERY=local`. A sweep failure leaves review state unresolved but does not prevent collecting questions.
2. Collect:
   - **Night summaries:** `bd --readonly list -l morning-summary --status open --json`, keeping those whose `metadata.auq_question_id` is not set. Their `## Summary` sections give the night in a few lines.
   - **Held questions:** `bd --readonly list -t decision --status open --json`, keeping those whose `metadata.auq_card` is set and `metadata.auq_question_id` is not. That metadata is the card the agent wrote at night, as JSON text.
   - **Questions already live in auq** (`auq_question_id` set): never post them again. Count the decision beads among them: posted, not yet recorded.
3. If there is nothing to post, post nothing and go to step 6.
4. Make one `ask_user_questions` call with `requester_name: "morning"` and `block_until_complete: false`. The call still waits up to 90 s; a `pending` result is normal here and means nothing more to do. Never wait further, and never post again:
   - **The night comes first:** a `single_select` "Night summary", with the summaries as plain prose in `context` and the options "Read" and "Something looks wrong". The bead ids go in `agent_notes`.
   - **Then each held card, as stored:** first the cards whose decision blocks work (it appears in some bead's `blocked_by` in `bd --readonly blocked --json`), then the rest, grouped by `topic:`.
5. Store the ids at once, because the post is the only copy: on each decision bead and each summary bead, `bd update <id> --set-metadata auq_question_id=<its question id> --set-metadata auq_thread_id=<thread id>`.
6. Print one line: how many questions you posted, and how many were already posted and not yet recorded. Then exit. Answers are recorded later:
   - each role's next work-loop session records the answers to its own questions (`slice` step 2, `question` §6);
   - an operator's `/beadwork:grill` records the rest, including the night-summary answer (§4).

A second morning run finds everything already posted and posts nothing. If the call errors after posting (a 429, for example), the error names the ids. Store those ids. Never post again.

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

Blocking is normal. If the call returns `pending`, or an error after posting (the error names the ids), run `"<plugin-root>/scripts/auq-wait.sh" <ids> 14400` as a background command and end the turn; the answers resume the work. Never re-post to get past an error.

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
  - feature requirement → `docs/capabilities/`, quality requirement → `docs/requirements/`, objective → `docs/product/objectives.md` (the `write` skill).
- **Night summaries the operator has read:** `bd close <id> --reason "read in grill"`, for every summary bead that shares the question id.
- **"Something looks wrong" on a night summary:** if the answer doesn't already say what, ask in the same thread (`parent_question_id`). File it with the `bead` skill as a bug labelled `surprise`, with `--deps discovered-from:<a summary's id>`. Then close every summary bead that shares that question id.

## 5. Memory hygiene

Run `bd memories`. For each memory:
- still needed and short-lived: keep it;
- durable: promote it to the right doc, then `bd forget <key>`;
- stale: `bd forget <key>`.

## 6. Report

Lead with a one-line verdict. Then give one short list: answered, deferred, follow-up beads filed, and what is now ready (`bd ready`). If the operator must still act on something, end with a `What I need from you` list; leave it out when there is nothing.
