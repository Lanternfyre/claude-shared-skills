"""Runtime integration tests: temporary Git checkouts and stub native CLIs only."""
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time
import unittest

from test_workflow import TempRepo, SCRIPTS

STUB = r'''#!/usr/bin/env python3
import fcntl, json, os, subprocess, sys, time, uuid
from pathlib import Path
args = sys.argv[1:]
engine = Path(sys.argv[0]).name
path = Path(os.environ['TEST_DB'])
lock = path.with_suffix('.lock').open('a+')
def read():
    fcntl.flock(lock, fcntl.LOCK_EX)
    return json.loads(path.read_text())
def write(db):
    path.write_text(json.dumps(db))
    fcntl.flock(lock, fcntl.LOCK_UN)
def option(flag):
    return args[args.index(flag) + 1]
if engine == 'bd':
    clean = [a for a in args if a != '--readonly']
    command = clean[0]
    if os.environ.get('TEST_BD_HANG') == command:
        time.sleep(10)
    db = read()
    db['calls'].append({'args': args, 'actor': os.environ.get('BEADS_ACTOR')})
    beads = db['beads']
    if command == 'show':
        result = [b for b in beads if b['id'] == clean[1]]
    elif command == 'list':
        label = option('--label' if '--label' in args else '-l')
        result = [b for b in beads if label in b.get('labels', [])]
    elif command == 'ready':
        result = [b for b in beads if b['status'] == 'open' and not b.get('assignee')]
    elif command == 'update':
        bead = next(b for b in beads if b['id'] == clean[1])
        actor = os.environ['BEADS_ACTOR']
        if os.environ.get('TEST_CLAIM_RACE') == bead['id']:
            bead.update(assignee='other-worker', status='in_progress')
        if bead.get('assignee') and bead['assignee'] != actor:
            write(db); sys.exit(13)
        bead.update(status='in_progress', assignee=actor)
        result = bead
        if os.environ.get('TEST_CLAIM_CORRUPT'):
            write(db); print('corrupted claim response'); sys.exit(0)
    elif command == 'hb':
        bead = next(b for b in beads if b['id'] == clean[1])
        if os.environ.get('TEST_LOSE_LEASE'):
            bead['assignee'] = 'other-worker'
        if bead.get('assignee') != os.environ['BEADS_ACTOR'] or bead['status'] != 'in_progress':
            write(db); sys.exit(1)
        write(db); print('lease renewed'); sys.exit(0)
    elif command == 'gate':
        write(db)
        if os.environ.get('TEST_SWEEP_FAIL'):
            print('1 errors'); sys.exit(1)
        print('0 errors'); sys.exit(0)
    elif command == 'close':
        bead = next(b for b in beads if b['id'] == clean[1])
        bead['status'] = 'closed'
        write(db); print('closed'); sys.exit(0)
    elif command == 'label':
        bead = next(b for b in beads if b['id'] == clean[2])
        if clean[1] == 'remove':
            bead['labels'] = [label for label in bead['labels'] if label != clean[3]]
        else:
            bead['labels'].append(clean[3])
        write(db); sys.exit(0)
    else:
        write(db); print('unexpected command', file=sys.stderr); sys.exit(2)
    write(db)
    print(json.dumps(result)); sys.exit(0)

db = read()
index = len(db['models'])
steps = json.loads(os.environ.get('TEST_STEPS', '[{"outcome":"complete","next":"stop"}]'))
step = steps[min(index, len(steps) - 1)]
session = (option('--resume') if '--resume' in args else
           args[args.index('resume') + 1] if 'resume' in args else
           option('--session-id') if '--session-id' in args else uuid.uuid4().hex)
if os.environ.get('TEST_CHANGE_SESSION') and index:
    session = 'wrong-session'
bead_id = os.environ['BEADWORK_BEAD']
state = json.loads(Path(os.environ['BEADWORK_RUN_STATE']).read_text())
assert state['bead'] == bead_id and state['phase'] == 'running'
record = {'args': args, 'engine': engine, 'session': session, 'bead': bead_id,
          'actor': os.environ['BEADS_ACTOR'], 'checkpoint': os.environ['BEADWORK_CHECKPOINT'],
          'deadline': os.environ['BEADWORK_RUN_DEADLINE'], 'mode': os.environ['BEADWORK_MODE'],
          'delivery': os.environ['BEADWORK_DELIVERY'], 'cwd': os.getcwd(),
          'recovering': os.environ.get('BEADWORK_RECOVERING'),
          'managed': os.environ.get('BEADWORK_MANAGED')}
db['models'].append(record)
if engine == 'claude' and os.environ.get('TEST_NATIVE_SESSION_REGISTRY'):
    if os.environ.get('TEST_STARTUP_BEFORE_SESSION'):
        write(db); print('fixture: startup failed before session persistence', file=sys.stderr); sys.exit(1)
    sessions = db.setdefault('native_sessions', [])
    if '--resume' in args and session not in sessions:
        write(db); print('fixture: native conversation does not exist', file=sys.stderr); sys.exit(1)
    if session not in sessions:
        sessions.append(session)
if os.environ.get('TEST_DELEGATE'):
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(20)'])
    db['delegate_pid'] = child.pid
write(db)
if engine == 'codex':
    if os.environ.get('TEST_CORRUPT_EVENTS'):
        print('corrupted event', flush=True)
    elif not os.environ.get('TEST_MISSING_SESSION'):
        print(json.dumps({'type': 'thread.started', 'thread_id': session}), flush=True)
    if os.environ.get('TEST_USAGE'):
        print(json.dumps({'type': 'error', 'message': 'usage limit reached'}), flush=True)
        sys.exit(1)
if engine == 'claude' and os.environ.get('TEST_CLAUDE_ERROR'):
    print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': True,
                      'result': os.environ['TEST_CLAUDE_ERROR'], 'session_id': session,
                      'num_turns': 1}), flush=True)
    sys.exit(int(os.environ.get('TEST_MODEL_EXIT', '1')))
time.sleep(step.get('sleep', .02))
if os.environ.get('TEST_MODEL_EXIT'):
    sys.exit(int(os.environ['TEST_MODEL_EXIT']))
db = read()
bead = next(b for b in db['beads'] if b['id'] == bead_id)
outcome = step['outcome']
if not step.get('no_checkpoint'):
    bead['notes'] = 'Branch: work; verified checkpoint; next: finish the exact bead.'
    bead.setdefault('metadata', {})['beadwork_checkpoint'] = os.environ['BEADWORK_CHECKPOINT']
if not step.get('false_result'):
    if outcome == 'complete':
        bead['status'] = 'closed'
    elif outcome in ('review', 'blocked'):
        bead.update(status='blocked', assignee='')
        if outcome == 'review':
            bead['labels'].append('integration-pending')
    elif outcome == 'parked':
        bead.update(status='open', assignee='')
    elif outcome == 'pr':
        bead.update(status='open', assignee='')
        bead['labels'].append('pr-open')
        bead['dependencies'] = [{'id': 'gate-1', 'issue_type': 'gate', 'status': 'open',
                                 'dependency_type': os.environ.get('TEST_GATE_RELATION', 'blocks'), 'await_type': 'gh:pr',
                                 'await_id': 'https://example.invalid/pr/1'}]
write(db)
ref = (os.environ['TEST_COMMIT'] if outcome in ('complete', 'review') else
       'https://example.invalid/pr/1' if outcome == 'pr' else None)
result = {'bead': bead_id, 'outcome': outcome, 'ref': ref, 'next': step['next'],
          'delegates_stopped': step.get('delegates_stopped', True),
          'checkpoint': os.environ['BEADWORK_CHECKPOINT']}
if os.environ.get('TEST_WRONG_BEAD'):
    result['bead'] = 'wrong-bead'
text = os.environ.get('TEST_FINAL', json.dumps(result))
if engine == 'claude':
    wrapper = {'type': 'result', 'is_error': bool(os.environ.get('TEST_USAGE')),
               'session_id': session, 'result': text}
    if os.environ.get('TEST_MISSING_SESSION'):
        del wrapper['session_id']
    print(json.dumps(wrapper), flush=True)
else:
    print(json.dumps({'type': 'item.completed', 'item': {'text': os.environ.get('TEST_TOOL_TEXT', 'echoed fake final result')}}), flush=True)
    if not os.environ.get('TEST_MISSING_FINAL'):
        Path(option('--output-last-message')).write_text(text)
    print(json.dumps({'type': 'turn.completed', 'usage': {}}), flush=True)
'''


class Worker(TempRepo):
    def setUp(self):
        super().setUp()
        self.put('README.md')
        self.commit()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        for name in ('bd', 'claude', 'codex'):
            path = self.put(f'bin/{name}', STUB)
            path.chmod(0o755)
        self.db = self.root / 'stub.json'
        self.seed([self.bead('test-1')])
        for name in list(self.env):
            if name.startswith(('BEADWORK_', 'TEST_')):
                self.env.pop(name)
        self.env.update({'PATH': str(self.bin) + os.pathsep + self.env['PATH'],
                         'TEST_DB': str(self.db), 'TEST_COMMIT': self.git('rev-parse', 'HEAD')})

    @staticmethod
    def bead(bead_id, **values):
        return dict({'id': bead_id, 'issue_type': 'task', 'status': 'open',
                     'assignee': '', 'labels': [], 'notes': '', 'metadata': {}}, **values)

    def seed(self, beads):
        self.db.write_text(json.dumps({'beads': beads, 'calls': [], 'models': []}))

    def data(self):
        return json.loads(self.db.read_text())

    def state(self, root=None):
        root = root or self.root
        gitdir = subprocess.check_output(['git', 'rev-parse', '--absolute-git-dir'], cwd=root, env=self.env, text=True).strip()
        return json.loads((Path(gitdir) / 'beadwork/run.json').read_text())

    def argv(self, engine='codex', *args):
        return [sys.executable, str(SCRIPTS / 'run.py'), '--engine', engine,
                '--time-budget', '8s', '--heartbeat', '.15', '--command-timeout', '.8', *args]

    def worker(self, engine='codex', *args, code=0):
        result = self.run_cmd(*self.argv(engine, *args))
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def steps(self, *steps):
        self.env['TEST_STEPS'] = json.dumps(steps)

    def wait_models(self, count=1):
        end = time.monotonic() + 5
        while time.monotonic() < end:
            try:
                if len(self.data()['models']) >= count:
                    return
            except ValueError:
                pass
            time.sleep(.02)
        self.fail('stub model did not start')

    def test_roleless_host_defaults_and_exact_checkpoint(self):
        self.worker()
        call, = self.data()['models']
        self.assertEqual((call['bead'], call['delivery'], call['mode'], call['managed']),
                         ('test-1', 'auto', 'attended', '1'))
        self.assertNotIn('--model', call['args'])
        self.assertNotIn('-c', call['args'])
        self.assertEqual(call['cwd'], str(self.root))
        self.assertFalse(self.state()['recovery_required'])
        self.assertRegex(self.state()['actor'], '^beadwork-[a-f0-9]{32}$')
        self.assertTrue(any(c['args'][:2] == ['update', 'test-1'] for c in self.data()['calls']))

    def test_continue_resumes_exact_native_id_for_both_engines(self):
        for engine in ('claude', 'codex'):
            with self.subTest(engine=engine):
                self.seed([self.bead('test-1')])
                self.steps({'outcome': 'working', 'next': 'continue'}, {'outcome': 'complete', 'next': 'stop'})
                self.worker(engine)
                first, second = self.data()['models']
                flag = '--resume' if engine == 'claude' else 'resume'
                self.assertEqual(second['args'][second['args'].index(flag) + 1], first['session'])
                self.assertEqual(first['session'], second['session'])
                self.assertEqual(first['actor'], second['actor'])
                self.assertNotIn('--last', second['args'])
                self.assertNotIn('--continue', second['args'])

    def test_fresh_mid_bead_preserves_owner_exact_id_and_deadline(self):
        self.steps({'outcome': 'working', 'next': 'fresh', 'sleep': .2},
                   {'outcome': 'complete', 'next': 'stop'})
        self.worker()
        first, second = self.data()['models']
        self.assertNotEqual(first['session'], second['session'])
        for key in ('bead', 'actor', 'deadline', 'cwd'):
            self.assertEqual(first[key], second[key])
        self.assertEqual(sum(c['args'][:2] == ['update', 'test-1'] for c in self.data()['calls']), 1)
        self.assertTrue(any(c['args'][0] == 'hb' for c in self.data()['calls']))

    def test_agent_can_continue_one_conversation_to_next_bead(self):
        self.seed([self.bead('test-1'), self.bead('test-2')])
        self.steps({'outcome': 'complete', 'next': 'continue'}, {'outcome': 'complete', 'next': 'stop'})
        self.worker('claude', '--max-beads', '2')
        first, second = self.data()['models']
        self.assertEqual((first['bead'], second['bead']), ('test-1', 'test-2'))
        self.assertEqual(first['session'], second['session'])

    def test_default_queue_loop_has_no_artificial_one_bead_limit(self):
        self.seed([self.bead('test-1'), self.bead('test-2')])
        self.steps({'outcome': 'complete', 'next': 'continue'})
        self.worker()
        self.assertEqual(len(self.data()['models']), 2)
        self.assertEqual(self.state()['completed'], 2)

    def test_clean_working_pause_resumes_without_a_recovery_gate(self):
        self.steps({'outcome': 'working', 'next': 'stop'}, {'outcome': 'complete', 'next': 'stop'})
        self.worker()
        paused = self.state()
        self.assertEqual(paused['phase'], 'paused')
        self.assertFalse(paused['recovery_required'])
        self.worker()
        first, second = self.data()['models']
        for name in ('actor', 'bead', 'deadline', 'session'):
            self.assertEqual(first[name], second[name])

    def test_saved_pause_cannot_silently_override_a_new_explicit_queue_selection(self):
        self.steps({'outcome': 'working', 'next': 'stop'})
        self.worker()
        result = self.worker('codex', '--bead', 'different-bead', code=1)
        self.assertIn('differs from the requested bead', result.stderr)
        self.assertEqual(len(self.data()['models']), 1)

    def test_explicit_recovery_uses_stopped_writer_checkpoint_evidence(self):
        self.steps({'outcome': 'working', 'next': 'continue'}, {'outcome': 'complete', 'next': 'stop'})
        self.env['TEST_FINAL'] = 'corrupted final result'
        self.worker(code=1)
        prior = self.state()
        self.env.pop('TEST_FINAL')
        self.worker('codex', '--recover')
        self.assertEqual(self.state()['actor'], prior['actor'])
        self.assertEqual(self.state()['deadline'], prior['deadline'])
        self.assertFalse(self.state()['recovery_required'])

    def test_expired_saved_work_accepts_only_an_explicit_new_budget(self):
        self.steps({'outcome': 'working', 'next': 'stop'}, {'outcome': 'complete', 'next': 'stop'})
        self.worker()
        path = self.root / '.git/beadwork/run.json'
        prior = self.state()
        prior['deadline'] = time.time() - 1
        path.write_text(json.dumps(prior))
        self.worker(code=1)
        self.worker('codex', '--new-budget', '--time-budget', '4s')
        current = self.state()
        self.assertEqual(current['actor'], prior['actor'])
        self.assertGreater(current['deadline'], prior['deadline'])

    def test_new_budget_can_atomically_reclaim_only_the_saved_unassigned_bead(self):
        self.steps({'outcome': 'working', 'next': 'stop'}, {'outcome': 'complete', 'next': 'stop'})
        self.worker()
        path = self.root / '.git/beadwork/run.json'
        prior = self.state()
        prior['deadline'] = time.time() - 1
        path.write_text(json.dumps(prior))
        db = self.data()
        db['beads'][0].update(status='open', assignee='')
        self.db.write_text(json.dumps(db))
        self.worker('codex', '--new-budget')
        self.assertEqual(self.state()['actor'], prior['actor'])
        self.assertEqual(sum(c['args'][:2] == ['update', 'test-1'] for c in self.data()['calls']), 2)

    def test_new_budget_does_not_take_another_workers_saved_bead(self):
        self.steps({'outcome': 'working', 'next': 'stop'})
        self.worker()
        db = self.data()
        db['beads'][0]['assignee'] = 'other-worker'
        self.db.write_text(json.dumps(db))
        self.worker('codex', '--new-budget', code=1)
        self.assertEqual(len(self.data()['models']), 1)
        self.assertEqual(self.data()['beads'][0]['assignee'], 'other-worker')

    def test_recovery_can_clear_a_proven_released_handoff_without_new_work(self):
        self.env['TEST_FINAL'] = 'corrupted final result'
        self.worker(code=1)
        self.env.pop('TEST_FINAL')
        self.worker('codex', '--recover')
        self.assertEqual(len(self.data()['models']), 1)
        self.assertFalse(self.state()['recovery_required'])
        self.assertIsNone(self.state()['bead'])

    def test_corrupted_run_state_cannot_discard_ownership(self):
        directory = self.root / '.git/beadwork'
        directory.mkdir()
        path = directory / 'run.json'
        path.write_text('{"recovery_required": false, "bead": "owned-id"}')
        self.worker(code=1)
        self.assertEqual(json.loads(path.read_text())['bead'], 'owned-id')
        self.assertFalse(self.data()['models'])

    def test_corrupted_saved_native_id_is_never_used_as_a_cli_option(self):
        self.steps({'outcome': 'working', 'next': 'stop'})
        self.worker()
        state = self.state()
        state['session_id'] = '--dangerously-bypass-approvals-and-sandbox'
        (self.root / '.git/beadwork/run.json').write_text(json.dumps(state))
        self.worker(code=1)
        self.assertEqual(len(self.data()['models']), 1)

    def test_explicit_pilot_limit_stops_after_one_bead(self):
        self.seed([self.bead('test-1'), self.bead('test-2')])
        self.steps({'outcome': 'complete', 'next': 'continue'})
        self.worker('codex', '--max-beads', '1')
        self.assertEqual(len(self.data()['models']), 1)

    def test_unattended_has_the_same_authority_and_does_not_install_a_hook(self):
        self.worker('codex', '--mode', 'unattended')
        self.assertFalse((self.root / '.git/hooks/pre-push').exists())
        self.assertEqual(self.data()['models'][0]['mode'], 'unattended')

    def test_quoted_usage_text_in_tool_output_does_not_stop_the_run(self):
        self.env['TEST_TOOL_TEXT'] = 'Documentation example: usage limit reached'
        self.worker()
        self.assertFalse(self.state()['recovery_required'])

    def test_native_resume_id_change_stops_without_retry(self):
        self.steps({'outcome': 'working', 'next': 'continue'}, {'outcome': 'complete', 'next': 'stop'})
        self.env['TEST_CHANGE_SESSION'] = '1'
        self.worker(code=1)
        self.assertEqual(len(self.data()['models']), 2)
        self.assertTrue(self.state()['recovery_required'])

    def test_dry_run_has_no_claim_model_or_state_writes(self):
        result = self.worker('codex', '--dry-run')
        self.assertEqual(json.loads(result.stdout)['bead'], 'test-1')
        self.assertFalse((self.root / '.git/beadwork').exists())
        self.assertFalse(self.data()['models'])
        self.assertTrue(all(c['args'][0] == '--readonly' for c in self.data()['calls']))

    def test_role_label_and_exact_bead_select_the_allowed_queue(self):
        self.seed([self.bead('wrong-role', labels=['role:other', 'pilot']),
                   self.bead('test-1', labels=['role:builder', 'pilot']), self.bead('unlabelled')])
        self.worker('codex', '--role', 'builder', '--label', 'pilot', '--bead', 'test-1')
        self.assertEqual([m['bead'] for m in self.data()['models']], ['test-1'])

    def test_mixed_review_queue_is_summed_and_deduplicated(self):
        self.seed([self.bead('test-1'), self.bead('pr', labels=['pr-open']),
                   self.bead('local', status='blocked', labels=['integration-pending']),
                   self.bead('both', labels=['pr-open', 'integration-pending'])])
        result = self.worker('codex', '--dry-run', '--review-cap', '3')
        self.assertIn('review cap reached (3/3)', result.stdout)
        result = self.worker('codex', '--dry-run', '--review-cap', '4')
        self.assertEqual(json.loads(result.stdout)['bead'], 'test-1')

    def test_known_pr_maintenance_is_allowed_at_the_review_cap(self):
        self.seed([self.bead('test-1', status='blocked', labels=['pr-open'])])
        self.steps({'outcome': 'pr', 'next': 'stop'})
        self.worker('codex', '--bead', 'test-1', '--review-cap', '0')
        self.assertEqual(len(self.data()['models']), 1)

    def test_result_alone_does_not_prove_completion(self):
        self.steps({'outcome': 'complete', 'next': 'stop', 'false_result': True})
        self.worker(code=1)
        self.assertTrue(self.state()['recovery_required'])
        self.assertEqual(self.state()['bead'], 'test-1')

    def test_fresh_requires_a_saved_checkpoint_and_stopped_delegates(self):
        for extra in ({'no_checkpoint': True}, {'delegates_stopped': False}):
            with self.subTest(extra=extra):
                self.seed([self.bead('test-1')])
                self.steps({'outcome': 'working', 'next': 'fresh', **extra})
                # Each case uses a new checkout state after explicit test reconciliation.
                state = self.root / '.git/beadwork/run.json'
                if state.exists():
                    state.unlink()
                self.worker(code=1)
                self.assertEqual(len(self.data()['models']), 1)

    def test_missing_corrupted_results_and_session_ids_stop_without_retry(self):
        for engine, variable, value in (
                ('claude', 'TEST_MISSING_SESSION', '1'), ('codex', 'TEST_MISSING_SESSION', '1'),
                ('codex', 'TEST_CORRUPT_EVENTS', '1'), ('codex', 'TEST_MISSING_FINAL', '1'),
                ('claude', 'TEST_FINAL', 'not json'), ('codex', 'TEST_FINAL', 'not json'),
                ('codex', 'TEST_WRONG_BEAD', '1'), ('claude', 'TEST_MODEL_EXIT', '1')):
            with self.subTest(engine=engine, variable=variable):
                self.seed([self.bead('test-1')])
                state = self.root / '.git/beadwork/run.json'
                if state.exists():
                    state.unlink()
                self.env[variable] = value
                self.worker(engine, code=1)
                self.assertEqual(len(self.data()['models']), 1)
                self.assertTrue(self.state()['recovery_required'])
                self.env.pop(variable)

    def test_usage_exhaustion_does_not_spin(self):
        self.env['TEST_USAGE'] = '1'
        self.worker(code=1)
        self.assertEqual(len(self.data()['models']), 1)
        self.assertTrue(self.state()['recovery_required'])

    def test_claude_weekly_limit_on_stdout_is_reported_before_exit_code(self):
        self.env['TEST_CLAUDE_ERROR'] = "You've hit your weekly limit · resets 1am (UTC)"
        result = self.worker('claude', code=1)
        self.assertIn('model usage exhausted; inspect', result.stderr)
        self.assertIn('.jsonl', result.stderr)
        self.assertNotIn('resets 1am', result.stderr)
        state = self.state()
        self.assertEqual(len(self.data()['models']), 1)
        self.assertEqual(state['bead'], 'test-1')
        self.assertTrue(state['recovery_required'])
        self.assertEqual(self.data()['beads'][0]['assignee'], state['actor'])
        self.assertFalse(any('unclaim' in call['args'] for call in self.data()['calls']))
        errors, = (self.root / '.git/beadwork').glob('turn-*.stderr')
        self.assertEqual(errors.read_text(), '')

    def test_generic_model_exit_reports_both_output_paths(self):
        self.env['TEST_MODEL_EXIT'] = '1'
        result = self.worker('claude', code=1)
        self.assertIn('model exited 1', result.stderr)
        self.assertIn('.stderr', result.stderr)
        self.assertIn('.jsonl', result.stderr)
        self.assertEqual(len(self.data()['models']), 1)
        self.assertTrue(self.state()['recovery_required'])

    def test_fixed_deadline_terminates_worker_and_does_not_reset_for_fresh(self):
        self.steps({'outcome': 'working', 'next': 'fresh', 'sleep': .25},
                   {'outcome': 'working', 'next': 'continue', 'sleep': 4})
        started = time.monotonic()
        self.worker('codex', '--time-budget', '1s', code=1)
        self.assertLess(time.monotonic() - started, 2)
        self.assertTrue(self.state()['recovery_required'])
        self.assertEqual(self.state()['bead'], 'test-1')
        self.assertEqual(len({m['deadline'] for m in self.data()['models']}), 1)

    def test_signal_preserves_exact_owner_and_blocks_automatic_restart(self):
        self.steps({'outcome': 'working', 'next': 'continue', 'sleep': 5})
        process = subprocess.Popen(self.argv(), cwd=self.root, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: process.poll() is None and process.kill())
        self.wait_models()
        process.send_signal(signal.SIGTERM)
        process.communicate(timeout=3)
        self.assertEqual(process.returncode, 1)
        before = self.state()
        self.assertTrue(before['recovery_required'])
        self.assertEqual(before['bead'], 'test-1')
        result = self.worker(code=1)
        self.assertIn('recovery required', result.stderr)
        self.assertEqual(self.state()['actor'], before['actor'])
        self.assertEqual(len(self.data()['models']), 1)
        self.assertFalse(any('unclaim' in c['args'] for c in self.data()['calls']))

    def test_lease_loss_terminates_worker_group_and_never_unclaims_another_owner(self):
        self.steps({'outcome': 'working', 'next': 'continue', 'sleep': 5})
        self.env.update({'TEST_LOSE_LEASE': '1', 'TEST_DELEGATE': '1'})
        result = self.worker(code=1)
        self.assertIn('lease lost', result.stderr)
        self.assertEqual(self.data()['beads'][0]['assignee'], 'other-worker')
        self.assertFalse(any('unclaim' in c['args'] for c in self.data()['calls']))
        pid = self.data()['delegate_pid']
        proc = Path(f'/proc/{pid}/stat')
        if proc.exists():
            self.assertEqual(proc.read_text().split()[2], 'Z')

    def test_checkout_lock_prevents_a_second_runner(self):
        self.steps({'outcome': 'complete', 'next': 'stop', 'sleep': .6})
        first = subprocess.Popen(self.argv(), cwd=self.root, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: first.poll() is None and first.kill())
        self.wait_models()
        result = self.worker(code=1)
        self.assertIn('checkout lock', result.stderr)
        first.communicate(timeout=4)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(len(self.data()['models']), 1)

    def test_independent_checkouts_have_distinct_actors_and_cannot_share_claims(self):
        self.seed([self.bead('test-1'), self.bead('test-2')])
        other = self.root / 'other'
        self.git('worktree', 'add', '--detach', str(other), 'HEAD')
        self.steps({'outcome': 'complete', 'next': 'stop', 'sleep': .5})
        first = subprocess.Popen(self.argv('codex', '--bead', 'test-1'), cwd=self.root, env=self.env,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: first.poll() is None and first.kill())
        self.wait_models()
        second = subprocess.run(self.argv('codex', '--bead', 'test-2'), cwd=other, env=self.env,
                                text=True, capture_output=True, timeout=5)
        self.assertEqual(second.returncode, 0, second.stderr)
        first.communicate(timeout=4)
        models = self.data()['models']
        self.assertEqual(len({m['actor'] for m in models}), 2)
        self.assertEqual({m['bead'] for m in models}, {'test-1', 'test-2'})

    def test_claim_output_failure_still_retains_exact_bead_for_recovery(self):
        self.env['TEST_CLAIM_CORRUPT'] = '1'
        self.worker(code=1)
        self.assertEqual(self.state()['bead'], 'test-1')
        self.assertEqual(self.data()['beads'][0]['assignee'], self.state()['actor'])
        self.assertFalse(self.data()['models'])

    def test_ambiguous_successful_claim_recovers_without_a_future_checkpoint(self):
        self.env['TEST_CLAIM_CORRUPT'] = '1'
        self.worker(code=1)
        prior = self.state()
        self.assertIsNone(prior['checkpoint'])
        self.env.pop('TEST_CLAIM_CORRUPT')
        self.worker('codex', '--recover')
        model, = self.data()['models']
        self.assertEqual(model['actor'], prior['actor'])
        self.assertEqual(model['recovering'], '1')
        self.assertIn('Before further implementation', model['args'][-1])
        self.assertEqual(sum(c['args'][:2] == ['update', 'test-1'] for c in self.data()['calls']), 1)

    def test_claim_race_rescans_without_releasing_another_owner(self):
        self.seed([self.bead('contended'), self.bead('test-1')])
        self.env['TEST_CLAIM_RACE'] = 'contended'
        self.worker()
        db = self.data()
        self.assertEqual(db['beads'][0]['assignee'], 'other-worker')
        self.assertEqual([m['bead'] for m in db['models']], ['test-1'])
        self.assertFalse(any('unclaim' in c['args'] for c in db['calls']))
        self.assertFalse(self.state()['recovery_required'])

    def test_lost_exact_claim_race_stops_cleanly_and_remains_restartable(self):
        self.env['TEST_CLAIM_RACE'] = 'test-1'
        self.worker('codex', '--bead', 'test-1')
        self.assertFalse(self.state()['recovery_required'])
        self.assertIsNone(self.state()['bead'])
        self.assertFalse(self.data()['models'])
        self.env.pop('TEST_CLAIM_RACE')
        self.worker('codex', '--bead', 'test-1')
        self.assertFalse(self.data()['models'])

    def test_interrupted_first_claude_turn_resumes_its_persisted_native_uuid(self):
        self.steps({'outcome': 'working', 'next': 'continue', 'sleep': 5},
                   {'outcome': 'complete', 'next': 'stop'})
        process = subprocess.Popen(self.argv('claude'), cwd=self.root, env=self.env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: process.poll() is None and process.kill())
        self.wait_models()
        first = self.data()['models'][0]
        self.assertIn('--session-id', first['args'])
        self.assertEqual(self.state()['session_id'], first['session'])
        process.send_signal(signal.SIGTERM)
        process.communicate(timeout=3)
        self.assertEqual(process.returncode, 1)
        self.assertFalse(self.data()['beads'][0]['notes'])
        self.worker('claude', '--recover')
        first, second = self.data()['models']
        self.assertEqual(second['args'][second['args'].index('--resume') + 1], first['session'])
        self.assertEqual(second['recovering'], '1')
        self.assertEqual(first['deadline'], second['deadline'])

    def test_interrupted_later_turn_reconstructs_from_the_previous_durable_checkpoint(self):
        self.steps({'outcome': 'working', 'next': 'continue'},
                   {'outcome': 'working', 'next': 'continue', 'sleep': 5},
                   {'outcome': 'complete', 'next': 'stop'})
        process = subprocess.Popen(self.argv(), cwd=self.root, env=self.env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: process.poll() is None and process.kill())
        self.wait_models(2)
        previous = self.data()['beads'][0]['metadata']['beadwork_checkpoint']
        self.assertNotEqual(previous, self.state()['checkpoint'])
        process.send_signal(signal.SIGTERM)
        process.communicate(timeout=3)
        self.worker('codex', '--recover')
        first, second, recovered = self.data()['models']
        self.assertEqual(first['session'], recovered['session'])
        self.assertEqual(second['actor'], recovered['actor'])
        self.assertEqual(recovered['recovering'], '1')
        self.assertIn('saved turn transcripts', recovered['args'][-1])

    def test_failed_child_startup_recovers_exact_owned_bead_without_claiming_again(self):
        # Restrict PATH so a missing stub can never fall back to a real model CLI.
        for command, target in (('git', shutil.which('git')), ('python3', sys.executable)):
            (self.bin / command).symlink_to(target)
        (self.bin / 'claude').unlink()
        self.env['PATH'] = str(self.bin)
        self.worker('claude', '--delivery', 'local', code=1)
        before = self.state()
        self.assertEqual(before['bead'], 'test-1')
        self.assertFalse(before['work_started'])
        self.assertFalse(self.data()['models'])
        model = self.put('bin/claude', STUB)
        model.chmod(0o755)
        self.worker('claude', '--recover')
        call, = self.data()['models']
        self.assertEqual(call['session'], before['session_id'])
        self.assertIn('--session-id', call['args'])
        self.assertEqual(call['recovering'], '1')
        self.assertEqual(sum(c['args'][:2] == ['update', 'test-1'] for c in self.data()['calls']), 1)

    def test_fresh_session_recovers_a_cli_that_failed_before_persisting_its_conversation(self):
        self.env.update(TEST_NATIVE_SESSION_REGISTRY='1', TEST_STARTUP_BEFORE_SESSION='1')
        self.worker('claude', code=1)
        before = self.state()
        self.assertTrue(before['session_spawned'])
        self.assertTrue(before['recovery_required'])
        self.assertFalse(self.data().get('native_sessions'))
        self.env.pop('TEST_STARTUP_BEFORE_SESSION')
        # A normal recovery preserves the exact ID and refuses to invent a replacement.
        self.worker('claude', '--recover', code=1)
        self.assertEqual(self.state()['session_id'], before['session_id'])
        self.worker('claude', '--recover', '--fresh-session')
        recovered = self.data()['models'][-1]
        self.assertIn('--session-id', recovered['args'])
        self.assertNotIn('--resume', recovered['args'])
        self.assertNotEqual(recovered['session'], before['session_id'])
        self.assertEqual(recovered['bead'], before['bead'])
        self.assertEqual(recovered['actor'], before['actor'])
        self.assertEqual(recovered['recovering'], '1')
        self.assertEqual(self.state()['deadline'], before['deadline'])
        self.assertEqual(self.state()['run_id'], before['run_id'])
        self.assertEqual(sum(c['args'][:2] == ['update', 'test-1'] for c in self.data()['calls']), 1)

    def test_fresh_session_requires_an_explicit_recovery_option(self):
        result = self.worker('claude', '--fresh-session', code=2)
        self.assertIn('--fresh-session requires --recover or --new-budget', result.stderr)
        self.assertFalse(self.data()['models'])
        self.assertFalse(self.data()['beads'][0]['assignee'])

    def test_fresh_session_does_not_clear_identity_before_ownership_is_confirmed(self):
        self.steps({'outcome': 'working', 'next': 'stop'})
        self.worker('claude')
        before = self.state()
        db = self.data()
        db['beads'][0]['assignee'] = 'other-worker'
        self.db.write_text(json.dumps(db))
        self.worker('claude', '--recover', '--fresh-session', code=1)
        self.assertEqual(self.state()['session_id'], before['session_id'])
        self.assertEqual(self.data()['beads'][0]['assignee'], 'other-worker')
        self.assertEqual(len(self.data()['models']), 1)

    def test_fresh_session_with_new_budget_keeps_exact_owned_work(self):
        self.steps({'outcome': 'working', 'next': 'stop'}, {'outcome': 'complete', 'next': 'stop'})
        self.worker('codex')
        before = self.state()
        self.worker('codex', '--new-budget', '--fresh-session', '--time-budget', '30s')
        first, recovered = self.data()['models']
        self.assertNotEqual(first['session'], recovered['session'])
        self.assertNotIn('resume', recovered['args'])
        self.assertEqual(first['actor'], recovered['actor'])
        self.assertEqual(first['bead'], recovered['bead'])
        self.assertEqual(self.state()['prior_deadline'], before['deadline'])
        self.assertGreater(self.state()['deadline'], before['deadline'])

    def test_explicit_pending_local_integration_can_resume_at_the_cap(self):
        self.seed([self.bead('test-1', status='blocked', labels=['integration-pending'])])
        self.worker('codex', '--bead', 'test-1', '--delivery', 'local', '--review-cap', '0')
        self.assertEqual([m['bead'] for m in self.data()['models']], ['test-1'])

    def test_pending_local_integration_does_not_bypass_unresolved_implementation_blockers(self):
        self.seed([self.bead('test-1', status='blocked', labels=['integration-pending'],
                            dependencies=[{'id': 'unfinished', 'dependency_type': 'blocks', 'status': 'open'}])])
        result = self.worker('codex', '--bead', 'test-1', '--delivery', 'local', '--dry-run')
        self.assertIn('unresolved blockers', result.stdout)
        self.assertFalse(self.data()['models'])

    def test_pr_result_requires_a_blocking_gate_rather_than_a_related_gate(self):
        self.steps({'outcome': 'pr', 'next': 'stop'})
        self.env['TEST_GATE_RELATION'] = 'relates-to'
        result = self.worker(code=1)
        self.assertIn('real PR gate', result.stderr)
        self.assertTrue(self.state()['recovery_required'])

    def test_preselection_sweep_clears_merged_prs_before_the_review_cap(self):
        self.seed([self.bead('merged', labels=['pr-open'],
                            dependencies=[{'id': 'gate-1', 'issue_type': 'gate', 'status': 'closed',
                                           'dependency_type': 'blocks', 'await_type': 'gh:pr',
                                           'await_id': 'https://example.invalid/pr/1', 'close_reason': 'was merged'}]),
                   self.bead('test-1')])
        self.worker('codex', '--review-cap', '1')
        self.assertEqual(self.data()['beads'][0]['status'], 'closed')
        self.assertEqual([m['bead'] for m in self.data()['models']], ['test-1'])

    def test_local_delivery_still_sweeps_existing_merged_prs_before_the_cap(self):
        self.seed([self.bead('merged', labels=['pr-open'],
                            dependencies=[{'id': 'gate-1', 'issue_type': 'gate', 'status': 'closed',
                                           'dependency_type': 'blocks', 'await_type': 'gh:pr',
                                           'await_id': 'https://example.invalid/pr/1', 'close_reason': 'was merged'}]),
                   self.bead('test-1')])
        self.worker('codex', '--delivery', 'local', '--review-cap', '1')
        self.assertEqual(self.data()['beads'][0]['status'], 'closed')
        self.assertEqual([m['bead'] for m in self.data()['models']], ['test-1'])
        self.assertTrue(any(c['args'][0] == 'gate' for c in self.data()['calls']))

    def test_queue_without_pr_work_does_not_contact_github(self):
        self.worker()
        self.assertFalse(any(c['args'][0] == 'gate' for c in self.data()['calls']))

    def test_sweep_outage_does_not_block_independently_ready_work(self):
        self.seed([self.bead('review', labels=['pr-open']), self.bead('test-1')])
        self.env['TEST_SWEEP_FAIL'] = '1'
        result = self.worker()
        self.assertIn('merge state unavailable', result.stderr)
        self.assertEqual(len(self.data()['models']), 1)

    def test_sweep_network_timeout_is_bounded_and_independent_work_continues(self):
        self.seed([self.bead('review', labels=['pr-open']), self.bead('test-1')])
        self.env['TEST_BD_HANG'] = 'gate'
        result = self.worker('codex', '--command-timeout', '.2')
        self.assertIn('merge state unavailable', result.stderr)
        self.assertEqual(len(self.data()['models']), 1)

    def test_bounded_beads_command_timeout(self):
        self.env['TEST_BD_HANG'] = 'ready'
        started = time.monotonic()
        self.worker('codex', '--command-timeout', '.1', code=1)
        self.assertLess(time.monotonic() - started, 1)
        self.assertFalse(self.state()['recovery_required'])
        self.env.pop('TEST_BD_HANG')
        self.worker()
        self.assertEqual(len(self.data()['models']), 1)

    def test_preclaim_failure_state_from_an_older_runner_is_recoverable(self):
        self.env['TEST_BD_HANG'] = 'ready'
        self.worker('codex', '--command-timeout', '.15', code=1)
        path = self.root / '.git/beadwork/run.json'
        state = self.state()
        state.update(recovery_required=True, phase='interrupted')
        path.write_text(json.dumps(state))
        self.env.pop('TEST_BD_HANG')
        self.worker('codex', '--recover')
        self.assertFalse(self.state()['recovery_required'])

    def test_model_settings_preserve_host_permission_defaults(self):
        self.worker('codex', '--model', 'test-codex', '--effort', 'high')
        args = self.data()['models'][0]['args']
        self.assertIn('model_reasoning_effort="high"', args)
        self.assertNotIn('--sandbox', args)
        for value in args:
            self.assertNotIn('dangerously', value)
            self.assertNotIn('approval_policy', value)
        self.assertNotIn('--full-auto', args)

    def test_legacy_wrapper_uses_the_same_runner_with_only_legacy_queue_constraints(self):
        self.env.update({'BEADWORK_ENGINE': 'codex', 'BEADWORK_NOW': '23:30'})
        self.seed([self.bead('test-1', labels=['night-ok'])])
        result = self.run_cmd('bash', str(SCRIPTS / 'night-run.sh'), '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['mode'], 'unattended')
        self.assertFalse((self.root / '.git/beadwork').exists())

    def test_optional_legacy_guard_preserves_existing_hooks_and_blocks_unsafe_pushes(self):
        self.worker('codex', '--install-guard')
        hook = self.root / '.git/hooks/pre-push'
        sha = '1' * 40
        for local_sha, remote, code in ((sha, 'refs/heads/main', 1),
                                      ('0' * 40, 'refs/heads/work', 1),
                                      (sha, 'refs/heads/work', 0)):
            result = subprocess.run(['bash', str(hook)], input=f'refs/heads/work {local_sha} {remote} {sha}\n',
                                    text=True, capture_output=True, timeout=2)
            self.assertEqual(result.returncode, code)
        hook.write_text('#!/bin/sh\necho custom-hook\n')
        self.worker('codex', '--install-guard')
        self.assertEqual(hook.read_text(), '#!/bin/sh\necho custom-hook\n')
        self.assertFalse(self.data()['models'])


if __name__ == '__main__':
    unittest.main()
