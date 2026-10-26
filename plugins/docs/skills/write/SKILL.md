---
name: write
description: Write, move or restructure a documentation page (docs/ or a README) so a person can use it. Pick the reader and their question, reuse what exists, choose the smallest useful form, then check structure and walk the reader route. Use before any docs page is created or substantially changed.
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/docs.py *)
---

# Writing documentation people can use

Use the [host runtime guide](../../runtime.md) for invocation, helper paths and startup context.

Docs are for people: the operator, engineers joining a project, people running systems, external users. Agents write and maintain the docs and read the same pages, but they are not the audience.

**If something helps agents but makes a page harder for a person to understand, find or maintain, don't do it, or keep it off the page.** When readability and truth pull apart, keep the truth and fix the presentation, or state the uncertainty plainly.

## Before writing: the gate

1. **Reader and question.** Who needs this page? What do they already know, and what will they do next? A page answers one question or supports one task. If you can't name the reader and the question, don't write the page.
2. **Existing answer.** Search the established docs home first. Improve the canonical page before adding one. Link to detailed facts; a short summary is useful when it helps the reader understand the page without unnecessary navigation.
3. **Smallest useful form.** Pick one kind from [kinds.md](kinds.md). Never create several kinds for one feature by default. A small change usually needs a paragraph in an existing page.
4. **A home readers can reach.** Put the page in the section below that fits it. Create a section folder only with its first real page, and give the section a `README.md`: one paragraph on what the section is for, then its pages. Link the new page from that README, so a reader can get from the root README to the page without knowing any path.

## Layout

| Section | Holds |
|---|---|
| `README.md` (repo root) | What this is, how to start, where to find things |
| `docs/start/` | First-run tutorial |
| `docs/guides/` | How to do a specific thing |
| `docs/operate/` | Runbooks: symptoms, safe steps, verification, rollback |
| `docs/reference/` | API (exported OpenAPI files), config, CLI |
| `docs/product/` | Vision, objectives (`objectives.md`), who it is for |
| `docs/capabilities/` | Each feature, with its requirements (REQ) |
| `docs/flows/` | Journeys across components |
| `docs/architecture/` | Boundaries, components, constraints, diagrams |
| `docs/domain/` | Glossary (`glossary.md`), rules, invariants |
| `docs/requirements/` | System-wide quality requirements (NFR) |
| `docs/decisions/` | ADRs; its `README.md` is the generated index (the `adr` skill) |
| `docs/planning/` | Roadmap, open questions; never phrased as built |

A repo with its own established layout keeps it. A request to reorganize docs authorizes the necessary moves and link repairs; do not ask twice. Routine in-scope moves are allowed. Ask before an unrequested broad reorganization or a move that changes a published URL contract.

## Writing

- **Lead with the purpose.** The first paragraph says what the page is for and who it helps. Then comes the main point. Details go deeper down, or behind a link.
- **Headings say what the section answers.** An id never leads a heading. A requirement looks like this:
  ```markdown
  ### Expired refresh tokens are refused
  <a id="REQ-20261025-110045-29dc"></a>
  A refresh token past its expiry never issues an access token.

  *REQ-20261025-110045-29dc · Implemented · verified by `RefreshTokenTests.Expired_token_is_rejected`*
  ```
- **Templates are prompts.** Leave out sections that don't apply. Never write TBD, filler or invented examples. Unknowns that matter go under a short "Open questions".
- **State what is real.** On consequential pages (architecture, security, runbooks, external interfaces, business rules), say in plain words what is Implemented, Planned, Proposed or Unverified, and how we know: the test, commit or check. A date is not evidence. A plan never reads as if it were built.
- **Diagrams** are Mermaid inside the page. Each one answers one question, has a caption, and has a sentence or two of prose saying its point. Split anything a reader would have to zoom into.
- **API reference** comes from the framework's own OpenAPI export, kept in `docs/reference/`. Prose explains intent and gives one real example. Never hand-copy request or response tables.
- **Exposure.** Pages meant for external readers carry no internal hosts, endpoints, credentials or personal data.
- **Never invent** a feature, route, output or status. If the evidence is missing, leave the claim out or mark it Unverified.
- Before finishing, check the page against [prose.md](prose.md).

## Ids

- **Requirements:** `python3 "<plugin-root>/scripts/docs.py" id REQ` for a feature requirement (in `capabilities/`), or `id NFR` for a quality requirement (in `requirements/`). Define each id once with `<a id="…"></a>` and never reuse one. Pages and code comments may cite it.
- **Objectives:** `OBJ-n`, owned by the operator (`/docs:objectives`).
- **ADRs:** the `adr` skill.

## Critical pages

Substantive changes to these pages need their owner's review before integration, unless the owner has delegated that review:
- architecture;
- security guidance;
- runbooks with destructive steps;
- business claims;
- anything written for external readers.

The operator owns them, unless the page names another owner with an `Owner:` line under its title. Typo, formatting and link repairs that preserve meaning do not need a separate owner sign-off. Existing approval of the exact content counts. Other pages carry no owner, date or status boilerplate.

## Contradictions

When sources disagree, identify which source has authority for this question. Fix a demonstrable implementation bug against clear approved intent, or correct descriptive docs against verified behavior, within task scope. Preserve accepted ADR history. If the authoritative intent is ambiguous, or the proposed fix would change it, raise a decision through the `question` skill (must-ask for changed approved intent). Its Question section lists:
- the subject;
- each source, what it says, and its version or commit;
- what conflicts, and the risk;
- what needs deciding;
- what remains to verify.

Approved requirements stand until the operator changes them. Existing authorization to revise a requirement counts; record it rather than asking again. ADRs stay as history. With no Beads/question plugin, record unresolved decisions in the project's existing channel; do not install a tracker just to edit a page.

## Finish

1. Run `python3 "<plugin-root>/scripts/docs.py" check`. It checks structure only.
2. Select the proportional reader check in [walkthrough.md](walkthrough.md). A small factual edit needs a focused check; new pages, navigation or consequential guidance need an independent walkthrough when available.
3. Report these separately in the PR body, or the task evidence for local delivery. A passing structure check alone never makes the docs ready.
   ```text
   Docs impact: updated (<pages>) | needs review (<why>) | unknown (<what wasn't checked>) | none
   Structure: docs.py check passed | failed (<count>)
   Readers: focused check (<what was checked>) | walkthrough <n>/<m> tasks passed (<failures>) | not run (<reason and remaining review>)
   ```
