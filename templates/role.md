---
role: <name>
model: <a `claude --model` value, e.g. opus or sonnet>
effort: <optional: a `claude --effort` level, low | medium | high | xhigh | max; e.g. high for building, max for planning and spikes>
codex_model: <required for Codex nights: a Codex model id supported by the installed CLI and account>
codex_effort: <optional Codex reasoning effort: low | medium | high | xhigh>
night: <yes | no>
paths: <comma-separated globs for expected scope, e.g. src/**, tests/**>
protected: <optional comma-separated globs requiring explicit authorization; omit if none>
---

# <Role name>

<!-- One card per role. BEADWORK_ROLE_CARD overrides its path; otherwise use
     BEADWORK_ROLE_DIR/<name>.md when set, then .beads/roles/<name>.md if present,
     with .claude/roles/<name>.md as the compatibility fallback. Night runs reject an
     automatic card path change until it is reviewed on the default branch; a new
     preferred card cannot replace approved policy merely by existing in the worktree.
     A box runs one role
     (BEADWORK_ROLE). The work loop reads the card at the start of every bead and checks
     each PR's changed files against `paths` (advisory) and `protected` (blocking).
     Necessary adjacent fixes may extend expected scope; explain and verify them.
     Existing hard path allowlists must move into the Never section or remain an
     explicit project rule. The night loop requires `night: yes` and uses
     BEADWORK_ENGINE=claude (default) or codex. Claude reads `model` and `effort`;
     Codex reads `codex_model` and `codex_effort`, with no fallback to Claude settings.
     Omit an engine's effort field to use that engine's default.
     Attended sessions treat `effort` as guidance: start them with `claude --effort <level>`.
     Keep the header flat: one `key: value` per line. -->

## Purpose

One paragraph: what this role is for, and what it hands to other roles.

## Never

- Explicit boundaries beyond expected scope. Use these only where crossing the boundary needs the operator's authorization, for example changing a public contract or editing live-data migrations. Existing authorization counts; do not ask twice.
