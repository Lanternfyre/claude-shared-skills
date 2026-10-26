---
role: <name>
model: <a `claude --model` value, e.g. opus or sonnet>
effort: <optional: a `claude --effort` level, low | medium | high | xhigh | max; e.g. high for building, max for planning and spikes>
night: <yes | no>
paths: <comma-separated globs this role may change, e.g. src/**, tests/**>
---

# <Role name>

<!-- One card per role, at .claude/roles/<name>.md in the project. A box runs one role
     (BEADWORK_ROLE). The work loop reads the card at the start of every bead and checks
     each PR's changed files against `paths`; the night loop reads `model`, `effort` and
     `night`, and passes `effort` to each session (leave it out for claude's default).
     Attended sessions treat `effort` as guidance: start them with `claude --effort <level>`.
     Keep the header flat: one `key: value` per line. -->

## Purpose

One paragraph: what this role is for, and what it hands to other roles.

## Never

- What this role must never do, on top of the project's own rules. For example: "never edit migrations", "never change the public API".
