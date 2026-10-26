---
name: init
description: Bring a repo onto the documentation standard. Inventory what exists, propose the smallest layout its real content and readers need, preserve established layouts unless reorganization is authorized, and seed the landing README and project instructions.
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/docs.py *)
---

# Documentation init

Use the [host runtime guide](../../runtime.md) for invocation, helper paths and startup context.

Read the `write` skill first; its layout and rules are the target.

## 1. Inventory

- List what exists:
  - the root README;
  - `docs/`;
  - loose `*.md` files at the root and in code folders;
  - ADRs in any format;
  - runbooks in comments or scripts;
  - OpenAPI exports.
- Note who reads them today, and the conventions the repo already follows.
- Preserve an established layout unless the user authorized reorganization. A template update alone does not authorize moving content. Existing authorization counts; do not request it again.

## 2. Propose

Draft the smallest set of sections this repo's real content and readers need now. For each existing file, give its new home or "stays", and say why. Typical moves:
- loose operational notes → `docs/operate/`;
- design notes → `docs/architecture/`;
- old ADRs → `docs/decisions/`, re-headed by the `adr` skill, with their text unchanged;
- a long README → a short landing page plus the pages it links.

If the requested work already authorizes these moves, record the plan and apply it. Otherwise ask about the broad reorganization as one batch through the available question tool or chat, showing what readers will find and where. Improve in-scope content while that decision is pending.

## 3. Apply (after approval)

1. **Move** with `git mv`, so history follows the file.
2. **Landing README:** what this is, how to start, and where to find things, as task-named links: Start, Build, Operate, Reference, Architecture, Decisions. Link only sections that exist.
3. **Section READMEs:** each section gets one, with a purpose paragraph and its pages.
4. **Fix links:** run `docs.py index` if ADRs moved, then `docs.py check` until it passes.
5. **Project instructions:** add the knowledge map and documentation rules to `AGENTS.md` (Codex), `CLAUDE.md` (Claude Code), or their shared source. Use the repository's project template and record the adopted `docs` plugin version. Preserve existing instructions.
6. **CI (optional):** copy `docs.py` to `tools/` and run `python3 tools/docs.py check` there.

## 4. Prove it

Run the fresh-agent walkthrough from the `write` skill with one newcomer task and one task for the repo's main reader. Report the structure and reader results separately, plus anything left where it was and why.
