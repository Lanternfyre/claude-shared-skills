---
adr: ADR-20261026-134412-fb40
title: "Give agents authority within approved outcomes"
status: Superseded
date: 2026-10-26
supersedes: [ADR-20261025-110438-9a48]
superseded_by: ADR-20261026-173924-ce2c
amends: []
amended_by: []
refs: []
---

# Give agents authority within approved outcomes

## Context

The operator wants Beads and documentation skills to preserve an agent's ability to coordinate work and make engineering decisions. On 2026-10-26 the operator explicitly authorized outcome-preserving re-cuts and necessary adjacent fixes, then authorized revising the plugins. The follow-up decisions allow delegated implementation without a fixed agent count, project-specific delivery instead of mandatory stacks, and checks proportional to risk while preserving evidence and explicit approval boundaries.

The previous standard required a fresh reader for every documentation edit. The work loop also required approval for re-cuts, read-only delegates, a mandatory stack and several fixed process steps. These requirements could interrupt authorized implementation without improving its evidence.

This decision supersedes the original adoption decision. Its people-first purpose, Markdown format, question-led pages, canonical evidence, truthful built/planned status, stable ids, generated API references and immutable accepted decision history remain adopted. The current [documentation standard](../reference/documentation-standard.md) states the resulting rules.

## Decision

1. Agents may choose the implementation and delegate bounded work within an approved outcome. One bead owner coordinates writes, integrates results and owns the evidence. Project-specific restrictions and permissions still apply.
2. Agents may split, combine and reorder work without renewed approval when every acceptance criterion, protected boundary and promised behavior remains covered. Necessary adjacent fixes may extend expected paths; unrelated improvements remain separate work.
3. Role `paths` describe expected scope; `protected` globs and explicit project prohibitions are hard boundaries. Policy comes from the approved branch. Existing explicit authorization can be recorded as an exception; a work branch cannot grant itself authority by editing its card.
4. Routine implementation choices need no operator decision bead. Optional reversible preferences may proceed on a stated default. Changed intent, protected actions and material commitments need the applicable authorization; silence never grants it.
5. Beads owns current execution state and dependencies. Design plans and roadmaps stay in docs. Installed skills and tracker are assumed during execution; setup is separate work. A progress update need not be copied into several trackers or handover files.
6. Delivery is project-specific: independent PRs by default, stacks by choice, or local integration when configured. Mode does not authorize pushing or merging. Work closes only with verified acceptance and required integration; experiments close when their own evidence criteria are met.
7. Documentation checks scale with the change. Small factual and mechanical edits get focused checks. New pages, navigation changes and consequential guidance get an independent reader walkthrough when available, with limitations reported honestly. Structure and reader value remain separate results. Substantive critical-page changes still need owner review unless delegated; prior approval counts.
8. Clear implementation defects may be fixed against approved intent, and descriptive docs may be corrected against verified behavior. Ambiguous authority or changed approved intent needs a decision. Accepted ADR text stays historical and reversals use supersession. Existing proposal formats need no duplicate ADR solely for format compliance.
9. Investigation, review and checkpoint effort follow risk, uncertainty and budget. No fixed number of debugging hypotheses, one-spike quota or mandatory rewrite of useful experiment code applies. Required quality checks, lease ownership, unattended boundaries and explicit project limits remain.

## Consequences

Agents can keep working through routine decomposition, adjacent fixes and reversible implementation decisions. The operator receives fewer questions and can focus on choices that change outcomes. Existing project plans and local development flows can adopt the skills without adopting stacked PRs.

More judgment is delegated. Scope expansions need reviewable explanations, and a mistaken default can require rework. Expected-path warnings are no longer enforcement: projects upgrading from a hard allowlist must preserve it explicitly. Smaller docs changes receive less independent scrutiny. Real protected paths, required tests, integration evidence and substantive owner review limit those risks.

These are implemented workflow rules, with automated temporary-repository tests for path protection, local/PR night delivery and timeout ownership handling. Their effect on real project throughput and correction rates remains unverified until exercised in the pilots.

## Alternatives considered

- Keep the existing procedural gates: less local discretion, but routine work repeatedly waits for the operator and delivery mechanics constrain otherwise compatible projects.
- Remove all boundaries: fewer interruptions, but no protection against changing approved intent, conflicting writers or claiming unfinished work as complete.
- Add an independent fast mode: preserves existing defaults but leaves two competing workflows and makes projects discover which one allows ordinary engineering judgment.

## What would prove this wrong

Repeated re-cuts lose acceptance coverage, adjacent fixes grow unrelated scope, delegated work produces ownership conflicts, or lighter reader checks allow consequential guidance errors. Review evidence from completed work and tighten the specific failing boundary rather than reintroducing every procedural gate.
