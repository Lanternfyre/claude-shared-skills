---
name: question
description: Raise a decision or a surprise with the operator through Beads and auq. Classify it, file the bead, write a plain-language card, then wait, park the work, or go ahead on a provisional default. Use when a choice is the operator's to make, or when you find a bug, missing fact or undefined domain term outside your bead.
---

# Raising a question or a surprise

`<id>` is the bead you are working on. `<role>` is the role in the session-start status line, or `operator` if the line names none. Write commands literally, with the placeholders filled in; the permission check refuses shell variables and `$(…)`. The project's instructions (CLAUDE.md, `.beads/PRIME.md`) win over this skill.

## 1. Surprise or decision?

- **Surprise:** a bug, a missing fact or a broken assumption outside your bead. File it, then carry on unless it blocks you:
  `bd create -t bug -l surprise --deps discovered-from:<id> --body-file s.md --validate --silent`
  A bug's Steps to Reproduce is a Given/When/Then scenario that fails today.
- **Decision:** a choice with more than one reasonable answer that the operator owns. A code-level choice with an obvious convention is not a question: decide it and say so in the PR.
- **Undefined or ambiguous domain term:** a decision with `topic:glossary`. The answer goes into `docs/domain/glossary.md`.

## 2. Classify

- **must-ask:** destructive actions (data loss, force push, deleting history, deleting or rotating secrets, publishing outside the repo), plus the categories the project lists. Never proceed on a default. The label is `must-ask`, unless the project names its own.
- **default-ok:** everything else. At night, or when unanswered, you may go ahead on the default.
- **Level:** impact × how hard it is to undo.

| Level | When | Card |
|---|---|---|
| 1 | small, easy to undo | `single_select` |
| 2 | the wording alone is ambiguous | `single_select` with a snippet or scenario in `context`, or `code_choice` with "(recommended)" in a label |
| 3 | real costs either way | `tradeoff` (pros, cons, risks) |
| 4 | big or hard to undo | propose a spike: file it at level 4 with the variants. Once the operator approves, the spike runs as a bead and comes back as a level-3 question with numbers. |

## 3. File the decision bead

The body has these sections. The last three names are the ones bd's built-in decision lint requires.
- **Question:** in plain words.
- **Default:** what happens if nobody answers.
- **If overturned:** what changes if the operator picks something else.
- **Level:** 1 to 4.
- **Alternatives Considered:** the options, each with its cost and what it rules out.
- **Rationale:** your recommendation, why, and what would prove it wrong.
- **Decision:** `Open` at filing; the answer is recorded with `bd human respond`.

It is not an epic child. auq ids go in metadata, never in the text.

```bash
bd create --title "<the question, in plain words>" -t decision --silent \
  -l human,default-ok,asked-by:<role>,level:2,topic:<area> \
  --deps discovered-from:<id> --body-file q.md --validate
```
It prints the new bead's id; that is `<qid>` below.

## 4. Write the card (auq `ask_user_questions`)

**Read before asking.** List what already bears on the question: ADRs, the glossary, objectives, earlier decision beads, the code. Read whatever you haven't. A question a document already answers wastes the operator's turn, and the answer comes back shaped by your gap.

**Resolution check.** For each option, write the sentence you would act on if it were chosen. If any of those still leaves you unsure what to build, the question is too coarse: split it, or raise its level.

**Falsifier.** In the bead's Rationale, say what observation would prove the decision wrong. It carries over into the ADR.

The visible text is for someone on a phone who has forgotten everything:
- The first sentence of `context` says what changes for the operator. Then recap what happened, what you checked, and your prior: what you believe and why.
- Plain text only: no file paths, line numbers, commit hashes, bead or issue ids, and no markdown.
- Give a concrete example where it helps: a snippet, a scenario, a before/after.
- Offer 2–4 options with the recommendation starred (`recommended: true`). Name the default. Each option says, in the operator's terms, what it costs and what it rules out.
- Add a "Go one level deeper" option. If it is chosen, ask again one level up in the same thread (`parent_question_id`). Set `expects_followup: true` only on a question whose answer you will branch on at once, because it makes the call return before the rest are answered.
- Bead ids, paths, rule ids and evidence go in `agent_notes`, which only select-type questions carry. `agent_notes` is hidden from the operator, so never put anything there they would need in order to decide.
- `requester_name` is `<role>@<host>`. Send one card per sitting: batch everything you can ask now.

## 5. Day or night

The session-start line says which it is (`BEADWORK_TZ`, `BEADWORK_DAY`; default Europe/Warsaw, 08–23).

- **Day:** post the card. If the project says a steward posts cards, store it instead with `bd update <qid> --set-metadata 'auq_card=<the card JSON on one line>'`. Record the ids: `bd update <qid> --set-metadata auq_question_id=<ids> --set-metadata auq_thread_id=<id>`. Wait up to 30 min. On `pending`, run `auq await <ids> --max-secs 1800` in the background. No answer means night handling.
- **Night, or unanswered:**
  - **default-ok:** proceed on the default, run `bd label add <qid> provisional`, and name it in the PR body.
  - **must-ask:** park the bead:
    ```bash
    git push origin HEAD:bead/<id>-wip
    bd dep add <id> <qid>
    bd unclaim <id> --reason "waiting on <qid>"
    ```
    Then stop its heartbeat and take the next ready bead.
- Never re-post a question that is still live; await its ids.

## 6. When the answer arrives

1. `bd human respond <qid> -r "<option id>: <label>"` closes the question and unblocks parked work.
2. Record it where it belongs: architecture → an ADR (the `adr` skill), domain rule → `docs/domain/`, requirement → its page in `docs/capabilities/` or `docs/requirements/` (the `write` skill).
3. If it overturns a provisional default you built on, file a fix bead with `--deps discovered-from:<qid>`.
