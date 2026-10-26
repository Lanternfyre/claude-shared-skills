---
name: question
description: Raise a decision or a surprise with the operator through Beads and auq. Classify it, file the bead, write a plain-language card, then wait, park the work, or go ahead on a provisional default. Use when a choice is the operator's to make, or when you find a bug, missing fact or undefined domain term outside your bead.
---

# Raising a question or a surprise

Use the [host runtime guide](../../runtime.md) for invocation, helper paths and startup context.

`<id>` is the bead you are working on. `<role>` is the role in the session-start status line, or `operator` if the line names none. Fill command placeholders with actual values; use literal commands when the host's permission checks require them. User instructions and existing authorization take precedence; project rules (`AGENTS.md` or `CLAUDE.md`, and `.beads/PRIME.md`) fill in the boundaries. Do not ask again for an action already authorized.

## 1. Surprise or decision?

- **Surprise:** unrelated work discovered during your bead. File it, then carry on unless it blocks you. A necessary adjacent fix within the approved outcome can stay in the current bead (the `bead` skill). Use bug only for an actual defect with reproduction evidence; missing information may need a task or investigation instead:
  `bd create -t bug -l surprise --deps discovered-from:<id> --body-file s.md --validate --silent`
  A bug's Steps to Reproduce is a Given/When/Then scenario that fails today.
- **Implementation choice:** approach, internal structure, test names, routine decomposition and outcome-preserving adjacent fixes belong to the agent. Choose from the evidence and record consequential choices in the bead or PR; no question bead is needed merely because alternatives exist.
- **Decision:** a choice the operator owns, such as changed requirements, public contracts, security boundaries or material cost/commitments. Check existing authorization before filing.
- **Domain term:** reuse the documented or unambiguous established meaning. Ask with `topic:glossary` when ambiguity changes behavior or the business meaning; absence from the glossary alone is not a blocker. Record established meanings directly.

## 2. Classify

- **must-ask:** unresolved changes to approved intent or protected boundaries, and actions requiring permission that has not been granted (for example data loss, rewriting shared history, changing secrets or external publication), plus the project's categories. Never proceed on a default. The label is `must-ask`, unless the project names its own.
- **default-ok:** a reversible choice within delegated authority where operator preference would help but is not required. State the default and proceed immediately, by day or night. Keep the question open for correction; silence is not approval. Routine implementation choices need no card.
- **Level:** impact × how hard it is to undo.

| Level | When | Card |
|---|---|---|
| 1 | small, easy to undo | `single_select` |
| 2 | the wording alone is ambiguous | `single_select` with a snippet or scenario in `context`, or `code_choice` with "(recommended)" in a label |
| 3 | real costs either way | `tradeoff` (pros, cons, risks) |
| 4 | big or hard to undo | ask for the decision, or propose a bounded spike when evidence is missing. Run authorized investigation without another approval; the consequential action still waits for authorization. |

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
- Lead with the consequence in plain language. Put ids and paths in `agent_notes` on phone cards; include a short code or API example when it is needed to decide. In a technical session, use the detail and format the operator prefers.
- Give a concrete example where it helps: a snippet, a scenario, a before/after.
- Offer 2–4 options with the recommendation starred (`recommended: true`). Name the default. Each option says, in the operator's terms, what it costs and what it rules out.
- Offer "Go one level deeper" when further investigation would change the decision. Follow up in the same thread (`parent_question_id`). Set `expects_followup: true` only on a question whose answer you will branch on at once.
- Bead ids, paths, rule ids and evidence go in `agent_notes`, which only select-type questions carry. `agent_notes` is hidden from the operator, so never put anything there they would need in order to decide.
- `requester_name` is `<role>@<host>`. Send one card per sitting: batch everything you can ask now.

## 5. Ask without stalling independent work

Use explicit operator availability, including the current conversation, before any saved default. `BEADWORK_MODE=attended` (default) means ask now; `unattended` or an away operator means store the card as `auq_card` metadata for the next batch. If the project uses a steward, store it for the steward instead. The clock does not decide availability, and classification controls what may proceed in either mode.

- **Attended:** use auq `ask_user_questions` with `block_until_complete: false`, then store the returned question and thread ids immediately. If auq is unavailable, use the session's question tool or chat; record the question and any answer in Beads, without inventing auq ids. A missing optional inbox does not stop authorized implementation.
- **default-ok:** record the default and reversal cost, run `bd label add <qid> provisional`, and continue. Name defaults with material consequences in the delivery evidence. Do not wait 30 minutes just to exercise authority you already have.
- **must-ask:** do independent work on the same bead while possible. When only dependent work remains, stop and collect delegates, save progress (push WIP only if authorized), add the blocker with `bd dep add <id> <qid>`, then release with `bd unclaim <id> --if-assignee <actor> --reason "waiting on <qid>"`. Stop the heartbeat and take other ready work. If ownership was lost, follow the slice skill's ownership recovery instead of writing or releasing. If the operator is actively deciding and a short wait helps, wait; never treat elapsed time as an answer.
- **No duplicates:** if `auq_question_id` is already set, inspect or await that question. If posting errors after creating the card, store the ids from the error. If the result is ambiguous, inspect the inbox before retrying; do not re-post blindly.

## 6. When the answer arrives

For a question with auq ids, pick up an answer posted earlier (by you, or by the morning card): `"<plugin-root>/scripts/auq-wait.sh" <the bead's auq_question_id> 5`. It prints the answer, or exits 3 while you are still waiting.

1. Confirm the answer actually settles the question; free text or "go deeper" may need a follow-up. Then `bd human respond <qid> -r "<answer and source>"` closes it and unblocks parked work. Answers given directly in the session count too.
2. Record it where it belongs: architecture → an ADR (the `adr` skill), domain rule → `docs/domain/`, requirement → its page in `docs/capabilities/` or `docs/requirements/` (the `write` skill).
3. If it overturns a provisional default you built on, file a fix bead with `--deps discovered-from:<qid>`.
