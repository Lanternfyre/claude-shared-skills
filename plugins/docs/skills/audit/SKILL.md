---
name: audit
description: Audit a repo's documentation. Structural health, drift between docs, decisions and code, content problems, and the operator's own reader walkthrough, each reported separately. Run at milestones or when docs feel untrustworthy.
argument-hint: "[structure | drift | readers]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/docs.py *)
---

# Documentation audit

Use the [host runtime guide](../../runtime.md) for invocation, helper paths and startup context.

With no argument, run all four parts. Read the `write` skill first: its layout, critical pages and contradiction rules apply here.

## 1. Structure

`python3 "<plugin-root>/scripts/docs.py" check` covers ADR headers and links, relative links and anchors, and ids defined once and resolving (code comments included). Also list:
- pages no link from the root README reaches;
- section folders with no `README.md`.

## 2. Drift

Compare what the docs claim with the code, config, migrations and OpenAPI exports. Start with the riskiest areas: security, public contracts, operations, then data. Give each topic one outcome:
- **consistent:** nothing to do;
- **update-safe:** the docs are factually wrong about what is built. Fix them in a PR;
- **implementation bug:** clear approved intent is not implemented. File or fix the bug within scope; preserve the requirement and ADR history;
- **review-required:** authoritative intent is ambiguous, or fixing the conflict would change it. File a decision (the `write` skill's contradiction format);
- **unknown:** you could not check it. Say what is missing.

A security area or public contract with no docs at all is a **coverage gap**, never "consistent".

## 3. Content

Look for:
- the same fact stated on two pages;
- a page mixing kinds, such as a tutorial that turns into a reference table;
- plans written as if built;
- an "Implemented" claim with no evidence;
- critical pages with no owner path;
- diagrams with no prose;
- template filler: TBD, generic text, invented examples.

## 4. Readers (the operator)

Prepare 3–5 tasks, at least one for each reader the project has: newcomer, change, operate, external user. The `write` skill's [walkthrough.md](../write/walkthrough.md) has examples.
- Run the fresh-agent walkthrough first, and fix the dead ends it finds.
- Then ask the operator through the available question channel, in one batch: done (yes or no), where they got stuck, and anything that seemed wrong. Report human review as pending while you continue independent fixes.
- The operator follows the tasks from the rendered README in the Git host, not with an agent.

## Report

1. **Verdict:** one line, e.g. "Structure passes; 2 of 4 reader tasks fail; 1 contradiction needs a decision."
2. **Structure:** problems found by `docs.py check` and the reachability checks.
3. **Drift:** each topic and its outcome, with the decision beads filed.
4. **Content:** the problems found.
5. **Readers:** each task, done or not, and the obstacles.
6. **What I need from you:** only when the operator must act.

Never compute a single score, and never let a passing structure check stand in for reader results. File fixes as beads (`topic:docs`).
