---
adr: ADR-20261025-110438-9a48
title: "Adopt the human-first documentation standard"
status: Accepted
date: 2026-10-25
supersedes: []
superseded_by:
amends: []
amended_by: []
refs: []
---

# Adopt the human-first documentation standard

## Context

The Cloud Workbench Product Documentation Standard v0.9.0 (a draft spec held by the operator, not in this repo) set out Docs-as-Code for product monorepos: Antora and AsciiDoc, Diátaxis page kinds, padded ids, RFC and change-request documents, an evidence model, and an agent workflow. A gap analysis dated 2026-10-15 found that "human first, agents second" was stated but not enforceable. Reader usefulness could lose to template completeness, metadata and automation, and reader testing sat in the lowest priority band.

Three things have changed since v0.9 was written:
- The claude-workbench that v0.9 targeted is being retired.
- Live work now runs in Beads, with operator questions through auq.
- Most of our projects have one human, the operator, working with agents.

The operator settled the open points in two grills on 2026-10-25.

## Decision

We will maintain one documentation standard in claude-shared-skills, as a short page (`docs/reference/documentation-standard.md`) enforced by the `docs` and `beadwork` plugins:

1. **People first.** Docs are for people; agents are tools. The tie-breaker: reject anything that helps agents but makes a page harder for a person, or move it off the page.
2. **Readers:** the operator, engineers joining a project, people running systems, external users. Agents read the same pages, with ids, anchors and small header blocks as their only aids.
3. **Markdown in Git,** replacing v0.9's agreed choice of AsciiDoc and Antora. A product that needs a published site gets a Markdown site generator over the same files.
4. **Layout:** v0.9's domains (product, capabilities, flows, architecture, domain, requirements, decisions, planning) behind task-named entry sections (start, guides, operate, reference). Each section exists only once it has a real page.
5. **Ids:** timestamp ids for what agents write (REQ, NFR, ADR); short ids for the objectives the operator owns (OBJ-n).
6. **No RFC or change-request documents.** A proposal is a Proposed ADR; a requirement change is a decision bead.
7. **Drift and impact:** a four-value `Docs impact:` line in every PR. Contradictions become decision beads; `/docs:audit` sweeps on demand.
8. **Acceptance:** structure and reader value are reported separately. A fresh agent does a reader walkthrough on every docs change, and the operator walks the same tasks at milestones. Critical pages need the operator's review.
9. **Agents get the rules** from two lines in each project's `CLAUDE.md`, plus the `docs:write` skill, which they load themselves.
10. **The gap report's changes** are adopted:
    - the people-first precedence rule;
    - a named reader and question for every page;
    - a reader-benefit gate before writing;
    - templates as prompts;
    - reader testing as a gate;
    - ids kept out of headings;
    - landing-page navigation, with the main point first and details deeper;
    - visible built-versus-planned labels;
    - readable diagrams and plain-prose examples;
    - owners for critical pages;
    - build health reported apart from reader value.

    Two wait for a published site: rules for embedded API widgets, and search at scale.

These are kept from v0.9 unchanged in spirit:
- question-specific authority, and conflict triage that never rewrites approved intent or decision history;
- the four impact outcomes;
- truth labels and evidence on consequential pages;
- framework-native OpenAPI and no custom generators;
- no CI agent;
- no document explosion;
- accepted ADRs are immutable.

## Consequences

- Positive: one short standard, and the skills that apply it, in one versioned place.
- Positive: no AsciiDoc toolchain or site build until a product needs one.
- Positive: reader testing happens on every docs change instead of at the end.
- Positive: fewer document types for agents to choose between.
- Negative: no portal across products, no embedded Swagger UI, and no Antora versioning. A product with external users needs a site generator chosen later.
- Negative: a later move to Antora would mean converting files.
- Negative: v0.9's padded ids and its RFC and change-request templates are dropped. Projects that used them need migration through `/docs:init`.
- Negative: the reader walkthrough adds one sub-agent run, and its tokens, to every docs change.
- Negative: with one human, every critical page lands on the operator.

## Alternatives considered

- **Keep v0.9 as master and patch it to v0.9.1:** two documents to keep in step with the skills that enforce them.
- **Antora with AsciiDoc everywhere:** a toolchain and a format change for every repo, including ADRs, before any product needs a published site.
- **Folders by Diátaxis type:** navigation named after page types instead of reader tasks, and architecture and domain pages pushed under "explanation".
- **Short padded ids everywhere:** v0.9's registry admits it cannot stop parallel agents taking the same number.

## What would prove this wrong

- The home-lab or Necronia v2 pilot fails its reader tasks because of the standard itself, not because of missing content.
- A product's external readers need a portal across repos that a Markdown generator cannot provide.
- The fresh-agent walkthrough keeps passing pages that the operator then fails.
