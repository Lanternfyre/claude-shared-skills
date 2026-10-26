---
role: <name>
paths: <optional comma-separated globs for expected scope, e.g. src/**, tests/**>
protected: <optional comma-separated globs requiring explicit authorization; omit if none>
---

# <Role name>

<!-- Roles route work; several Claude or Codex workers can share one role.
     A card is optional. Keep it only if it adds useful project context.
     Resolve BEADWORK_ROLE_CARD, BEADWORK_ROLE_DIR/<name>.md,
     .beads/roles/<name>.md, then legacy .claude/roles/<name>.md.
     Models, effort and availability belong to the launcher, not this card.
     Keep the header flat: one key: value per line. -->

## Purpose

What this queue is for, and any context that changes how the work is done.

## Boundaries

- Explicit project protections only. Expected paths are advisory; necessary adjacent changes remain allowed. Preserve existing authorization rather than asking twice.
- Keep project-specific separation requirements here when they actually apply. Roles do not introduce a generic planner/reviewer/implementer hierarchy.
