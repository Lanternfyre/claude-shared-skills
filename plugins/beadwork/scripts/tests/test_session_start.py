"""Run the real shared startup hook with isolated Beads command fixtures."""
import os
import json
from pathlib import Path

from test_workflow import SCRIPTS, TempRepo


class SessionStart(TempRepo):
    def setUp(self):
        super().setUp()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        stub = self.bin / 'bd'
        stub.write_text('''#!/usr/bin/env python3
import os, sys
from pathlib import Path
args = sys.argv[1:]
with Path(os.environ['TEST_HOOK_CALLS']).open('a') as f:
    f.write(' '.join(args) + '\\n')
if 'ping' in args:
    sys.exit(1 if os.environ.get('TEST_UNREACHABLE') else 0)
elif 'memories' in args:
    print('{"schema_version":1,"fixture":"temporary context"}' if os.environ.get('TEST_MEMORIES') else '{"schema_version":1}')
elif 'prime' in args:
    print('fixture prime: ' + ' '.join(args))
elif 'count' in args:
    print('0')
elif 'config' in args:
    print('2')
elif 'show' in args:
    print(os.environ.get('TEST_BEAD', '[]'))
elif '--label-any' in args:
    print(os.environ.get('TEST_REVIEW', '[]'))
else:
    print('[]')
''')
        stub.chmod(0o755)
        self.calls = self.root / 'calls.txt'
        self.env.update({
            'PATH': str(self.bin) + os.pathsep + self.env['PATH'],
            'TEST_HOOK_CALLS': str(self.calls),
            'BEADWORK_PROJECT_DIR': str(self.root),
        })
        self.put('.beads/PRIME.md', '# fixture context\n')

    def hook(self):
        r = self.run_cmd('bash', str(SCRIPTS.parent / 'hooks/session-start.sh'))
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_prime_without_memories(self):
        output = self.hook()
        self.assertIn('prime --no-memories', output)
        self.assertIn('beadwork:', output)

    def test_prime_with_memories(self):
        self.env['TEST_MEMORIES'] = '1'
        output = self.hook()
        self.assertIn('fixture prime:', output)
        self.assertNotIn('--no-memories', output)

    def test_explicit_memory_opt_out(self):
        self.env.update(TEST_MEMORIES='1', BEADWORK_NO_MEMORIES='1')
        self.assertIn('prime --no-memories', self.hook())
        self.assertNotIn('memories --json', self.calls.read_text())

    def test_no_workspace_is_silent(self):
        (self.root / '.beads/PRIME.md').unlink()
        (self.root / '.beads').rmdir()
        self.assertEqual(self.hook(), '')
        self.assertFalse(self.calls.exists())

    def test_neutral_role_and_local_queue(self):
        self.put('.beads/roles/builder.md', 'fixture role\n')
        self.env.update(BEADWORK_ROLE='builder', BEADWORK_DELIVERY='local')
        output = self.hook()
        self.assertIn('role card .beads/roles/builder.md', output)
        self.assertIn('list --label-any pr-open,integration-pending', self.calls.read_text())

    def test_mixed_review_queue_deduplicates_and_excludes_closed(self):
        self.env['TEST_REVIEW'] = json.dumps([
            {'id': 'x', 'status': 'blocked'}, {'id': 'x', 'status': 'blocked'},
            {'id': 'y', 'status': 'open'}, {'id': 'z', 'status': 'closed'}])
        self.assertIn('in review 2', self.hook())

    def test_explicit_availability_and_exact_active_bead(self):
        self.env.update(BEADWORK_MODE='unattended', BEADWORK_BEAD='test-1',
                        BEADWORK_MANAGED='1', BEADS_ACTOR='worker-1',
                        TEST_BEAD=json.dumps([{'id': 'test-1', 'status': 'in_progress',
                                              'assignee': 'worker-1', 'notes': 'Next: finish the test'}]))
        output = self.hook()
        self.assertIn('beadwork: unattended', output)
        self.assertIn('active bead test-1', output)
        self.assertIn('Next: finish the test', output)
        self.assertIn('runner owns this claim', output)
        self.assertIn('show test-1 --json', self.calls.read_text())

    def test_role_without_card_is_optional(self):
        self.env['BEADWORK_ROLE'] = 'builder'
        self.assertIn('follow the project instructions', self.hook())

    def test_active_bead_missing_from_response_reports_failure(self):
        self.env.update(BEADWORK_BEAD='test-1', TEST_BEAD='[]')
        self.assertIn('cannot reload the active bead', self.hook())

    def test_role_override_agrees_with_runtime(self):
        role = self.put('custom/builder.md', 'fixture role\n')
        self.env.update(BEADWORK_ROLE='builder', BEADWORK_ROLE_CARD=str(role))
        self.assertIn(str(role), self.hook())

    def test_unreachable_beads_reports_recovery(self):
        self.env['TEST_UNREACHABLE'] = '1'
        self.assertIn('Beads server unreachable', self.hook())
