---
adr: ADR-20261026-154820-f051
title: "Share one skill source across Claude Code and Codex"
status: Superseded
date: 2026-10-26
supersedes: []
superseded_by: ADR-20261026-173924-ce2c
amends: []
amended_by: []
refs: [ADR-20261026-134412-fb40]
---

# Share one skill source across Claude Code and Codex

## Context

On 2026-10-26 the operator requested Codex support for the Beads and docs workflow, authorized implementation and PR creation, and asked to continue after an account usage interruption. The workflow authority in the referenced decision applies in both hosts.

Codex supports the existing repository marketplace and portable root plugin manifests. The skills themselves use compatible Markdown, but invocation policy, helper paths, startup hooks, project instruction filenames and unattended model launches need explicit host handling.

## Decision

Keep one maintained `plugins/<name>/skills/` tree and one helper implementation per plugin. Add a portable `plugin.json` beside the Claude manifest, keep identity and version aligned, and reuse the existing marketplace. There is no generated skill mirror or second repository.

Each skill receives Codex metadata in `agents/openai.yaml`. The operator procedures preserve explicit-only invocation; `bead`, `question`, `write` and `adr` remain automatically discoverable. Runtime guides resolve helper paths from the loaded skill rather than depending on a host's environment variable.

Share project rules through `AGENTS.md` and `CLAUDE.md`, using a symlink when identical. Prefer neutral `.beads/roles/` cards while retaining existing `.claude/roles/` and explicit overrides. Keep one startup script, with a host-specific hook definition for Codex. Codex hook trust and sandbox/approval policy remain in effect; absent startup context can be loaded explicitly through normal approvals.

The night runner selects Claude or Codex through `BEADWORK_ENGINE`. Models and effort fields are separate for each engine. Codex uses `codex exec` and reads the final-message file for its result, so echoed examples in the transcript cannot be mistaken for delivered work. The existing lease, eligibility, evidence and timeout-recovery rules still apply.

## Consequences

Both hosts receive workflow fixes from the same source. Installation uses each host's normal marketplace tools. A developer can use the local checkout, and projects can use a Git ref without maintaining symlinked skill mirrors by hand.

Two small manifests and two invocation-policy declarations must stay aligned; packaging tests check that agreement. Codex installs cached copies, so source changes need a plugin refresh and new sessions. Hook trust, credentials, network permissions and the availability of delegation or question tools remain environment concerns rather than permissions granted by a skill.

Implemented and verified: Codex CLI 0.164.0 discovers the marketplace, installs both plugins, and exposes the four discoverable skills in local prompt inspection without a model request. Unattended execution and startup behavior are covered with stub processes and temporary repositories. A live Codex night run and separate IDE distribution remain unverified.

## Alternatives considered

- Maintain a Codex copy of every skill: independent wording and bug fixes would drift, and every workflow change would need two reviews.
- Generate a mirror on install: adds transformation, deployment and stale-output failure modes despite native support for shared packages.
- Document manual skill copying only: leaves helper paths, hooks, policy and unattended execution inconsistent, and shifts updates onto every project.

## What would prove this wrong

A host begins interpreting shared instructions differently enough to change task authority, package updates repeatedly leave stale or mismatched behavior, or compatible distribution prevents required client support. Isolate the demonstrated host-specific behavior before duplicating whole workflows.
