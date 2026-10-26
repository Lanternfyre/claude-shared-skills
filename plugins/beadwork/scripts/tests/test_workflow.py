"""Behavior checks in temporary repos; no Beads server, GitHub or model calls.

Run: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s plugins/beadwork/scripts/tests -v
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]


class TempRepo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = os.environ.copy()
        self.env.update({
            'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_CONFIG_GLOBAL': '/dev/null',
            'GIT_AUTHOR_NAME': 'Test', 'GIT_AUTHOR_EMAIL': 'test@example.invalid',
            'GIT_COMMITTER_NAME': 'Test', 'GIT_COMMITTER_EMAIL': 'test@example.invalid',
        })
        self.git('init', '-q', '-b', 'main')

    def run_cmd(self, *args):
        return subprocess.run(args, cwd=self.root, env=self.env, text=True,
                              capture_output=True, timeout=15)

    def git(self, *args):
        r = self.run_cmd('git', *args)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def put(self, name, text='content\n'):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'test change')


class RoleCheck(TempRepo):
    card = '.claude/roles/builder.md'

    def setUp(self):
        super().setUp()
        self.put(self.card, '---\npaths: src/**, tests/**\nprotected: src/security/**, secrets/**\n---\n')
        self.put('secrets/old.txt')
        self.commit()
        self.git('checkout', '-qb', 'work')

    def check(self, *refs):
        return self.run_cmd('bash', str(SCRIPTS / 'role-check.sh'), self.card,
                            *(refs or ('main',)))

    def test_expected_path_passes(self):
        self.put('src/feature.py')
        self.commit()
        r = self.check()
        self.assertEqual((r.returncode, r.stdout), (0, ''))

    def test_absolute_in_repo_card_uses_approved_policy(self):
        self.put('src/feature.py')
        self.commit()
        r = self.run_cmd('bash', str(SCRIPTS / 'role-check.sh'),
                         str(self.root / self.card), 'main')
        self.assertEqual((r.returncode, r.stdout), (0, ''))
        self.put('src/security/policy.py')
        self.commit()
        r = self.run_cmd('bash', str(SCRIPTS / 'role-check.sh'),
                         str(self.root / self.card), 'main')
        self.assertEqual(r.returncode, 1, r.stderr)

    def test_adjacent_fix_is_advisory(self):
        self.put('shared/helper with space.py')
        self.commit()
        r = self.check()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('outside expected scope', r.stdout)
        self.assertIn('shared/helper with space.py', r.stdout)

    def test_protected_overrides_expected_scope(self):
        self.put('src/security/policy.py')
        self.commit()
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn('protected path', r.stdout)

    def test_rename_out_of_protected_area_blocks(self):
        self.git('mv', 'secrets/old.txt', 'public.txt')
        self.commit()
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn('secrets/old.txt', r.stdout)

    def test_changing_own_card_does_not_remove_protection(self):
        self.put(self.card, '---\npaths: **\n---\n')
        self.put('secrets/new.txt')
        self.commit()
        self.assertEqual(self.check().returncode, 1)

    def test_stack_uses_separate_policy_and_diff_bases(self):
        self.put(self.card, '---\npaths: **\n---\n')
        self.put('outside/lower.txt')
        self.commit()
        self.git('branch', 'lower')
        self.put('secrets/upper.txt')
        self.commit()
        r = self.check('lower', 'main')
        self.assertEqual(r.returncode, 1)
        self.assertIn('secrets/upper.txt', r.stdout)
        self.assertNotIn('outside/lower.txt', r.stdout)

    def test_missing_optional_protected_field(self):
        self.git('checkout', 'main')
        self.put(self.card, '---\npaths: src/**\n---\n')
        self.commit()
        self.git('checkout', '-qb', 'no-protected')
        self.put('shared/adjacent.txt')
        self.commit()
        self.assertEqual(self.check().returncode, 0)

    def test_missing_base_or_policy_is_reported(self):
        self.assertEqual(self.check('missing').returncode, 2)
        self.assertEqual(self.check('main', 'missing').returncode, 2)

    def test_unreviewed_card_is_not_silently_used_as_policy(self):
        self.git('checkout', 'main')
        self.git('rm', self.card)
        self.commit()
        self.git('checkout', '-qb', 'new-policy')
        self.put(self.card, '---\npaths: **\n---\n')
        self.commit()
        r = self.check()
        self.assertEqual(r.returncode, 2)
        self.assertIn('no approved card', r.stderr)



if __name__ == "__main__":
    unittest.main()
