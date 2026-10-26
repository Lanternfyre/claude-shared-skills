---
name: glossary
description: Build and maintain the project's ubiquitous language in docs/domain/glossary.md. Harvest candidate terms from docs, code and beads, settle synonyms and homonyms with the operator, write short entries agents can rely on, and check text against them.
argument-hint: "[harvest | check <path or PR>]"
disable-model-invocation: true
---

# Ubiquitous language

Use the [host runtime guide](../../runtime.md) for invocation, helper paths and startup context.

The aim: one word per concept and one concept per word inside a bounded context, used the same way in conversation, docs, beads, code, tests and UI. The glossary records domain meaning. Agents consult relevant entries when domain naming matters; ordinary internal identifiers do not require a glossary entry.

- No argument, or `harvest`: steps 1–4.
- `check <target>`: step 5 only.

## Entry format (`docs/domain/glossary.md`)

Keep entries concise and load the relevant context; the whole glossary need not enter every session.

```markdown
## Settlement
- **Context:** Billing
- **Means:** the transfer that closes a customer's open balance for one billing period.
- **Not:** payment (one card charge), payout (money to a merchant). Avoid "transaction".
- **Example:** the March settlement for account 1042: 3 invoices, €212.40, settled 2026-04-02.
- **Rules:** a period has at most one settlement → docs/domain/billing.md#settlement
- **Code:** `Settlement`, table `settlements`, route `/settlements`
- **Serves:** OBJ-2
```

The file starts with the list of bounded contexts and a sorted term index. When one word means different things in two contexts, give each its own entry (`Account (Billing)`, `Account (Identity)`). If there are many contexts, split into one file each under `docs/domain/<context>/` and keep the index here.

## 1. Harvest

**Sources:**
- `docs/product/`, `docs/capabilities/`, `docs/domain/` and the README;
- bead titles (`bd list --all --json`);
- code identifiers: types, tables, routes, enums, events;
- UI strings and test names.

**For each candidate term,** record where it appears (counts and two examples) and what it seems to mean.

**Then look for:**
- **synonyms:** different words for the same thing (user, account, customer, member);
- **homonyms:** one word meaning different things in different contexts;
- **vague words:** item, data, info, process, manager, handle, record;
- **drift:** the code says one word and the docs say another.

## 2. Draft

Draft every entry yourself from the evidence. Ask the operator only for what the evidence cannot settle.

## 3. Ask in one batch

Use auq when installed, or the host's question tool/chat in an attended session.
- **For each synonym cluster:** "Which word do we use for <a plain description>?" The options are the candidate words, each noting where it is used today, plus "These are different things" (`expects_followup`).
- **For each homonym:** "Is a <word> in <context A> the same thing as in <context B>?"
- **For each definition you had to guess:** confirm or correct it, with the example shown.

Write in business language. Star the recommendation. No file paths in the visible text.

## 4. Write and follow up

- Update the entries and keep the index sorted. Rejected words go under **Not**.
- Code that still uses a rejected word gets one bead per rename seam (`topic:glossary`). Never do a big-bang rename.
- Link an existing objective in **Serves** when relevant. A missing objective can be captured for later product work; do not block an established term's definition to create one.

## 5. Check

For the given path, PR or diff, report:
- every use of a word listed in some entry's **Not** line;
- every domain-looking noun the glossary lacks.

Each finding gives the location, the word and the term to use instead. Undefined terms are candidates for the next harvest, or a `topic:glossary` question when the project uses Beads.
