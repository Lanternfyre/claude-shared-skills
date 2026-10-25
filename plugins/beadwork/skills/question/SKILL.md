---
name: question
description: Raise a decision or a surprise with the operator through Beads and auq. Classify it, file the bead, write a plain-language card, then wait, park the work, or go ahead on a provisional default. Use when a choice is the operator's to make, or when you find a bug, missing fact or undefined domain term outside your bead.
---

# Raising a question or a surprise

`$ID` is the bead you are working on, `$ROLE` is `$BEADWORK_ROLE` (or `operator`). The project's instructions (CLAUDE.md, `.beads/PRIME.md`) win over this skill.

## 1. Surprise or decision?

- **Surprise:** a bug, a missing fact or a broken assumption outside your bead. File it, then carry on unless it blocks you:
  `bd create -t bug -l surprise --deps discovered-from:$ID --body-file s.md --validate --silent`
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

The body has the sections Question (plain words), Options, Recommendation, Default, If overturned and Level. It is not an epic child. auq ids go in metadata, never in the text.

```bash
QID=$(bd create --title "<the question, in plain words>" -t decision --silent \
  -l human,default-ok,"asked-by:$ROLE",level:2,topic:<area> \
  --deps "discovered-from:$ID" --body-file q.md --validate)
```

## 4. Write the card (auq `ask_user_questions`)

The visible text is for a human who has forgotten everything:
- Use plain language in product terms. `context` recaps what happened and why it matters now.
- Give a concrete example where it helps: a snippet, a scenario, a before/after.
- Offer 2–4 options with the recommendation starred (`recommended: true`). Name the default. Each option's description says what changes if it is chosen over the default.
- Add a "Go one level deeper" option with `expects_followup: true`.
- **No AI references in visible text.** Bead ids, paths, rule ids and evidence go in `agent_notes`, which only select-type questions carry. `agent_notes` is hidden from the operator, so never put anything there they would need in order to decide.
- `requester_name` is `<role>@<host>`. Send one card per sitting: batch everything you can ask now.

## 5. Day or night

The session-start line says which it is (`BEADWORK_TZ`, `BEADWORK_DAY`; default Europe/Warsaw, 08–23).

- **Day:** post the card. If the project says a steward posts cards, store it instead with `bd update $QID --set-metadata "auq_card=$(jq -c . card.json)"`. Record the ids: `bd update $QID --set-metadata auq_question_id=<ids> --set-metadata auq_thread_id=<id>`. Wait up to 30 min. On `pending`, run `auq await <ids> --max-secs 1800` in the background. No answer means night handling.
- **Night, or unanswered:**
  - **default-ok:** proceed on the default, run `bd label add $QID provisional`, and name it in the PR body.
  - **must-ask:** park the bead:
    ```bash
    git push origin "HEAD:bead/$ID-wip"
    bd dep add "$ID" "$QID"
    bd unclaim "$ID" --reason "waiting on $QID"
    ```
    Then stop its heartbeat and take the next ready bead.
- Never re-post a question that is still live; await its ids.

## 6. When the answer arrives

1. `bd human respond $QID -r "<option id>: <label>"` closes the question and unblocks parked work.
2. Record it where it belongs: architecture → `docs/adr/`, domain rule → `docs/domain/`, requirement → `docs/requirements/`.
3. If it overturns a provisional default you built on, file a fix bead with `--deps discovered-from:$QID`.
