# claude-shared-skills

A Claude Code plugin marketplace with the skills our projects share, and the [documentation standard](docs/reference/documentation-standard.md) they enforce. It is kept small on purpose: only four skill descriptions ever sit in a session's context, and everything else loads when someone runs it. A live session on 2026-10-25 confirmed the model sees only those four. `claude plugin details` estimates about 880 always-on tokens, but that figure also counts the operator-only skills.

- **Start:** [Use it in a project](#use-it-in-a-project).
- **Reference:** [standards and exact facts](docs/reference/README.md), starting with the documentation standard.
- **Decisions:** [why things are the way they are](docs/decisions/README.md).
- **Terms:** [what Beads, auq, grill and the rest mean](#terms).

## Terms

| Term | Meaning |
|---|---|
| Agent box | A homelab pod running one Claude Code session for one role, reachable by Remote Control |
| Work loop | `/beadwork:slice`: close merged work, claim a bead, build it, open its PR behind a merge gate |
| Operator | The human who decides; in most projects, the one person working with the agents |
| Beads (`bd`) | The issue tracker for live work: beads are work items with dependencies, stored in a Dolt database ([steveyegge/beads](https://github.com/steveyegge/beads)) |
| Decision bead | A bead holding a question for the operator: options, recommendation, default, and the answer once given |
| must-ask / default-ok | Whether an agent may go ahead on the default when the operator hasn't answered |
| auq | The question inbox: agents post cards, and the operator answers from the terminal or phone |
| Grill | One sitting where the operator answers every open question as one batch of cards |
| Lease | A claimed bead stays claimed only while the agent keeps renewing it |
| Merge gate | A Beads gate per pull request (`gh:pr`, the PR URL) that keeps the bead out of the ready list until the PR merges; such beads carry the `pr-open` label |
| Dolt | The versioned SQL database Beads stores its data in |
| `PRIME.md` | An optional project file in `.beads/` that Beads prints at session start, holding the project's own workflow rules |
| Day / night | Agents ask the operator questions straight away by day; at night they queue them for the morning grill |
| Spike | A time-boxed experiment comparing 2–3 variants by measurement; its code never merges |
| Night run | An unattended work loop that runs while the operator sleeps |
| home-lab, Necronia v2 | Our two projects that pilot the documentation standard |
| claude-workbench | The earlier tooling repo these skills replace |

## Plugins

### `beadwork`: the Beads side (live work)

| Skill | Run by | Context cost until used |
|---|---|---|
| [`bead`](plugins/beadwork/skills/bead/SKILL.md): write or split a work item (Task / Guardrails / Acceptance Criteria); cut a plan into beads | agent | one description |
| [`question`](plugins/beadwork/skills/question/SKILL.md): raise a decision or surprise; day/night handling; provisional defaults | agent | one description |
| [`/beadwork:slice [night]`](plugins/beadwork/skills/slice/SKILL.md): close merged work → claim → lease → branch → verify → PR behind a merge gate; one PR stack per box, bug flow, spikes, night runs | operator or scheduler | none |
| [`/beadwork:grill`](plugins/beadwork/skills/grill/SKILL.md): one auq batch of every open question; record the answers; tidy memories | operator | none |
| [`/beadwork:review-chunk`](plugins/beadwork/skills/review-chunk/SKILL.md): digest of PRs awaiting review; closes merged beads | operator | none |

**Hook (SessionStart):** prints `.beads/PRIME.md` (if present), `bd` memories, and one status line: day/night, ready, open questions, PRs in review, away. It is silent in repos without `.beads/`.

### `docs`: the Git side (durable knowledge)

| Skill | Run by | What it does |
|---|---|---|
| [`write`](plugins/docs/skills/write/SKILL.md): reader-and-question gate, layout, page kinds, prose, ids, contradictions, reader walkthrough | agent | one description |
| [`adr`](plugins/docs/skills/adr/SKILL.md): new / supersede / review / audit, in `docs/decisions/` | agent or operator | one description |
| [`/docs:init`](plugins/docs/skills/init/SKILL.md): bring a repo onto the standard; moves only after approval | operator | none |
| [`/docs:audit [structure \| drift \| readers]`](plugins/docs/skills/audit/SKILL.md): structure, drift, content and reader tasks, reported separately | operator | none |
| [`/docs:glossary [harvest \| check <path>]`](plugins/docs/skills/glossary/SKILL.md): `docs/domain/glossary.md` | operator | none |
| [`/docs:objectives [sources]`](plugins/docs/skills/objectives/SKILL.md): `docs/product/objectives.md` | operator | none |

[`scripts/docs.py`](plugins/docs/scripts/docs.py) (standard library only) mints ADR and requirement ids and rebuilds the decision index. Its `check` reports structure only, never reader value. It fails on:
- an ADR header problem or a one-sided supersede or amend link;
- a broken relative link or anchor;
- a requirement or objective id defined twice;
- an id mentioned in a page or a code comment that no page defines;
- a stale decision index.

Copy it into a project's `tools/` to run it in pre-commit or CI.

## Use it in a project

```bash
claude plugin marketplace add Lanternfyre/claude-shared-skills       # once per machine; clones over SSH
claude plugin install beadwork@claude-shared-skills --scope project    # writes .claude/settings.json
claude plugin install docs@claude-shared-skills --scope project
```

The homelab agent boxes get both plugins without any of this: home-lab's `claude-boxes/common-values.yaml` declares them as managed settings for every box. A machine needs SSH access to the Lanternfyre GitHub org to add the marketplace. To try edits to the skills before pushing, add a local clone instead (`claude plugin marketplace add <path>`); Claude Code then reads the plugins straight from that folder.

**Beads** (only for `beadwork`): each repo gets its own database on the shared Beads server, which runs Dolt in server mode. The connection comes from environment variables: `BEADS_DOLT_SERVER_MODE=1`, `BEADS_DOLT_SERVER_HOST`, `BEADS_DOLT_SERVER_PORT`, `BEADS_DOLT_SERVER_USER` and `BEADS_DOLT_SERVER_TLS`. The password comes from `~/.config/beads/credentials`. `<prefix>` is the short name in front of each bead id, for example `skills` gives `skills-1qd`.

```bash
bd init --server --external --server-user beads --prefix <prefix> --skip-agents --skip-hooks --non-interactive --role maintainer
<a clone of this repo>/plugins/beadwork/scripts/configure-beads.sh
```

`--skip-agents --skip-hooks` matters. Our hook and CLAUDE.md replace what `bd setup claude` would write. Re-run `configure-beads.sh` (in the main checkout, never a worktree) whenever the session-start line says the repo's Beads settings predate the skills, then commit `.beads/config.yaml`.

If a Beads web board serves the same Dolt server, add the new database to the board's project list: a lower-case database name and a readable display name. The board does not discover databases by itself, so a project left off the list exists but stays invisible there.

**Personal instructions** (once per machine): copy [`templates/personal-CLAUDE.md`](templates/personal-CLAUDE.md) to `~/.claude/CLAUDE.md`. It holds the candour and report rules for every project.

**Instructions:** copy [`templates/CLAUDE.md`](templates/CLAUDE.md) into the project and fill its slots. It holds:
- the two documentation lines: who the docs are for, and "load the `docs:write` skill before writing a page", with the adopted standard version;
- the knowledge map: what goes to Git docs, what goes to Beads, what goes to `bd remember`;
- the language rules;
- the project's work rules: verify command, PR cap, must-ask categories, who closes beads.

Then run `/docs:init` to bring existing docs onto the layout.

**Roles** (optional): an agent box runs one role, set as `BEADWORK_ROLE` in that box's own homelab values (`extraEnv`). Set per project instead, every box would get the same role. A box with a role claims only beads labelled `role:<role>`; a box without one claims any bead. Each role has a card at `.claude/roles/<role>.md`, copied from [`templates/role.md`](templates/role.md): purpose, allowed paths, model, whether it may run at night, and a never list. The [work loop](plugins/beadwork/skills/slice/SKILL.md) reads the card at the start of every bead. Before opening a PR it runs [`role-check.sh`](plugins/beadwork/scripts/role-check.sh), which lists files outside the card's paths, and opens no PR until the list is empty. This is a check the agent runs, not CI: nothing yet catches a PR opened by other means.

**Environment** (project `.claude/settings.json` `env`, or the box env):

| Variable | Default | Meaning |
|---|---|---|
| `BEADWORK_ROLE` | unset (any) | `role:<x>` label to claim, and `asked-by:<x>` on questions |
| `BEADWORK_TZ` | `Europe/Warsaw` | clock for day/night |
| `BEADWORK_DAY` | `08-23` | day window, in hours |
| `BEADWORK_NIGHT_CUTOFF` | `06:00` | the night loop starts no new bead from this time until the day ends |
| `BEADWORK_BEAD_TIMEBOX` | `2h` | how long one night session may run before the loop parks its bead |
| `BEADWORK_NO_MEMORIES` | `0` | `1` keeps `bd` memories out of session start |

### Night runs

A bead is worked overnight only when all of this holds:
- **The box has a role** (`BEADWORK_ROLE`), and that role's card says `night: yes` and names a `model`.
- **The bead carries `role:<role>` and `night-ok`.** You add these: `bd label add <id> role:<role>`, then `bd label add <id> night-ok`. It must be ready, or blocked only by beads in the box's own [PR stack](plugins/beadwork/skills/slice/stack.md). Epics, decisions and `human` beads never run.
- **The project has a verify command:** `bd config set custom.beadwork-verify "<command>"`. Optionally set `custom.beadwork-review-cap` (default 12).

The loop is [`scripts/night-run.sh`](plugins/beadwork/scripts/night-run.sh), run inside the box in the project's checkout. A homelab scheduled job will start it at 23:05 (bead `skills-wp1.6`); until then, start it by hand. `--dry-run` shows what it would do now, and why. Between beads it stops starting new work when:
1. it is between 06:00 and 23:00 (no new bead after the 06:00 cutoff);
2. PRs in review reach the review cap;
3. the project has no verify command;
4. the box has no role, the card is missing, or the card says `night: no` or names no model;
5. no `night-ok` bead is left for the role;
6. a session hit the usage limit;
7. two sessions in a row failed or ran past the two-hour time box.

It also stops when Beads is unreachable. When it stops, it files a **morning-summary** bead: why it stopped, plus one line per session. A morning card bundling these with the night's held questions is still to come (bead `skills-wp1.5`). Away mode does not stop nights: it only holds questions, as at night.

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

The Necronia v2 plan will map onto this repo as follows. This is planned, not done, and tracked in Beads:
- `night-shift` is `/beadwork:slice night`;
- `spike` is `slice/spike.md`;
- its `gs` label plays the role of `must-ask`, which its CLAUDE.md names;
- `BEADWORK_NO_MEMORIES=1` keeps its `--no-memories` rule;
- its ADR numbers (`ADR-0005` style) become timestamp ids;
- its `rewrite/` docs home meets the documentation standard's layout in the Necronia pilot.
