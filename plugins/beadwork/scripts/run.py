#!/usr/bin/env python3
"""One owned Beads worker, using native Claude/Codex conversations. Stdlib only."""
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

PLUGIN = Path(__file__).resolve().parents[1]
RESULT_KEYS = {'bead', 'outcome', 'ref', 'next', 'delegates_stopped', 'checkpoint'}
OUTCOMES = {'working', 'pr', 'review', 'complete', 'parked', 'blocked'}


class StopRun(Exception):
    pass


def duration(value):
    match = re.fullmatch(r'(\d+(?:\.\d+)?)([smhd]?)', value)
    if not match:
        raise argparse.ArgumentTypeError('use a positive duration, e.g. 30m or 2h')
    seconds = float(match[1]) * {'': 1, 's': 1, 'm': 60, 'h': 3600, 'd': 86400}[match[2]]
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError('duration must be positive')
    return seconds


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine', choices=('claude', 'codex'), required=True)
    p.add_argument('--model', default=os.environ.get('BEADWORK_MODEL'))
    p.add_argument('--effort', default=os.environ.get('BEADWORK_EFFORT'))
    p.add_argument('--mode', choices=('attended', 'unattended'), default='attended')
    p.add_argument('--delivery', choices=('auto', 'pr', 'stack', 'local'), default=os.environ.get('BEADWORK_DELIVERY', 'auto'))
    p.add_argument('--role', default=os.environ.get('BEADWORK_ROLE') or None)
    p.add_argument('--label', action='append', default=[])
    p.add_argument('--bead', help='one authorized bead, including existing PR maintenance')
    p.add_argument('--time-budget', type=duration, default=7200)
    p.add_argument('--max-beads', type=int, default=0, help='0 keeps working through the authorized queue')
    p.add_argument('--review-cap', type=int, default=int(os.environ.get('BEADWORK_REVIEW_CAP', '12')))
    p.add_argument('--heartbeat', type=float, default=30)
    p.add_argument('--command-timeout', type=float, default=10)
    p.add_argument('--dry-run', action='store_true', help='inspect queue; no claim/model/state writes')
    p.add_argument('--recover', action='store_true', help='reconcile saved ownership/checkpoint and stopped writers before resuming')
    p.add_argument('--new-budget', action='store_true', help='recover checkpointed work with an explicitly new time budget')
    p.add_argument('--fresh-session', action='store_true', help='with --recover or --new-budget, replace an unavailable conversation after recovery checks')
    p.add_argument('--install-guard', action='store_true', help='only install the legacy unattended pre-push guard')
    p.add_argument('--legacy-night-schedule', action='store_true', help=argparse.SUPPRESS)
    return p


def atomic_json(path, data):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


class Runner:
    def __init__(self, args):
        self.args = args
        self.root = Path.cwd().resolve()
        self.deadline = time.time() + args.time_budget
        self.monotonic_deadline = time.monotonic() + args.time_budget
        self.env = os.environ.copy()
        self.state = {}
        self.path = None
        self.bead = self.checkpoint = self.process = None
        self.interrupted = threading.Event()
        self.heartbeat_stop = threading.Event()
        self.lost = None
        self.lease_active = False
        self.seen_session = False
        self.seen_completed = False
        self.reconciled_handoff = False
        self.reconstruct_checkpoint = False
        self.fresh_claude_session = False
        self.contended = set()

    def command(self, argv):
        remaining = min(self.deadline - time.time(), self.monotonic_deadline - time.monotonic())
        if remaining <= 0:
            raise StopRun('fixed run deadline reached')
        process = None
        try:
            process = subprocess.Popen(argv, cwd=self.root, env=self.env, text=True,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, start_new_session=True)
            output, errors = process.communicate(timeout=min(self.args.command_timeout, remaining))
        except (OSError, subprocess.TimeoutExpired) as error:
            if process is not None:
                self.stop_group(process)
            raise StopRun(f'{argv[0]} unavailable or timed out: {error}') from error
        if process.returncode:
            raise StopRun(f'{argv[0]} failed ({process.returncode}): {errors.strip()}')
        return output

    def bd(self, *args, readonly=False):
        output = self.command(['bd'] + (['--readonly'] if readonly else []) + list(args))
        try:
            return json.loads(output)
        except (ValueError, TypeError) as error:
            raise StopRun('invalid Beads JSON; ownership must be reconciled') from error

    def show(self, bead=None):
        bead = bead or self.bead
        value = self.bd('show', bead, '--json', readonly=True)
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        if not isinstance(value, dict) or value.get('id') != bead:
            raise StopRun(f'Beads did not return exact bead {bead}')
        metadata = value.get('metadata') or {}
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        if not isinstance(metadata, dict):
            raise StopRun('invalid bead metadata')
        value['metadata'] = metadata
        if not isinstance(value.get('labels') or [], list):
            raise StopRun('invalid bead labels')
        return value

    def save(self, **values):
        self.state.update(values)
        atomic_json(self.path, self.state)

    @staticmethod
    def utc(value):
        return datetime.fromtimestamp(value, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    def initialize(self):
        directory = Path(self.command(['git', 'rev-parse', '--absolute-git-dir']).strip()) / 'beadwork'
        directory.mkdir(exist_ok=True)
        self.path = directory / 'run.json'
        self.lock = (directory / 'run.lock').open('a+')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise StopRun('another worker holds this checkout lock') from error
        previous = None
        if self.path.exists():
            try:
                previous = json.loads(self.path.read_text())
            except (ValueError, OSError) as error:
                raise StopRun(f'corrupted run state; reconcile {self.path}') from error
            if not isinstance(previous, dict) or not isinstance(previous.get('recovery_required'), bool):
                raise StopRun(f'invalid run state; reconcile {self.path}')
            required = {'version', 'run_id', 'actor', 'checkout', 'engine', 'deadline', 'session_id',
                        'bead', 'phase', 'completed', 'turn', 'checkpoint', 'worker_pgid', 'config'}
            if (not required <= previous.keys() or previous['version'] != 1
                    or not isinstance(previous['run_id'], str)
                    or not re.fullmatch(r'[a-f0-9]{32}', previous['run_id'])
                    or previous['actor'] != 'beadwork-' + previous['run_id']
                    or not isinstance(previous['deadline'], (int, float))
                    or not math.isfinite(previous['deadline'])
                    or not isinstance(previous['config'], dict)
                    or (previous['session_id'] is not None and
                        (not isinstance(previous['session_id'], str) or
                         not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', previous['session_id'])))
                    or (previous['bead'] and not previous['recovery_required'] and previous['phase'] != 'paused')):
                raise StopRun(f'invalid run state; reconcile {self.path}')
        names = ('model', 'effort', 'mode', 'delivery', 'role', 'label', 'bead', 'max_beads')
        # Old preclaim failures held no bead and started no writer. They are safe
        # to retry as new runs; never strand a queue read behind a recovery gate.
        no_claim = bool(previous and not previous.get('bead') and
                        self.writers_stopped(previous.get('worker_pgid')))
        if no_claim:
            previous['recovery_required'] = False
        resume = (self.args.recover or self.args.new_budget or
                  bool(previous and previous.get('phase') == 'paused' and previous.get('bead')))
        if no_claim:
            resume = False
        if self.args.fresh_session and not resume:
            raise StopRun('fresh-session recovery needs saved exact-bead state')
        if resume:
            if not previous or not previous.get('bead'):
                raise StopRun('no recoverable exact-bead state; reconcile saved run manually')
            if previous.get('checkout') != str(self.root) or previous.get('engine') != self.args.engine:
                raise StopRun('saved run checkout/engine differs')
            if ((self.args.bead and self.args.bead != previous['bead'])
                    or (self.args.role and self.args.role != previous['config']['role'])
                    or (self.args.label and self.args.label != previous['config']['label'])):
                raise StopRun('saved work differs from the requested bead/role/labels; finish or reconcile the saved claim first')
            self.state = previous
            old_deadline = previous['deadline']
            self.deadline = time.time() + self.args.time_budget if self.args.new_budget else old_deadline
            self.monotonic_deadline = time.monotonic() + max(0, self.deadline - time.time())
            if self.deadline <= time.time():
                raise StopRun('saved run deadline expired; --new-budget explicitly starts a new budget after recovery checks')
            self.bead, self.checkpoint = previous['bead'], previous['checkpoint']
            for name in names:
                setattr(self.args, name, previous['config'][name])
            if not self.writers_stopped(previous.get('worker_pgid')):
                raise StopRun('saved worker still has live processes; stop writers before recovery')
        else:
            if previous and previous['recovery_required']:
                raise StopRun(f'recovery required; inspect {self.path}; --recover checks exact ownership, checkpoint and stopped writers')
            token = uuid.uuid4().hex
            self.state = {
                'version': 1, 'run_id': token, 'actor': f'beadwork-{token}', 'checkout': str(self.root),
                'engine': self.args.engine, 'deadline': self.deadline, 'session_id': None, 'bead': None,
                'phase': 'ready', 'recovery_required': False, 'completed': 0, 'turn': 0,
                'checkpoint': None, 'worker_pgid': None, 'handled': [],
                'config': {name: getattr(self.args, name) for name in names},
            }
        self.env.update({'BEADS_ACTOR': self.state['actor'], 'BEADWORK_MANAGED': '1',
                         'BEADWORK_ENGINE': self.args.engine,
                         'BEADWORK_MODE': self.args.mode, 'BEADWORK_DELIVERY': self.args.delivery,
                         'BEADWORK_PLUGIN_ROOT': str(PLUGIN), 'BEADWORK_RUN_STATE': str(self.path),
                         'BEADWORK_RUN_DEADLINE': self.utc(self.deadline),
                         'BEADWORK_PARK_BY': self.utc(self.deadline - min(120, self.args.time_budget / 4))})
        if self.args.role:
            self.env['BEADWORK_ROLE'] = self.args.role
        else:
            self.env.pop('BEADWORK_ROLE', None)
        if resume:
            current = self.show()
            if current.get('status') == 'in_progress' and current.get('assignee') == self.state['actor']:
                # A crash can precede the very checkpoint it was supposed to
                # write. Exact ownership and stopped writers permit recovery;
                # the worker must reconstruct progress before implementation.
                self.reconstruct_checkpoint = not self.has_checkpoint(current)
            elif (current.get('assignee') and current['assignee'] != self.state['actor']
                    and not previous.get('work_started', previous['turn'] > 0)):
                self.contended.add(self.bead)
                self.state['bead'] = self.bead = None
            elif not self.has_checkpoint(current):
                raise StopRun('released handoff recovery needs saved notes and its exact checkpoint')
            elif (self.args.new_budget and current.get('status') == 'open'
                    and not current.get('assignee') and self.allowed(current)):
                ready = self.bd('ready', '--limit', '0', '--json', readonly=True)
                if not isinstance(ready, list) or not any(isinstance(row, dict) and row.get('id') == self.bead for row in ready):
                    raise StopRun('saved bead is not independently ready; resolve its current blockers before reclaiming')
                self.save(deadline=self.deadline, prior_deadline=old_deadline)
                self.claim(current)
            elif (current.get('status') in ('open', 'blocked', 'closed')
                    and current.get('assignee') in (None, '', self.state['actor'] if current.get('status') == 'closed' else None)):
                self.state['handled'] = self.state.get('handled', []) + [self.bead]
                self.bead = None
                self.reconciled_handoff = True
                self.state['bead'] = None
            elif self.bead:
                self.require_owned(current)
            self.lease_active = bool(self.bead)
            if self.args.new_budget:
                self.state['prior_deadline'] = old_deadline
            if self.args.fresh_session and self.bead:
                # An allocated native ID need not have been persisted by a CLI
                # that failed during startup. Replacing it is an explicit choice
                # after ownership and stopped-writer checks, never a blind retry.
                self.state.update(session_id=None, session_spawned=False)
                self.reconstruct_checkpoint = True
        self.save(phase='owned' if self.bead else 'ready', worker_pgid=None, deadline=self.deadline,
                  recovery_required=bool(self.bead), reconstruct_checkpoint=self.reconstruct_checkpoint)

    @staticmethod
    def writers_stopped(pgid):
        if not pgid:
            return True
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return True
        # A killed delegate can remain a zombie until its host reaps it. Zombies
        # cannot write and must not turn evidence-based recovery into a human gate.
        proc = Path('/proc')
        if not proc.exists():
            return False
        for entry in proc.iterdir():
            if not entry.name.isdigit():
                continue
            try:
                fields = (entry / 'stat').read_text().rsplit(')', 1)[1].split()
                if int(fields[2]) == pgid and fields[0] != 'Z':
                    return False
            except (OSError, ValueError, IndexError):
                continue
        return True

    def require_owned(self, value):
        if value.get('status') != 'in_progress' or value.get('assignee') != self.state['actor']:
            raise StopRun(f'ownership lost for {self.bead}; do not release or write another owner\'s bead')

    def has_checkpoint(self, value):
        return (isinstance(self.checkpoint, str) and bool(self.checkpoint)
                and value.get('metadata', {}).get('beadwork_checkpoint') == self.checkpoint
                and isinstance(value.get('notes'), str) and bool(value['notes'].strip()))

    def review_count(self):
        ids = set()
        for label in ('pr-open', 'integration-pending'):
            rows = self.bd('list', '--label', label, '--limit', '0', '--json', readonly=True)
            if not isinstance(rows, list) or any(not isinstance(row, dict) or not row.get('id') for row in rows):
                raise StopRun('invalid review queue')
            ids.update(row['id'] for row in rows if row.get('status') != 'closed')
        return len(ids)

    def allowed(self, value, maintenance=False):
        labels = value.get('labels') or []
        return (isinstance(labels, list) and 'human' not in labels and 'pr-closed' not in labels
                and (maintenance or 'pr-open' not in labels)
                and value.get('issue_type') not in ('epic', 'decision')
                and (not self.args.role or f'role:{self.args.role}' in labels)
                and all(label in labels for label in self.args.label))

    def candidate(self):
        if self.args.legacy_night_schedule:
            now = os.environ.get('BEADWORK_NOW') or datetime.now(ZoneInfo(os.environ.get('BEADWORK_TZ', 'Europe/Warsaw'))).strftime('%H:%M')
            cutoff = os.environ.get('BEADWORK_NIGHT_CUTOFF', '06:00')
            end = os.environ.get('BEADWORK_DAY', '08-23').split('-')[1] + ':00'
            if cutoff <= now < end:
                return None, 'legacy night cutoff'
        if self.args.bead:
            known = self.show(self.args.bead)
            if (known['id'] not in self.contended and 'pr-open' in (known.get('labels') or []) and self.allowed(known, maintenance=True)
                    and known.get('status') in ('open', 'blocked') and not known.get('assignee')):
                return known, 'existing PR maintenance'
            if (known['id'] not in self.contended and 'integration-pending' in (known.get('labels') or [])
                    and self.allowed(known, maintenance=True) and known.get('status') in ('open', 'blocked')
                    and not known.get('assignee')):
                dependencies = known.get('dependencies') or []
                if (not isinstance(dependencies, list) or
                        any(not isinstance(dep, dict) or
                            (dep.get('dependency_type') == 'blocks' and dep.get('status') != 'closed')
                            for dep in dependencies)):
                    return None, 'integration-pending bead still has unresolved blockers'
                return known, 'existing local integration maintenance'
        reviews = self.review_count()
        if reviews >= self.args.review_cap:
            return None, f'review cap reached ({reviews}/{self.args.review_cap})'
        args = ['ready', '--limit', '0', '--exclude-type', 'epic,decision',
                '--exclude-label', 'human,pr-open,pr-closed', '--json']
        for label in ([f'role:{self.args.role}'] if self.args.role else []) + self.args.label:
            args += ['--label', label]
        rows = self.bd(*args, readonly=True)
        if not isinstance(rows, list):
            raise StopRun('invalid ready queue')
        for value in rows:
            if (isinstance(value, dict) and value.get('id') and self.allowed(value)
                    and value.get('status') == 'open' and not value.get('assignee')
                    and value['id'] not in self.state.get('handled', [])
                    and value['id'] not in self.contended
                    and (not self.args.bead or value['id'] == self.args.bead)):
                return value, f'review queue {reviews}/{self.args.review_cap}'
        return None, 'no eligible bead in the authorized queue'

    def claim(self, value):
        self.bead = value['id']
        self.checkpoint = None
        self.save(bead=self.bead, checkpoint=None, phase='claiming', work_started=False,
                  recovery_required=True)
        try:
            self.bd('update', self.bead, '--claim', '--json')
            self.require_owned(self.show())
        except StopRun:
            # A stale ready snapshot can lose the atomic assignee claim. Read
            # exact ownership before deciding whether anything needs recovery.
            current = self.show()
            if current.get('assignee') == self.state['actor']:
                raise
            self.contended.add(self.bead)
            self.bead = None
            self.save(bead=None, checkpoint=None, phase='ready', recovery_required=False)
            return False
        self.lease_active = True
        self.save(phase='owned')
        return True

    def sweep(self):
        try:
            reviews = self.bd('list', '--label', 'pr-open', '--limit', '0', '--json', readonly=True)
            if not isinstance(reviews, list) or any(not isinstance(row, dict) or not row.get('id') for row in reviews):
                raise StopRun('invalid PR review queue')
            if not any(row.get('status') != 'closed' for row in reviews):
                return
            output = self.command(['bash', str(PLUGIN / 'scripts/close-merged.sh')])
            self.save(last_sweep={'ok': True, 'output': output.strip()})
        except StopRun as error:
            self.check_stop()
            self.save(last_sweep={'ok': False, 'error': str(error)})
            print(f'merge state unavailable: {error}; continuing independently ready work', file=sys.stderr)

    def safe_handoff(self, value):
        return (self.has_checkpoint(value) and value.get('status') in ('open', 'blocked', 'closed')
                and value.get('assignee') in (None, '', self.state['actor']))

    def heartbeat(self):
        while not self.heartbeat_stop.wait(self.args.heartbeat):
            bead = self.bead
            if not bead or not self.lease_active:
                continue
            try:
                value = self.show(bead)
                if value.get('status') == 'in_progress' and value.get('assignee') == self.state['actor']:
                    try:
                        self.command(['bd', 'hb', bead])
                    except StopRun:
                        if not self.safe_handoff(self.show(bead)):
                            raise
                elif not self.safe_handoff(value):
                    raise StopRun('lease ownership changed')
            except (StopRun, ValueError, TypeError) as error:
                if bead == self.bead and self.lease_active:
                    self.lost = str(error)
                    return

    def check_stop(self):
        if self.interrupted.is_set():
            raise StopRun('interrupted by signal; reconcile checkout, delegates and exact ownership')
        if time.time() >= self.deadline or time.monotonic() >= self.monotonic_deadline:
            raise StopRun('fixed run deadline reached; reconcile checkout, delegates and exact ownership')
        if self.lost:
            raise StopRun(f'lease lost: {self.lost}; no claim was released')

    def prompt(self):
        contract = {'bead': self.bead, 'outcome': 'working|pr|review|complete|parked|blocked',
                    'ref': None, 'next': 'continue|fresh|stop', 'delegates_stopped': True, 'checkpoint': self.checkpoint}
        recovery = ''
        if self.reconstruct_checkpoint:
            recovery = (f'Recovery of interrupted work on exactly {self.bead}: writers are stopped and ownership '
                        'is confirmed, but this turn has no completed durable checkpoint. Before further implementation, '
                        'read the bead task, comments and last durable notes; inspect actual git status/diff and the '
                        f'saved turn transcripts in {self.path.parent}. Reconstruct progress from that evidence, '
                        'then save corrected notes and this turn\'s beadwork_checkpoint token while still owner. '
                        'Do not assume the interrupted turn finished, repeat unsafe external actions, or trust stale notes. '
                        'If state cannot be reconstructed, preserve the checkout and park/block safely. ')
        return (recovery + f'Read and follow the exact skill {PLUGIN / "skills/slice/SKILL.md"} and referenced files. '
                f'This is a managed {self.args.mode} worker. The runner already claimed exactly {self.bead} '
                f'as {self.state["actor"]} and owns heartbeat across compaction and conversations. '
                'Do not claim another bead, start a nested runner or change actor. '
                f'If startup context is absent, run {PLUGIN / "hooks/session-start.sh"} and read it; '
                'respect hook trust, normal approvals, sandbox permissions, and project/role protections. '
                f'Delivery mode: {self.args.delivery}. Fixed run deadline: {self.utc(self.deadline)}. '
                'Host auto-compaction owns context limits. Choose next=continue (resume this exact native conversation), '
                'fresh (new conversation), or stop at a useful task boundary. Before returning, stop all delegates, '
                'save complete durable progress notes on this exact bead, then while still its owner use '
                f'bd update {self.bead} --if-assignee {self.state["actor"]} '
                f'--set-metadata beadwork_checkpoint={self.checkpoint}. '
                'working keeps the claim; fresh mid-bead requires this checkpoint. Deliver/park safely under the skill '
                'before releasing ownership. pr needs its real PR gate and pr-open; review needs a local commit and '
                'blocked integration-pending; complete needs a closed bead and reachable local commit, '
                'with actual verification/integration evidence recorded under the skill. '
                'ref is the PR URL for pr, commit for review/complete, null otherwise. '
                'working+stop is a clean resumable pause that retains this exact claim and saved conversation. '
                'Return only one final JSON object with exactly these keys and literal chosen values: ' + json.dumps(contract))

    def model_args(self, final):
        session = self.state.get('session_id')
        if self.args.engine == 'claude':
            args = ['claude', '-p', '--output-format', 'json']
            if self.fresh_claude_session:
                args += ['--session-id', session]
            elif session:
                args += ['--resume', session]
            if self.args.model:
                args += ['--model', self.args.model]
            if self.args.effort:
                args += ['--effort', self.args.effort]
        else:
            args = ['codex', 'exec', '--sandbox', 'workspace-write']
            if self.args.model:
                args += ['--model', self.args.model]
            if self.args.effort:
                args += ['-c', f'model_reasoning_effort="{self.args.effort}"']
            if session:
                args += ['resume', session]
            args += ['--json', '--output-last-message', str(final)]
        return args + [self.prompt()]

    def capture_session(self, value):
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}', value):
            raise StopRun('missing or invalid native conversation ID')
        if self.state.get('session_id') and self.state['session_id'] != value:
            raise StopRun('native conversation ID changed during explicit resume')
        self.save(session_id=value)
        self.seen_session = True

    def codex_event(self, line):
        try:
            event = json.loads(line)
        except ValueError as error:
            raise StopRun('corrupted Codex event stream') from error
        if not isinstance(event, dict):
            raise StopRun('invalid Codex event')
        if event.get('type') == 'thread.started':
            self.capture_session(event.get('thread_id'))
        if event.get('type') == 'turn.completed':
            self.seen_completed = True
        if event.get('type') in ('error', 'turn.failed'):
            if re.search(r'usage limit|rate limit|quota exceeded|insufficient_quota', json.dumps(event), re.I):
                raise StopRun('model usage exhausted; inspect saved transcript')
            raise StopRun('Codex reported an error; inspect saved transcript')

    @staticmethod
    def stop_group(process):
        pgid = process.pid
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=.3)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=1)

    def terminate_group(self):
        if not self.process:
            return
        self.stop_group(self.process)
        self.process = None

    def turn(self):
        self.require_owned(self.show())
        self.checkpoint = uuid.uuid4().hex
        self.seen_session = self.seen_completed = False
        number = self.state['turn'] + 1
        self.fresh_claude_session = self.args.engine == 'claude' and (
            not self.state.get('session_id') or not self.state.get('session_spawned', True))
        if self.args.engine == 'claude' and not self.state.get('session_id'):
            self.save(session_id=str(uuid.uuid4()), session_spawned=False)
        self.save(turn=number, checkpoint=self.checkpoint, phase='running', recovery_required=True,
                  work_started=False)
        output = self.path.parent / f'turn-{self.state["run_id"]}-{number}.jsonl'
        errors, final = output.with_suffix('.stderr'), output.with_suffix('.final.json')
        self.env.update({'BEADWORK_BEAD': self.bead, 'BEADWORK_CHECKPOINT': self.checkpoint,
                         'BEADWORK_RECOVERING': '1' if self.reconstruct_checkpoint else '0'})
        with output.open('w') as stdout, errors.open('w') as stderr:
            self.process = subprocess.Popen(self.model_args(final), cwd=self.root, env=self.env,
                                            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                            start_new_session=True)
            self.save(worker_pgid=self.process.pid, session_spawned=True, work_started=True)
            with output.open() as reader:
                pending = ''
                while True:
                    self.check_stop()
                    if self.args.engine == 'codex':
                        pending += reader.read()
                        while '\n' in pending:
                            line, pending = pending.split('\n', 1)
                            if line.strip():
                                self.codex_event(line)
                    code = self.process.poll()
                    if code is not None:
                        if self.args.engine == 'codex':
                            pending += reader.read()
                            for line in pending.splitlines():
                                if line.strip():
                                    self.codex_event(line)
                        break
                    self.interrupted.wait(.03)
        self.terminate_group()
        self.save(worker_pgid=None)
        if code:
            raise StopRun(f'model exited {code}; inspect {errors}')
        if self.args.engine == 'claude':
            try:
                native = json.loads(output.read_text())
                if not isinstance(native, dict) or native.get('type') != 'result' or native.get('is_error'):
                    raise ValueError('Claude reported an error')
                self.capture_session(native.get('session_id'))
                result_text = native['result']
            except (ValueError, KeyError, TypeError) as error:
                raise StopRun(f'invalid Claude JSON result: {error}') from error
        else:
            if not self.seen_session or not self.seen_completed:
                raise StopRun('missing native Codex conversation ID or completed turn event')
            try:
                result_text = final.read_text()
            except OSError as error:
                raise StopRun('missing Codex final-message file') from error
        if not isinstance(result_text, str):
            raise StopRun('invalid model final result')
        try:
            result = json.loads(result_text)
        except ValueError as error:
            raise StopRun('model final response is not one JSON object') from error
        self.verify(result)
        self.reconstruct_checkpoint = False
        self.save(reconstruct_checkpoint=False)
        return result

    def verify(self, result):
        if (not isinstance(result, dict) or set(result) != RESULT_KEYS or result.get('bead') != self.bead
                or result.get('checkpoint') != self.checkpoint or result.get('outcome') not in OUTCOMES
                or result.get('next') not in ('continue', 'fresh', 'stop') or result.get('delegates_stopped') is not True):
            raise StopRun('invalid worker protocol; reconcile exact bead and delegates')
        value = self.show()
        if not self.has_checkpoint(value):
            raise StopRun('missing durable progress notes/checkpoint on the exact bead')
        outcome, ref = result['outcome'], result['ref']
        if outcome in ('pr', 'review', 'complete'):
            if not isinstance(ref, str) or not ref.strip():
                raise StopRun('delivery result needs an exact reference')
            if outcome != 'pr' and not re.fullmatch(r'(?:[a-fA-F0-9]{40}|[a-fA-F0-9]{64})', ref):
                raise StopRun('local delivery requires an immutable full commit id')
            if outcome == 'pr' and not re.fullmatch(r'https?://\S+', ref):
                raise StopRun('PR delivery requires a real URL')
        elif ref is not None:
            raise StopRun('non-delivery result must use ref=null')
        if outcome == 'working':
            self.require_owned(value)
            return
        if value.get('assignee') not in (None, '', self.state['actor'] if outcome == 'complete' else None):
            raise StopRun('delivery/parking has not safely released this exact owner')
        labels = value.get('labels') or []
        if outcome == 'complete':
            if value.get('status') != 'closed':
                raise StopRun('completion was not recorded as a closed bead')
            self.command(['git', 'merge-base', '--is-ancestor', ref, 'HEAD'])
        elif outcome == 'pr':
            gates = value.get('dependencies') or []
            if ('pr-open' not in labels or value.get('status') == 'closed'
                    or not any(isinstance(g, dict) and g.get('issue_type') == 'gate'
                               and g.get('dependency_type') == 'blocks' and g.get('await_type') == 'gh:pr'
                               and g.get('await_id') == ref for g in gates)):
                raise StopRun('PR delivery lacks its durable real PR gate/label')
        elif outcome == 'review':
            if value.get('status') != 'blocked' or 'integration-pending' not in labels:
                raise StopRun('local review needs blocked integration-pending handoff')
            self.command(['git', 'cat-file', '-e', ref + '^{commit}'])
        elif value.get('status') != ('open' if outcome == 'parked' else 'blocked'):
            raise StopRun('parking/blocking state was not durably recorded')

    def install_guard(self):
        hook = Path(self.command(['git', 'rev-parse', '--git-path', 'hooks/pre-push']).strip())
        if not hook.is_absolute():
            hook = self.root / hook
        if hook.exists():
            print('pre-push hook exists; preserving it')
            return
        try:
            default = self.command(['git', 'symbolic-ref', '--quiet', '--short', 'refs/remotes/origin/HEAD']).strip().removeprefix('origin/')
        except StopRun:
            default = 'main'
        content = ('#!/usr/bin/env bash\n# beadwork night guard\n'
                   'while read -r _lref lsha rref _rsha; do\n'
                   f'  [ "$rref" = {shlex.quote("refs/heads/" + default)} ] && {{ echo "beadwork night guard: no default-branch pushes" >&2; exit 1; }}\n'
                   '  [ "$lsha" = "0000000000000000000000000000000000000000" ] && { echo "beadwork night guard: no branch deletions" >&2; exit 1; }\n'
                   'done\nexit 0\n')
        with hook.open('x') as stream:
            stream.write(content)
        hook.chmod(0o755)

    def run(self):
        self.root = Path(self.command(['git', 'rev-parse', '--show-toplevel']).strip()).resolve()
        if self.args.install_guard:
            self.install_guard()
            return 0
        if self.args.dry_run:
            value, reason = self.candidate()
            print(json.dumps({'engine': self.args.engine, 'mode': self.args.mode, 'delivery': self.args.delivery,
                              'bead': value['id'] if value else None, 'reason': reason}))
            return 0
        self.initialize()
        if self.reconciled_handoff:
            self.save(phase='stopped', reason='saved bead is already released; no completion inferred', recovery_required=False)
            print('saved bead is already released; recovery state cleared without another claim')
            self.lock.close()
            return 0
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            signal.signal(sig, lambda _signal, _frame: self.interrupted.set())
        thread = threading.Thread(target=self.heartbeat, daemon=True)
        thread.start()
        try:
            while not self.args.max_beads or self.state['completed'] < self.args.max_beads:
                self.check_stop()
                if not self.bead:
                    self.sweep()
                    value, reason = self.candidate()
                    if value is None:
                        self.save(phase='stopped', reason=reason, recovery_required=False)
                        print(reason)
                        return 0
                    if not self.claim(value):
                        continue
                result = self.turn()
                self.save(last_result=result)
                print(json.dumps(result), flush=True)
                if result['outcome'] != 'working':
                    self.lease_active = False
                    handled = self.state.get('handled', []) + [self.bead]
                    self.bead = None
                    self.save(bead=None, completed=self.state['completed'] + 1, handled=handled,
                              phase='ready', recovery_required=False)
                if result['next'] == 'stop':
                    self.save(phase='paused' if self.bead else 'stopped', recovery_required=False)
                    return 0
                if result['next'] == 'fresh':
                    self.save(session_id=None, session_spawned=False)
                if self.args.bead and not self.bead:
                    break
            self.save(phase='stopped', reason='max beads reached', recovery_required=False)
            return 0
        except (StopRun, OSError, ValueError, KeyError, TypeError) as error:
            needs_recovery = bool(self.bead or self.process)
            self.save(recovery_required=needs_recovery, phase='interrupted' if needs_recovery else 'stopped',
                      reason=str(error))
            print(f'beadwork stopped: {error}; state: {self.path}', file=sys.stderr)
            return 1
        finally:
            self.terminate_group()
            self.heartbeat_stop.set()
            thread.join(timeout=self.args.command_timeout + 1)
            self.lock.close()


def main():
    args = parser().parse_args()
    if args.fresh_session and not (args.recover or args.new_budget):
        parser().error('--fresh-session requires --recover or --new-budget')
    if (args.max_beads < 0 or args.review_cap < 0 or not math.isfinite(args.heartbeat)
            or not math.isfinite(args.command_timeout) or args.heartbeat <= 0 or args.command_timeout <= 0):
        parser().error('max-beads/review-cap must be nonnegative; heartbeat/command-timeout must be positive')
    if args.effort and args.effort not in ('low', 'medium', 'high', 'xhigh', *(['max'] if args.engine == 'claude' else [])):
        parser().error('effort is unsupported by the selected engine')
    if args.engine == 'codex' and args.model and re.match(r'^(opus|sonnet|haiku|opusplan|claude-)', args.model):
        parser().error('Codex needs a Codex model id; omit --model to use host default')
    try:
        return Runner(args).run()
    except (StopRun, OSError, ValueError, KeyError, TypeError) as error:
        print(f'beadwork stopped: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
