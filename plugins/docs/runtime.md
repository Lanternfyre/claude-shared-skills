# Running docs skills in Claude Code and Codex

Both hosts load the same documentation skills and `scripts/docs.py`. Use the host's shell, question and delegation tools; a missing optional question plugin or reader agent does not require installing one to make an ordinary edit.

`<plugin-root>` is the absolute plugin directory containing the loaded `skills/` tree, `scripts/` and this page. From the skill directory, move up through `skills/` to that plugin directory. Replace it with the actual installed path before running a command, and quote paths. Run `docs.py` from the project root, or pass its supported `--root` option. Do not assume the source checkout or another plugin's environment variable is the installed docs plugin.

In Claude Code, operator procedures use `/docs:init`, `/docs:audit`, `/docs:glossary` and `/docs:objectives`. In Codex, choose the corresponding skill using `$` or `/skills`, or ask for it by name. Slash references in shared pages identify those procedures. Claude's `$ARGUMENTS` is the invocation's argument text in Codex. The write and ADR skills remain discoverable; the operator procedures retain explicit-only invocation in both hosts.

Project instructions live in `AGENTS.md` for Codex or `CLAUDE.md` for Claude Code. A symlink can share their rules. Keep established layouts and instruction sources; adoption does not require inventing a second rulebook.

For reader walkthroughs use the available read-only delegation tool, or report a direct check when delegation is unavailable. If a decision needs the operator, use auq when installed or the session's question channel/chat otherwise. Preserve existing answers and authorization. Record pending decisions in the project's tracker; installing this plugin does not require Beads.
