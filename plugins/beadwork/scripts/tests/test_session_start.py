"""Run the real shared startup hook with isolated Beads command fixtures."""
import os
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
        self.assertIn('count -l integration-pending', self.calls.read_text())

    def test_role_override_agrees_with_runtime(self):
        role = self.put('custom/builder.md', 'fixture role\n')
        self.env.update(BEADWORK_ROLE='builder', BEADWORK_ROLE_CARD=str(role))
        self.assertIn(str(role), self.hook())

    def test_unreachable_beads_reports_recovery(self):
        self.env['TEST_UNREACHABLE'] = '1'
        self.assertIn('Beads server unreachable', self.hook())
