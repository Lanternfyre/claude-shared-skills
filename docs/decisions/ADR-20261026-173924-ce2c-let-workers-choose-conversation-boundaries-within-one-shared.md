---
adr: ADR-20261026-173924-ce2c
title: "Let workers choose conversation boundaries within one shared work loop"
status: Accepted
date: 2026-10-26
supersedes: [ADR-20261026-134412-fb40, ADR-20261026-154820-f051]
superseded_by:
amends: []
amended_by: []
refs: []
---

# Let workers choose conversation boundaries within one shared work loop

## Context

On 2026-10-26 the operator approved agent-selected delivery and conversation boundaries, optional existing roles, the same workflow for attended and unattended work, and a one-box trial with selectable Claude/Codex engines. The operator then explicitly authorized implementation and PRs. The previous runner forced a fresh session per bead and coupled model settings, routing and night eligibility in role cards.

This supersedes the two preceding workflow decisions while retaining their outcome-preserving autonomy, proportional docs checks, explicit project protections and single maintained skill source. The change is tracked by skills-wp1.20.

## Decision

- We will use one runner for both engines and both availability modes. The agent chooses whether the next turn reuses the explicit conversation ID, starts fresh, or stops. Auto-compaction is the host's responsibility.
- We will keep roles as optional queue filters and context. A role may have multiple workers and either engine. Launch configuration selects model, effort, availability and the authorized queue; a unique worker identity owns each claim across sequential conversation refreshes.
- We will default delivery to automatic agent selection within project conventions, preserving an existing bead's method. Independent PRs remain the fallback; stacks and local integration remain available. Delivery selection does not grant push or merge authority.
- We will retain current progress in Beads and store only process identity, exact bead/checkout, logs and fixed deadline in the checkout's Git-private runtime directory. The supervisor verifies the recorded handoff before continuing. A conversation refresh cannot extend the budget.
- We will use the same engineering authority in attended and unattended runs. Current operator availability determines immediate versus queued questions; project restrictions and host permissions still apply. Reversible choices within approved outcomes, delegated implementation, proportional review and protected boundaries retain the earlier decisions' meaning.
- We will preserve one source for skills/helpers, host-specific invocation metadata, normal sandbox/approval/hook trust, and shared project instructions. The existing night entrypoint remains a compatibility launcher, not a second workflow.

## Consequences

Workers can retain useful context across related beads and refresh it when useful. The operator does not need to manage conversation size, route every implementation detail, or maintain separate day and night processes. Distinct workers and isolated checkouts permit parallel work without sharing a claim identity.

A small supervisor and validated handoff are still necessary. Clean pauses and unclean interruptions have different recovery requirements. Saved notes can be incomplete, so a replacement must inspect the actual checkout and evidence. Process checks cannot prove acceptance criteria or prevent every detached writer; recovery must establish that old writers stopped. A live box can still lack login, network access or sandbox support even when subprocess tests pass.

## Alternatives considered

- A fresh conversation for every bead: predictable isolation but discards useful context and prevents the agent choosing a better boundary.
- One indefinitely running conversation with only compaction: supports continuity but provides no independent recovery after a process or pod interruption.
- A separate orchestration service or separate engine-specific workflows: adds deployment and maintenance before the one-box trial demonstrates a need.

## What would prove this wrong

Real trials repeatedly lose task decisions during refresh, resume the wrong conversation or checkout, leave conflicting writers, or spend more operator time recovering than they save. Fix the demonstrated failure and rerun that scenario before adding general process gates.
