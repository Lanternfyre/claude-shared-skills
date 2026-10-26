# claude-shared-skills

Shared Beads and documentation skills for **Claude Code and Codex**, with one source for each workflow and helper. Four skills are automatically discoverable (`bead`, `question`, `write`, `adr`); operator procedures load when requested. The [documentation standard](docs/reference/documentation-standard.md) describes the human-facing rules.

- **Start:** [Use it in a project](#use-it-in-a-project).
- **Reference:** [standards and exact facts](docs/reference/README.md), starting with the documentation standard.
- **Decisions:** [why things are the way they are](docs/decisions/README.md).
- **Terms:** [what Beads, auq, grill and the rest mean](#terms).

## Terms

| Term | Meaning |
|---|---|
| Agent box | A homelab pod running a Claude Code or Codex session for one role |
| Work loop | `/beadwork:slice`: claim an authorized outcome, build or delegate, verify and deliver through the project's PR or local integration workflow |
| Operator | The human who decides; in most projects, the one person working with the agents |
| Beads (`bd`) | The issue tracker for live work: beads are work items with dependencies, stored in a Dolt database ([steveyegge/beads](https://github.com/steveyegge/beads)) |
| Decision bead | A bead holding a question for the operator: options, recommendation, default, and the answer once given |
| must-ask / default-ok | Whether an unresolved operator choice needs an answer before dependent work, or may proceed on a reversible default within delegated authority |
| auq | The question inbox: agents post cards, and the operator answers from the terminal or phone |
| Grill | One sitting where the operator answers every open question as one batch of cards |
| Lease | A claimed bead stays claimed only while the agent keeps renewing it |
| Merge gate | A Beads gate per pull request (`gh:pr`, the PR URL) that keeps the bead out of the ready list until the PR merges; such beads carry the `pr-open` label |
| Dolt | The versioned SQL database Beads stores its data in |
| `PRIME.md` | An optional project file in `.beads/` that Beads prints at session start, holding the project's own workflow rules |
| Day / night | Agents ask the operator questions straight away by day; at night they queue them for the morning grill |
| Spike | A bounded investigation comparing plausible alternatives with evidence; any reused code still needs normal delivery checks |
| Night run | An unattended work loop that runs while the operator sleeps |
| home-lab, Necronia v2 | Our two projects that pilot the documentation standard |
| claude-workbench | The earlier tooling repo these skills replace |

## Plugins

### `beadwork`: the Beads side (live work)

| Skill | Run by | Context cost until used |
|---|---|---|
| [`bead`](plugins/beadwork/skills/bead/SKILL.md): write or split a work item (Task / Guardrails / Acceptance Criteria); cut a plan into beads | agent | one description |
| [`question`](plugins/beadwork/skills/question/SKILL.md): raise a decision or surprise; day/night handling; provisional defaults | agent | one description |
| [`/beadwork:slice [night]`](plugins/beadwork/skills/slice/SKILL.md): claim → build or delegate → verify → PR or local integration; bug investigation, spikes, night runs | operator or scheduler | none |
| [`/beadwork:grill`](plugins/beadwork/skills/grill/SKILL.md): one auq batch of every open question; record the answers; tidy memories | operator | none |
| [`/beadwork:review-chunk`](plugins/beadwork/skills/review-chunk/SKILL.md): digest of PRs awaiting review; closes merged beads | operator | none |

**Hook (SessionStart):** prints `.beads/PRIME.md` (if present), `bd` memories, and status: day/night, ready work, questions, review queue, role and away mode. It is silent in repos without `.beads/`. Codex requires hook trust; if startup context is absent, run the same hook explicitly through normal approvals. See the [beadwork runtime guide](plugins/beadwork/runtime.md).

### `docs`: the Git side (durable knowledge)

| Skill | Run by | What it does |
|---|---|---|
| [`write`](plugins/docs/skills/write/SKILL.md): reader-and-question gate, layout, page kinds, prose, ids, contradictions, reader walkthrough | agent | one description |
| [`adr`](plugins/docs/skills/adr/SKILL.md): new / supersede / review / audit, in `docs/decisions/` | agent or operator | one description |
| [`/docs:init`](plugins/docs/skills/init/SKILL.md): adopt the standard; preserve established layouts unless reorganization is authorized | operator | none |
| [`/docs:audit [structure \| drift \| readers]`](plugins/docs/skills/audit/SKILL.md): structure, drift, content and reader tasks, reported separately | operator | none |
| [`/docs:glossary [harvest \| check <path>]`](plugins/docs/skills/glossary/SKILL.md): `docs/domain/glossary.md` | operator | none |
| [`/docs:objectives [sources]`](plugins/docs/skills/objectives/SKILL.md): `docs/product/objectives.md` | operator | none |

[`scripts/docs.py`](plugins/docs/scripts/docs.py) (standard library only) mints ADR and requirement ids and rebuilds the decision index. Its `check` reads every Markdown file Git tracks outside dot-folders and reports structure only, never reader value. It fails on:
- an ADR header problem or a one-sided supersede or amend link;
- a broken relative link or anchor;
- a requirement or objective id defined twice;
- an id mentioned in a page or a code comment that no page defines;
- a stale decision index.

Copy it into a project's `tools/` to run it in pre-commit or CI.

## Maintain the shared skills

Edit the canonical `plugins/<name>/skills/<skill>/SKILL.md` and its references. Host-specific invocation metadata lives beside the skill; helper logic remains shared. Keep `plugin.json` and `.claude-plugin/plugin.json` identity/version aligned, and bump both when behavior changes. [Repository instructions](AGENTS.md) list the commit checks.

```bash
python3 -m unittest discover -s plugins/beadwork/scripts/tests -v
python3 -m unittest discover -s scripts/tests -v
python3 plugins/docs/scripts/docs.py check
claude plugin validate .
claude plugin validate plugins/beadwork
claude plugin validate plugins/docs
```

After refreshing a cached Codex package, start a new session. For a consequential docs change, run the [reader walkthrough](plugins/docs/skills/write/walkthrough.md) as well as the structure check.

## Agent authority and the remaining boundaries

An approved outcome gives the agent room to implement it. It may split or combine beads while preserving every acceptance criterion, make necessary adjacent fixes outside expected paths, delegate implementation, and choose routine internal details. It records consequential choices and evidence without asking for the same authority again. [The work loop](plugins/beadwork/skills/slice/SKILL.md) describes ownership and delivery; [the decision record](docs/decisions/ADR-20261026-134412-fb40-give-agents-authority-within-approved-outcomes.md) explains the trade-offs.

Beads owns execution status; design plans and roadmaps remain in docs. One current progress record replaces repeated handover summaries. Docs checks scale with the change: a small factual edit gets a focused check, while new pages and consequential guidance get a reader walkthrough.

These constraints remain deliberate and should be reviewed when they impede an authorized task:

| Boundary | What it constrains | How to change it |
|---|---|---|
| Approved intent and protected resources | Changing promised behavior, protected paths or security boundaries | Explicit operator authorization; prior authorization counts |
| Ownership and evidence | Concurrent writes to another owner's work, closing unverified or unintegrated work | Coordinate ownership; meet the criteria rather than bypass them |
| Hard timeout recovery | Starting another session in a checkout whose writers may still be active | Confirm delegates stopped, preserve work and reconcile ownership before restarting |
| Critical docs | Substantive architecture, security, operational or external guidance needs owner review | Owner may delegate review; small meaning-preserving repairs need no separate sign-off |
| Night eligibility and budget | Role approval, `night-ok`, cutoff, review cap and session time box | Project/operator config; agents do not grant themselves eligibility |
| Unattended external actions | PR merges, default-branch pushes, live-system changes, secrets and shared data/history | Keep separate from the night runner; explicit project authority is required for local unattended integration |

Expected role paths and review-size targets are advisory. An explicit project hard limit still binds. A reversible default does not authorize a protected action, and silence is never approval.

## Use it in a project

For an already configured project, start work directly. Plans may assume the skills and tracker exist; setup below is a one-time prerequisite, not a phase of every task.

### Claude Code

```bash
claude plugin marketplace add Lanternfyre/claude-shared-skills       # once per machine; clones over SSH
claude plugin install beadwork@claude-shared-skills --scope project    # writes .claude/settings.json
claude plugin install docs@claude-shared-skills --scope project
```

The homelab agent boxes get both plugins without any of this: home-lab's `claude-boxes/common-values.yaml` declares them as managed settings for every box. A machine needs SSH access to the Lanternfyre GitHub org to add the marketplace. To try edits to the skills before pushing, add a local clone instead (`claude plugin marketplace add <path>`); Claude Code then reads the plugins straight from that folder.

### Codex

Codex CLI and desktop can use the same repository marketplace. The installed CLI was verified with version `0.164.0`; installation and initial skill discovery were tested without making a model request.

```bash
codex plugin marketplace add Lanternfyre/claude-shared-skills
codex plugin add beadwork@claude-shared-skills
codex plugin add docs@claude-shared-skills
```

For development, register the absolute path of this checkout instead of the GitHub source. The marketplace name remains `claude-shared-skills` for compatibility; no renamed repository or generated skill mirror is needed. Codex installs a cached copy, so start a new session after installation. Use `codex plugin marketplace upgrade claude-shared-skills` to refresh a Git-backed marketplace, then add the updated plugins. For local changes, re-run `codex plugin add` to refresh the cached package.

Type `$` or `/skills` and choose a skill. Operator procedures (`slice`, `grill`, `review-chunk`, `init`, `audit`, `glossary`, `objectives`) retain explicit-only invocation. The shared pages show Claude slash names; Codex invokes the selected skill with the same argument text. The [docs runtime guide](plugins/docs/runtime.md) and [beadwork runtime guide](plugins/beadwork/runtime.md) explain helper paths and host tools.

Codex's sandbox, approval policy and hook trust still apply. Installing the package does not configure Beads credentials, auq or GitHub access. Attended questions can use the host's question tool or chat. Review and trust the bundled startup hook through Codex when you want it to run automatically; no trust bypass is installed.

The CLI and desktop plugin path is implemented. IDE users can use Codex's standalone-skill discovery, but this repo does not install a separate IDE mirror. Hosted environments still need shell access, the helper files and access to the project's Beads service.

### Project setup shared by both hosts

**Beads** (only for `beadwork`): each repo gets its own database on the shared Beads server, which runs Dolt in server mode. The connection comes from environment variables: `BEADS_DOLT_SERVER_MODE=1`, `BEADS_DOLT_SERVER_HOST`, `BEADS_DOLT_SERVER_PORT`, `BEADS_DOLT_SERVER_USER` and `BEADS_DOLT_SERVER_TLS`. The password comes from `~/.config/beads/credentials`. `<prefix>` is the short name in front of each bead id, for example `skills` gives `skills-1qd`.

```bash
bd init --server --external --server-user beads --prefix <prefix> --skip-agents --skip-hooks --non-interactive --role maintainer
<a clone of this repo>/plugins/beadwork/scripts/configure-beads.sh
```

`--skip-agents --skip-hooks` matters. Our hook and project instructions replace host-specific bootstrap text from `bd setup`. Re-run `configure-beads.sh` (in the main checkout, never a worktree) whenever the session-start line says the repo's Beads settings predate the skills, then commit `.beads/config.yaml`.

If a Beads web board serves the same Dolt server, add the new database to the board's project list: a lower-case database name and a readable display name. The board does not discover databases by itself, so a project left off the list exists but stays invisible there.

**Personal instructions** (once per machine): use [`personal-CLAUDE.md`](templates/personal-CLAUDE.md) in `~/.claude/CLAUDE.md`, or [`personal-AGENTS.md`](templates/personal-AGENTS.md) in `~/.codex/AGENTS.md`. They share one source and hold candour and report rules. Merge with existing personal instructions rather than overwriting them.

**Instructions:** use [`templates/CLAUDE.md`](templates/CLAUDE.md) for Claude Code or [`templates/AGENTS.md`](templates/AGENTS.md) for Codex, and fill its slots. When both hosts use identical rules, keep one real file and symlink the other to it, as this repository does. Preserve existing instructions. It holds:
- the two documentation lines: who the docs are for, and "load the `docs:write` skill before writing a page", with the adopted standard version;
- the knowledge map: what goes to Git docs, what goes to Beads, what goes to `bd remember`;
- the language rules;
- the project's work rules: verification, delivery mode and authority, review-size targets, protected boundaries and who closes beads.

Use `/docs:init` if the repo needs documentation onboarding. Existing layouts and design plans can stay; adoption does not require a documentation migration.

**Roles** (optional): set `BEADWORK_ROLE` per box. A role claims matching beads; with no role, the session can claim any non-human bead. A role card defines purpose, expected paths, protected paths, engine-specific models/effort and night eligibility. Resolve it through `BEADWORK_ROLE_CARD`, `BEADWORK_ROLE_DIR/<role>.md`, an existing `.beads/roles/<role>.md`, or legacy `.claude/roles/<role>.md`. Automatic night-role path changes cannot replace approved policy before review; explicit operator overrides remain available. Start with [the template](templates/role.md).

**Upgrade to beadwork 0.6:** `paths:` now means expected scope. [`role-check.sh`](plugins/beadwork/scripts/role-check.sh) reports adjacent changes without rejecting them; `protected:` globs block even inside expected paths. Move any intended hard allowlist into an explicit project rule or the card's Never section before relying on the new behavior. The checker compares committed changes using the approved policy ref, independently of a stack's diff base. Explicit authorizations are recorded exceptions, not edits made to the card to pass its own check. This is an agent-run check, not CI enforcement.

**Delivery:** `BEADWORK_DELIVERY=pr` uses independent PRs by default, `stack` opts into stacked PRs, and `local` uses the project's authorized local integration workflow. [Delivery modes](plugins/beadwork/skills/slice/delivery.md) explains gates, closure and work awaiting integration. The mode never grants permission to push or merge.

Existing boxes continuing an open stack should set `BEADWORK_DELIVERY=stack` before their next run. The new default does not migrate or flatten existing branches. Keep the current bead's recorded delivery mode when resuming it, and use the configured default for new work.

**Environment** (the box or launching shell; Claude Code also supports project `.claude/settings.json` `env`):

| Variable | Default | Meaning |
|---|---|---|
| `BEADWORK_ENGINE` | `claude` | Night runner: `claude` or `codex` |
| `BEADWORK_ROLE_CARD` | resolved by role | Explicit role card path |
| `BEADWORK_ROLE_DIR` | unset | Role-card directory; otherwise `.beads/roles/` then legacy `.claude/roles/` |
| `BEADWORK_ROLE` | unset (any) | `role:<x>` label to claim, and `asked-by:<x>` on questions |
| `BEADWORK_DELIVERY` | `pr` | `pr`, `stack`, or `local`; mechanics, not push/merge authorization |
| `BEADWORK_STATE_DIR` | `~/.local/state/beadwork` | night-run logs and reviewed role-card cache |
| `BEADWORK_TZ` | `Europe/Warsaw` | clock for day/night |
| `BEADWORK_DAY` | `08-23` | day window, in hours |
| `BEADWORK_NIGHT_CUTOFF` | `06:00` | the night loop starts no new bead from this time until the day ends |
| `BEADWORK_BEAD_TIMEBOX` | `2h` | how long one night session may run before the loop parks its bead |
| `BEADWORK_NO_MEMORIES` | `0` | `1` keeps `bd` memories out of session start |

### Night runs

A bead is worked overnight only when all of this holds:
- **The box has a role** (`BEADWORK_ROLE`) whose card says `night: yes`. Claude uses `model`/`effort`; Codex uses `codex_model`/`codex_effort`. Configure a model supported by that engine and account; effort is optional. No model aliases or effort levels are translated between engines.
- **The bead carries `role:<role>` and `night-ok`.** The operator grants night eligibility. It must be ready, or in stack mode blocked only by verified implementation work in its own stack. Epics, decisions, `human` and closed-unmerged PR beads are not new implementation work.
- **The project has a verify command:** `bd config set custom.beadwork-verify "<command>"`. Optionally set `custom.beadwork-review-cap` (default 12).

The loop is [`scripts/night-run.sh`](plugins/beadwork/scripts/night-run.sh), run inside the box in the project's checkout. A homelab scheduled job will start it at 23:05 (bead `skills-wp1.6`); until then, start it by hand. `--dry-run` shows what it would do now, and why. Between beads it stops starting new work when:
1. it is between 06:00 and 23:00 (no new bead after the 06:00 cutoff);
2. pending review reaches the cap (`pr-open` beads, or `integration-pending` in local mode);
3. the project has no verify command;
4. the box has no role, the card is missing/not night-enabled, or its selected engine has no model or an invalid effort;
5. no `night-ok` bead is left for the role;
6. a session hit the usage limit;
7. two sessions in a row failed, or any session ran past its hard time box and needs recovery;
8. the time box (`BEADWORK_BEAD_TIMEBOX`) is invalid, the engine is not `claude`/`codex`, or delivery is not `pr`/`stack`/`local`.

Set `BEADWORK_ENGINE=codex` in a Codex box or launching shell and provide `codex_model` in its approved role card. The runner uses `codex exec` with workspace-write sandboxing, normal approvals and a final-message file; it never bypasses hook trust or approvals. Engine behavior was verified with stub processes; a live unattended model run remains unverified.

Each session gets a park-by time, a quarter of the time box before it ends. After it, the session parks its bead before starting the finish steps, and a later session continues it.

It also stops when Beads is unreachable. A GitHub sweep failure leaves uncertain review work alone and permits independently ready work. Local delivery skips GitHub entirely. A timed-out session does not cause the runner to guess which claim to release: inspect its log and checkout, confirm delegates stopped, and reconcile ownership or let the lease expire. When it stops, it files a **morning-summary** bead: why it stopped, plus one line per session. The morning card, `/beadwork:grill morning`, posts these with the night's held questions as one card when the day starts. A homelab job will run it at 08:00 (bead `skills-wp1.6`); until then, run it by hand. Away mode does not stop nights: it only holds questions, as at night.

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
