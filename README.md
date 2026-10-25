# claude-shared-skills

A Claude Code plugin marketplace with the skills our projects share. It is kept small on purpose: only three skill descriptions ever sit in a session's context, and everything else loads when someone runs it.

## Plugins

### `beadwork`: the Beads side (live work)

| Skill | Run by | Context cost until used |
|---|---|---|
| `bead`: write or split a work item (Task / Guardrails / Acceptance Criteria); cut a plan into beads | agent | one description |
| `question`: raise a decision or surprise; day/night handling; provisional defaults | agent | one description |
| `/beadwork:slice [night]`: claim → lease → branch → verify → PR → `in_review`; bug flow, spikes, night runs | operator or scheduler | none |
| `/beadwork:grill`: one auq batch of every open question; record the answers; tidy memories | operator | none |
| `/beadwork:review-chunk`: digest of PRs awaiting review; closes merged beads | operator | none |

**Hook (SessionStart):** prints `.beads/PRIME.md` (if present), `bd` memories, and one status line: day/night, ready, open questions, in review, away. It is silent in repos without `.beads/`.

### `docs`: the Git side (durable knowledge)

| Skill | Run by | Writes |
|---|---|---|
| `adr`: new / supersede / review / audit | agent or operator | `docs/adr/ADR-YYYYMMDD-HHMMSS-xxxx-<slug>.md` + `INDEX.md` |
| `/docs:glossary [harvest \| check <path>]` | operator | `docs/domain/glossary.md` |
| `/docs:objectives [sources]` | operator | `docs/requirements/objectives.md` |

`adr` ships `adr.py` (standard library only). It mints ids, rebuilds the index, and with `check` fails on:
- an unknown status;
- one-sided supersede or amend links;
- references to ADRs that don't exist;
- a stale index.

Copy it into a project's `tools/` to run it in pre-commit or CI.

## Use it in a project

```bash
claude plugin marketplace add ~/Private/Techyon/claude-shared-skills   # once per machine
claude plugin install beadwork@claude-shared-skills --scope project    # writes .claude/settings.json
claude plugin install docs@claude-shared-skills --scope project
```

**Beads** (server mode, same Dolt server, one database per repo):

```bash
bd init --server --external --server-user beads --prefix <prefix> --skip-agents --skip-hooks --non-interactive --role maintainer
~/Private/Techyon/claude-shared-skills/plugins/beadwork/scripts/configure-beads.sh
```

`--skip-agents --skip-hooks` matters. Our hook and CLAUDE.md replace what `bd setup claude` would write.

**Personal instructions** (once per machine): copy `templates/personal-CLAUDE.md` to `~/.claude/CLAUDE.md`. It holds the candour and report rules for every project.

**Instructions:** copy `templates/CLAUDE.md` into the project and fill its slots. It holds the knowledge map (what goes to Git docs, what goes to Beads, what goes to `bd remember`), the language rules, and the project's work rules: verify command, PR cap, must-ask categories, who closes beads.

**Environment** (project `.claude/settings.json` `env`, or the box env):

| Variable | Default | Meaning |
|---|---|---|
| `BEADWORK_ROLE` | unset (any) | `role:<x>` label to claim, and `asked-by:<x>` on questions |
| `BEADWORK_TZ` | `Europe/Warsaw` | clock for day/night |
| `BEADWORK_DAY` | `08-23` | day window, in hours |
| `BEADWORK_NIGHT_MIN_READY` | `3` | a night run needs at least this many ready beads to start |
| `BEADWORK_NO_MEMORIES` | `0` | `1` keeps `bd` memories out of session start |

## Deliberately not here

These are project-specific, and the project keeps them:
- **verify:** the project's own fast checks and health rows.
- **demo:** depends on the project's client.
- **clean-room guards:** `bd-guard` and its text lint.
- **identity check, session scheduler, steward workflows:** those live in CI.

General engineering skills are taken from upstream rather than copied here: test-first, deep-module design and prototyping are in [mattpocock/skills](https://github.com/mattpocock/skills). Copies would go stale. From the claude-workbench, three things live on in this repo:
- its grilling lessons, in `question` and `grill`;
- its bug-fix workflow, as `slice/bug.md`;
- its plan cutting, as `bead/cutting.md`.

The Necronia v2 plan maps onto this repo as follows:
- `night-shift` is `/beadwork:slice night`;
- `spike` is `slice/spike.md`;
- its `gs` label plays the role of `must-ask`, which its CLAUDE.md names;
- `BEADWORK_NO_MEMORIES=1` keeps its `--no-memories` rule;
- its ADR numbers (`ADR-0005` style) become timestamp ids.
