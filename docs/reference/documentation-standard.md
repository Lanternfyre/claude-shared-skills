# Documentation standard

How our projects write and keep documentation. This page is the version people read. Agents follow the same rules through the [`docs`](../../plugins/docs/skills/write/SKILL.md) and [`beadwork`](../../plugins/beadwork/skills/slice/SKILL.md) skills. These rules apply now; the pilots test whether they work. Only the structural part is automated (`docs.py check`). The reader walkthrough, the `Docs impact:` line and the review of critical pages are steps the skills tell agents to take, and the operator sees them in the PR digest (`/beadwork:review-chunk`). Nothing blocks a merge that skips them yet.

*Version: follows the `docs` plugin (0.3.0). A draft until the two pilots pass ([Reaching 1.0](#reaching-10)). It replaces the Cloud Workbench Product Documentation Standard v0.9.0; the reasons and every change from v0.9 are in the [adoption decision](../decisions/ADR-20261025-110438-9a48-adopt-the-human-first-documentation-standard.md).*

## The rule

Documentation is for people. Agents write it, maintain it and read it, but they are tools, not the audience. **If something helps agents but makes a page harder for a person to understand, find or maintain, don't do it, or keep it off the page.** When readability and truth pull apart, keep the truth and fix the presentation, or state the uncertainty plainly.

## Readers

- the operator, coming back to a project after weeks away;
- engineers joining a project;
- people running systems;
- external users of a product or API.

Agents read the same pages. The only aids added for them are ids, link anchors and small header blocks, none of which change how a page reads. Instructions for agents live in `CLAUDE.md` and the skills, never in docs pages.

## Where things go

The root `README.md` is the landing page. It answers three questions: what this is, how to start, and where things are. Its links are task-named: Start, Build, Operate, Reference, Architecture, Decisions.

| Section | Holds |
|---|---|
| `docs/start/` | First-run tutorial |
| `docs/guides/` | How to do a specific thing |
| `docs/operate/` | Runbooks |
| `docs/reference/` | API (exported OpenAPI), config, CLI |
| `docs/product/` | Vision, objectives, who it is for |
| `docs/capabilities/` | Each feature and its requirements |
| `docs/flows/` | Journeys across components |
| `docs/architecture/` | Boundaries, components, constraints |
| `docs/domain/` | Glossary, rules, invariants |
| `docs/requirements/` | System-wide quality requirements |
| `docs/decisions/` | ADRs and their index |
| `docs/planning/` | Roadmap and open questions |

A section exists only once it has a real page, and every section has a `README.md` saying what it holds. Live work, such as task progress, blockers and fresh findings, belongs in Beads, not in docs. Short-lived agent context goes to `bd remember`. A finding worth keeping is moved into the right page in the PR that found it.

## Writing a page

- **One reader, one question.** Before writing, name who the page is for, what they know, and what they will do next. Improve an existing page before adding one, and never state a fact twice.
- **One kind per page:** tutorial, how-to, runbook, reference or explanation. Capabilities, flows, requirements, decisions and plans are governance pages. A feature gets the pages it needs, never all four reader kinds by default.
- **Templates are prompts.** Leave out what doesn't apply. No TBD, no filler, no invented examples.
- **Purpose first.** The opening paragraph says what the page is for. The main point comes next; details sit deeper or behind a link.
- **Human headings.** An id never leads a heading. It sits in an anchor and a small line below.
- **Say what is real.** Pages about architecture, security, operations, external interfaces or business rules say in plain words what is Implemented, Planned, Proposed or Unverified, and how we know it. A date is not evidence.
- **Diagrams** are Mermaid inside the page. Each answers one question, with a caption and a sentence or two of prose.
- **API reference** comes from the framework's own OpenAPI export. Never hand-copy request and response tables.
- **Plain prose:** concrete, active, no inflated introductions or performative conclusions.
- **Exposure:** pages for external readers carry no internal hosts, endpoints, credentials or personal data.

## Ids

- Feature and quality requirements: `REQ-…` and `NFR-…`, timestamp ids minted by `docs.py id`, so parallel agents never clash.
- ADRs: timestamp ids too.
- Objectives: short ids (`OBJ-2`), because only the operator creates them and says them out loud.
- Each id is defined once, with an anchor, and never reused. Code comments may cite requirement ids.

## Decisions and proposals

An ADR records a decision that is hard to reverse, surprising without context, and a real trade-off. A proposal is an ADR with status Proposed; there are no separate RFC or change-request documents. Once Accepted, a decision is never edited to say something else: a new ADR supersedes it.

A change to an approved requirement is a decision bead. Its answer edits the requirement page in the same PR.

## Keeping docs true

- **Every PR body** ends with a `Docs impact:` line, for example `Docs impact: updated (docs/operate/backup.md)`. It takes one of four values:
  - **none**;
  - **updated**, naming the pages;
  - **needs review**, saying why;
  - **unknown**, saying what wasn't checked.

  A security or public-contract change with no matching docs is "unknown", never "none".
- **Contradictions** between a requirement, an ADR and the code are never resolved by editing one source to match the others. The agent lists every source with its version and files a decision bead. Approved requirements stand until the operator decides, and ADRs stay as history.
- **`/docs:audit`** sweeps a repo for drift, content problems and broken structure.

## Acceptance

- **Structure and reader value are reported separately.** `docs.py check` proves links, anchors, ids and ADR consistency, and nothing about usefulness. There is no single quality score.
- **Every docs change** gets a reader walkthrough by a fresh agent: it starts at the README, follows only links, and tries two or three real reader tasks.
- **At milestones** the operator walks the same tasks by hand. A failed task blocks "ready" unless it is recorded as an accepted exception.
- **Critical pages** need their owner's review in the PR: architecture, security guidance, destructive runbooks, business claims, and anything for external readers. The owner is the operator, unless the page names someone else on an `Owner:` line under its title. Other pages carry no owner, date or status boilerplate.

## Publishing

Docs are Markdown, read in the Git host. Markdown needs no toolchain until a product needs a published site; Antora would mean AsciiDoc and a site build in every repo first ([why](../decisions/ADR-20261025-110438-9a48-adopt-the-human-first-documentation-standard.md#alternatives-considered)). When a product needs a published site, a Markdown site generator builds it from the same files, for example MkDocs Material. Before anything is published outside the team, its pages and assets are checked for exposure.

## Versions

- The standard's version is the `docs` plugin's version. Each repo records the version it adopted in its `CLAUDE.md`.
- Product releases and docs versions are separate. The docs describe the default branch until supported releases diverge.

## Reaching 1.0

1. home-lab and Necronia v2 adopt the standard through `/docs:init`.
2. In each, the fresh-agent and operator reader tasks pass. That means newcomer, change and operate tasks, plus an external-user task where one applies.
3. A real change makes the full round trip: docs impact, updated pages, check and walkthrough.
4. A deliberately introduced contradiction comes back as a decision bead, not a silent edit.
5. A failed criterion stays open; an exception is recorded as an ADR.

*Status on 2026-10-25: neither pilot has started.*

## Not doing

- no documentation agent in CI;
- no custom OpenAPI slicer or renderer;
- no knowledge graph or vector search;
- no ids on every paragraph;
- no Antora for now ([why](../decisions/ADR-20261025-110438-9a48-adopt-the-human-first-documentation-standard.md#alternatives-considered));
- no RFC or change-request documents;
- no rewriting accepted ADRs;
- no four reader kinds per feature by default.
