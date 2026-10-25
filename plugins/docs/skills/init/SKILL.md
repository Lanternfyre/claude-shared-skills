---
name: init
description: Bring a repo onto the documentation standard. Inventory what exists, propose the smallest layout its real content and readers need, move pages only after approval, and seed the landing README and CLAUDE.md rules.
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/docs.py *)
---

# Documentation init

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
- **Never reorganise an established repo without approval.** A template update is not permission to move content.

## 2. Propose

Draft the smallest set of sections this repo's real content and readers need now. For each existing file, give its new home or "stays", and say why. Typical moves:
- loose operational notes → `docs/operate/`;
- design notes → `docs/architecture/`;
- old ADRs → `docs/decisions/`, re-headed by the `adr` skill, with their text unchanged;
- a long README → a short landing page plus the pages it links.

Post the proposal as one auq `tasks` card. Each move is a task with a `required` or `optional` tag. The card's `context` says what a reader will find, where, after the move. Move nothing before approval.

## 3. Apply (after approval)

1. **Move** with `git mv`, so history follows the file.
2. **Landing README:** what this is, how to start, and where to find things, as task-named links: Start, Build, Operate, Reference, Architecture, Decisions. Link only sections that exist.
3. **Section READMEs:** each section gets one, with a purpose paragraph and its pages.
4. **Fix links:** run `docs.py index` if ADRs moved, then `docs.py check` until it passes.
5. **CLAUDE.md:** add the knowledge-map table and the two documentation lines from claude-shared-skills' `templates/CLAUDE.md`, and record the adopted standard (`docs` plugin version).
6. **CI (optional):** copy `docs.py` to `tools/` and run `python3 tools/docs.py check` there.

## 4. Prove it

Run the fresh-agent walkthrough from the `write` skill with one newcomer task and one task for the repo's main reader. Report the structure and reader results separately, plus anything left where it was and why.
