# claude-shared-skills

A Claude Code plugin marketplace with the skills our projects share. It is kept small on purpose. Only two skill descriptions ever sit in a session's context; everything else loads when someone runs it.

## Plugins

### `beadwork`: Beads + auq work loop

| Skill | Run by | Context cost until used |
|---|---|---|
| `bead`: write or split a work item (Task / Guardrails / Acceptance Criteria) | agent | one description |
| `question`: raise a decision or surprise; day/night handling; provisional defaults | agent | one description |
| `/beadwork:slice [night]`: claim → lease → branch → verify → PR → `in_review`; spikes and night runs | operator or scheduler | none |
| `/beadwork:grill`: one auq batch of every open question; record the answers; tidy memories | operator | none |
| `/beadwork:review-chunk`: digest of PRs awaiting review; closes merged beads | operator | none |

**Hook (SessionStart):** prints `.beads/PRIME.md` (if present), `bd` memories, and one status line: day/night, ready, open questions, in review, away. It is silent in repos without `.beads/`.

### `domain`: ubiquitous language and objectives

| Skill | Run by | Writes |
|---|---|---|
| `/domain:glossary [harvest \| check <path>]` | operator | `docs/domain/glossary.md` |
| `/domain:objectives [sources]` | operator | `docs/requirements/objectives.md` |

## Use it in a project

```bash
claude plugin marketplace add ~/Private/Techyon/claude-shared-skills   # once per machine
claude plugin install beadwork@claude-shared-skills --scope project    # writes .claude/settings.json
claude plugin install domain@claude-shared-skills --scope project
```

**Beads** (server mode, same Dolt server, one database per repo):

```bash
bd init --server --external --server-user beads --prefix <prefix> --skip-agents --skip-hooks --non-interactive --role maintainer
~/Private/Techyon/claude-shared-skills/plugins/beadwork/scripts/configure-beads.sh
```

`--skip-agents --skip-hooks` matters. Our hook and CLAUDE.md replace what `bd setup claude` would write.

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

The Necronia v2 plan maps onto this repo as follows:
- `night-shift` is `/beadwork:slice night`;
- `spike` is `slice/spike.md`;
- its `gs` label plays the role of `must-ask`, which its CLAUDE.md names;
- `BEADWORK_NO_MEMORIES=1` keeps its `--no-memories` rule.
