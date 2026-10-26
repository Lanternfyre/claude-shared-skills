"""Behavior checks in temporary repos; no Beads server, GitHub or model calls.

Run: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s plugins/beadwork/scripts/tests -v
"""
import json
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


class NightDelivery(TempRepo):
    def setUp(self):
        super().setUp()
        self.put('README.md')
        self.commit()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.calls = self.root / 'calls.txt'
        self.stub('bd', '''#!/usr/bin/env python3
import os, sys
from pathlib import Path
args = sys.argv[1:]
with Path(os.environ['TEST_CALLS']).open('a') as f:
    f.write(' '.join(args) + '\\n')
if 'count' in args:
    print(os.environ.get('TEST_REVIEW_COUNT', '0'))
elif 'ready' in args:
    print('[{"id":"test-1"}]')
elif 'blocked' in args or 'list' in args:
    print('[]')
elif 'gate' in args:
    if os.environ.get('TEST_GATE_FAIL') == '1':
        print('1 errors'); sys.exit(1)
    print('0 errors')
elif 'create' in args:
    Path(os.environ['TEST_SUMMARY']).write_text(Path(args[args.index('--body-file') + 1]).read_text())
    print('test-summary')
else:
    print('')
''')
        model_stub = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
if '--help' in args:
    print('--effort level')
    sys.exit(0)
engine = Path(sys.argv[0]).name
calls = Path(os.environ['TEST_MODEL_CALLS'])
previous = calls.read_text().splitlines() if calls.exists() else []
with calls.open('a') as f:
    f.write(json.dumps({'engine': engine, 'args': args,
                       'park_by': os.environ.get('BEADWORK_PARK_BY'),
                       'plugin_root': os.environ.get('BEADWORK_PLUGIN_ROOT')}) + '\\n')
messages = json.loads(os.environ.get('TEST_FINAL_MESSAGES', '["BEADWORK-NIGHT: nothing - -"]'))
message = messages[min(len(previous), len(messages) - 1)]
if engine == 'codex':
    if os.environ.get('TEST_WRITE_FINAL', '1') == '1':
        Path(args[args.index('--output-last-message') + 1]).write_text(message + '\\n')
    print(os.environ.get('TEST_TRANSCRIPT', 'codex execution transcript'))
else:
    print(message)
sys.exit(int(os.environ.get('TEST_MODEL_EXIT', '0')))
'''
        self.stub('claude', model_stub)
        self.stub('codex', model_stub)
        card = self.put('role.md', '---\nnight: yes\nmodel: test-model\npaths: **\n---\n')
        self.env.update({
            'PATH': str(self.bin) + os.pathsep + self.env['PATH'],
            'TEST_CALLS': str(self.calls),
            'TEST_MODEL_CALLS': str(self.root / 'model-calls.jsonl'),
            'TEST_SUMMARY': str(self.root / 'summary.md'),
            'BEADWORK_NOW': '23:30', 'BEADWORK_DAY': '08-23',
            'BEADWORK_NIGHT_CUTOFF': '06:00', 'BEADWORK_BEAD_TIMEBOX': '30s',
            'BEADWORK_ROLE': 'builder', 'BEADWORK_ROLE_CARD': str(card),
            'BEADWORK_ENGINE': 'claude',
            'BEADWORK_VERIFY': 'true', 'BEADWORK_REVIEW_CAP': '12',
            'BEADWORK_STATE_DIR': str(self.root / 'state'),
        })
        self.env.pop('BEADWORK_ROLE_DIR', None)

    def stub(self, name, content):
        p = self.bin / name
        p.write_text(content)
        p.chmod(0o755)

    def run_night(self, mode, *args):
        self.env['BEADWORK_DELIVERY'] = mode
        r = self.run_cmd('bash', str(SCRIPTS / 'night-run.sh'), *args)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return r

    def model_calls(self):
        p = Path(self.env['TEST_MODEL_CALLS'])
        return [json.loads(line) for line in p.read_text().splitlines()] if p.exists() else []

    def set_card(self, fields, name='role.md', night='yes'):
        return self.put(name, f'---\nnight: {night}\n' + fields + '\npaths: **\n---\n')

    def test_local_runs_without_github_gate_calls(self):
        self.env['TEST_GATE_FAIL'] = '1'
        r = self.run_night('local')
        calls = self.calls.read_text()
        self.assertIn('session starts', r.stdout)
        self.assertNotIn('gate check', calls)
        self.assertIn('count -l integration-pending', calls)

    def test_pr_mode_preserves_merge_sweep(self):
        r = self.run_night('pr')
        self.assertIn('session starts', r.stdout)
        calls = self.calls.read_text()
        self.assertIn('gate check', calls)
        self.assertIn('count -l pr-open', calls)
        self.assertIn('--exclude-label human,pr-open,pr-closed', calls)

    def test_gate_outage_allows_independently_ready_work(self):
        self.env['TEST_GATE_FAIL'] = '1'
        r = self.run_night('pr')
        self.assertIn('merge state unavailable', r.stdout)
        self.assertIn('session starts', r.stdout)

    def test_local_review_cap_still_stops_new_work(self):
        self.env['TEST_REVIEW_COUNT'] = '12'
        r = self.run_night('local', '--dry-run')
        self.assertIn('stop cap:', r.stdout)

    def test_invalid_mode_is_reported(self):
        r = self.run_night('unknown', '--dry-run')
        self.assertIn('stop delivery:', r.stdout)
        self.assertFalse(self.calls.exists())

    def test_stack_checks_blocked_candidates(self):
        self.run_night('stack', '--dry-run')
        self.assertIn('blocked --json', self.calls.read_text())

    def test_timeout_does_not_guess_or_release_another_sessions_claim(self):
        self.stub('timeout', '#!/bin/sh\nexit 124\n')
        r = self.run_night('local')
        self.assertIn('claim not released', r.stdout)
        self.assertIn('timeout: reconcile delegates', r.stdout)
        self.assertEqual(r.stdout.count('session starts'), 1)
        calls = self.calls.read_text()
        self.assertNotIn('unclaim', calls)
        self.assertNotIn('list --status in_progress', calls)

    def test_claude_is_the_default_engine_and_keeps_its_arguments(self):
        self.env.pop('BEADWORK_ENGINE')
        self.set_card('model: opus\neffort: max\ncodex_model: unused\ncodex_effort: low')
        self.run_night('local')
        call, = self.model_calls()
        self.assertEqual(call['engine'], 'claude')
        self.assertEqual(call['args'], ['-p', '/beadwork:slice night', '--model', 'opus', '--effort', 'max'])
        self.assertRegex(call['park_by'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z$')

    def test_codex_arguments_use_separate_settings_and_absolute_skill_paths(self):
        self.env['BEADWORK_ENGINE'] = 'codex'
        self.set_card('model: opus\neffort: max\ncodex_model: test-codex\ncodex_effort: HIGH')
        self.run_night('local')
        call, = self.model_calls()
        args = call['args']
        self.assertEqual(call['engine'], 'codex')
        self.assertEqual(args[:7], ['exec', '--model', 'test-codex', '-c',
                                    'model_reasoning_effort="high"', '--sandbox', 'workspace-write'])
        self.assertEqual(args[7], '--output-last-message')
        self.assertTrue(Path(args[8]).is_absolute())
        prompt = args[9]
        plugin = SCRIPTS.parent
        self.assertIn(str(plugin / 'skills/slice/SKILL.md'), prompt)
        self.assertIn(str(plugin / 'hooks/session-start.sh'), prompt)
        self.assertIn('context is absent', prompt)
        self.assertIn('arguments: night', prompt)
        self.assertIn('trust', prompt)
        self.assertEqual(call['plugin_root'], str(plugin))
        self.assertRegex(call['park_by'], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z$')
        for flag in ('--dangerously-bypass-approvals-and-sandbox', '--yolo', '--full-auto',
                     '--ask-for-approval', '--dangerously-skip-permissions', '--effort'):
            self.assertNotIn(flag, args)
        self.assertFalse(any('approval_policy' in arg for arg in args))
        self.assertNotIn('opus', args)
        self.assertNotIn('max', args)

    def test_codex_effort_is_optional_and_supported_levels_are_forwarded(self):
        self.env['BEADWORK_ENGINE'] = 'codex'
        for effort in ('', 'low', 'medium', 'high', 'xhigh'):
            with self.subTest(effort=effort):
                self.set_card('model: opus\neffort: max\ncodex_model: test-codex' +
                              (f'\ncodex_effort: {effort}' if effort else ''))
                self.run_night('local')
                args = self.model_calls()[-1]['args']
                if effort:
                    self.assertIn(f'model_reasoning_effort="{effort}"', args)
                else:
                    self.assertNotIn('-c', args)

    def test_codex_requires_its_own_model_even_with_a_claude_model(self):
        self.env['BEADWORK_ENGINE'] = 'codex'
        self.set_card('model: opus\neffort: max')
        r = self.run_night('local', '--dry-run')
        self.assertIn('has no codex_model', r.stdout)
        self.assertEqual(self.model_calls(), [])
        self.assertFalse(self.calls.exists())

    def test_codex_rejects_claude_aliases_and_invalid_effort(self):
        self.env['BEADWORK_ENGINE'] = 'codex'
        for fields, error in (
            ('codex_model: opus', 'Claude model in codex_model'),
            ('codex_model: test-codex\ncodex_effort: max', 'codex_effort: max'),
            ('codex_model: test-codex\ncodex_effort: intense', 'codex_effort: intense'),
        ):
            with self.subTest(fields=fields):
                self.set_card(fields)
                r = self.run_night('local', '--dry-run')
                self.assertIn(error, r.stdout)
                self.assertEqual(self.model_calls(), [])

    def test_unknown_engine_stops_without_model_or_beads_calls(self):
        self.env['BEADWORK_ENGINE'] = 'other'
        r = self.run_night('local', '--dry-run')
        self.assertIn('stop engine: BEADWORK_ENGINE=other', r.stdout)
        self.assertEqual(self.model_calls(), [])
        self.assertFalse(self.calls.exists())

    def test_codex_uses_final_message_and_excludes_transcript_results_from_summary(self):
        self.env.update({
            'BEADWORK_ENGINE': 'codex',
            'TEST_TRANSCRIPT': 'BEADWORK-NIGHT: nothing transcript-id transcript-value',
            'TEST_FINAL_MESSAGES': json.dumps(['BEADWORK-NIGHT: review test-1 abc123',
                                               'BEADWORK-NIGHT: nothing - -']),
        })
        self.set_card('codex_model: test-codex')
        r = self.run_night('local')
        self.assertEqual(len(self.model_calls()), 2)
        self.assertIn('BEADWORK-NIGHT: review test-1 abc123', r.stdout)
        summary = Path(self.env['TEST_SUMMARY']).read_text()
        self.assertIn('- review test-1 abc123', summary)
        self.assertNotIn('transcript-id', summary)

    def test_codex_missing_or_invalid_final_status_counts_as_failure(self):
        self.env['BEADWORK_ENGINE'] = 'codex'
        self.env['TEST_TRANSCRIPT'] = 'BEADWORK-NIGHT: nothing - -'
        self.set_card('codex_model: test-codex')
        for final in ('', 'BEADWORK-NIGHT: invented id value',
                      'echo BEADWORK-NIGHT: nothing - -'):
            with self.subTest(final=final):
                self.env['TEST_FINAL_MESSAGES'] = json.dumps([final])
                before = len(self.model_calls())
                r = self.run_night('local')
                self.assertEqual(len(self.model_calls()) - before, 2)
                self.assertIn('failures: two sessions in a row failed', r.stdout)

    def test_codex_nonzero_exit_still_counts_as_failure(self):
        self.env.update({'BEADWORK_ENGINE': 'codex', 'TEST_MODEL_EXIT': '1'})
        self.set_card('codex_model: test-codex')
        r = self.run_night('local')
        self.assertEqual(len(self.model_calls()), 2)
        self.assertIn('failures: two sessions in a row failed', r.stdout)

    def test_codex_transcript_cannot_replace_an_unwritten_final_message(self):
        self.env.update({'BEADWORK_ENGINE': 'codex', 'TEST_WRITE_FINAL': '0',
                         'TEST_TRANSCRIPT': 'BEADWORK-NIGHT: nothing - -'})
        self.set_card('codex_model: test-codex')
        r = self.run_night('local')
        self.assertEqual(len(self.model_calls()), 2)
        self.assertIn('failures: two sessions in a row failed', r.stdout)

    def test_codex_timeout_stops_without_releasing_an_unknown_claim(self):
        self.env['BEADWORK_ENGINE'] = 'codex'
        self.set_card('codex_model: test-codex')
        self.stub('timeout', '#!/bin/sh\nexit 124\n')
        r = self.run_night('local')
        self.assertEqual(r.stdout.count('session starts'), 1)
        self.assertIn('timeout: reconcile delegates', r.stdout)
        self.assertNotIn('unclaim', self.calls.read_text())

    def test_codex_usage_limit_stops_after_one_session(self):
        self.env.update({'BEADWORK_ENGINE': 'codex', 'TEST_TRANSCRIPT': 'usage limit reached'})
        self.set_card('codex_model: test-codex')
        r = self.run_night('local')
        self.assertEqual(len(self.model_calls()), 1)
        self.assertIn('limit: the usage limit was hit', r.stdout)

    def test_role_card_override_takes_priority_over_both_role_directories(self):
        self.env['BEADWORK_ROLE_DIR'] = str(self.root / 'custom')
        self.set_card('model: custom-model', 'custom/builder.md')
        self.set_card('model: beads-model', '.beads/roles/builder.md')
        r = self.run_night('local', '--dry-run')
        self.assertIn('go model=test-model', r.stdout)

    def test_role_directory_override_takes_priority_and_does_not_silently_fallback(self):
        self.env.pop('BEADWORK_ROLE_CARD')
        self.set_card('model: legacy-model', '.claude/roles/builder.md')
        self.set_card('model: beads-model', '.beads/roles/builder.md')
        self.set_card('model: custom-model', 'custom/builder.md')
        for directory in ('custom', str(self.root / 'custom')):
            with self.subTest(directory=directory):
                self.env['BEADWORK_ROLE_DIR'] = directory
                r = self.run_night('local', '--dry-run')
                self.assertIn('go model=custom-model', r.stdout)
        self.env['BEADWORK_ROLE_DIR'] = 'missing'
        r = self.run_night('local', '--dry-run')
        self.assertIn('no readable role card at missing/builder.md', r.stdout)

    def test_beads_role_card_is_preferred_over_legacy_fallback(self):
        self.env.pop('BEADWORK_ROLE_CARD')
        self.set_card('model: legacy-model', '.claude/roles/builder.md')
        r = self.run_night('local', '--dry-run')
        self.assertIn('go model=legacy-model', r.stdout)
        self.set_card('model: beads-model', '.beads/roles/builder.md')
        r = self.run_night('local', '--dry-run')
        self.assertIn('go model=beads-model', r.stdout)

    def test_unreviewed_neutral_role_cannot_enable_nights_denied_by_approved_legacy(self):
        self.env.pop('BEADWORK_ROLE_CARD')
        self.set_card('model: legacy-model\ncodex_model: legacy-codex',
                      '.claude/roles/builder.md', night='no')
        self.commit()
        self.git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        self.git('checkout', '-qb', 'unreviewed-role')
        self.set_card('model: replacement-model\ncodex_model: replacement-codex',
                      '.beads/roles/builder.md')
        for committed in (False, True):
            if committed:
                self.commit()
            for engine in ('claude', 'codex'):
                with self.subTest(committed=committed, engine=engine):
                    self.env['BEADWORK_ENGINE'] = engine
                    r = self.run_night('local', '--dry-run')
                    self.assertIn('stop card: unreviewed role card at .beads/roles/builder.md', r.stdout)
                    self.assertIn('would replace approved .claude/roles/builder.md', r.stdout)
                    self.assertEqual(self.model_calls(), [])
                    self.assertFalse(self.calls.exists())

    def test_unreviewed_neutral_role_cannot_replace_approved_legacy_model(self):
        self.env.pop('BEADWORK_ROLE_CARD')
        self.set_card('model: legacy-model\ncodex_model: legacy-codex',
                      '.claude/roles/builder.md')
        self.commit()
        self.git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        self.set_card('model: replacement-model\ncodex_model: replacement-codex',
                      '.beads/roles/builder.md')
        for engine in ('claude', 'codex'):
            with self.subTest(engine=engine):
                self.env['BEADWORK_ENGINE'] = engine
                r = self.run_night('local', '--dry-run')
                self.assertIn('would replace approved .claude/roles/builder.md', r.stdout)
                self.assertEqual(self.model_calls(), [])

    def test_approved_neutral_role_keeps_policy_and_rejects_unreviewed_legacy_fallback(self):
        self.env.pop('BEADWORK_ROLE_CARD')
        self.set_card('model: legacy-model', '.claude/roles/builder.md', night='no')
        neutral = self.set_card('model: approved-neutral', '.beads/roles/builder.md')
        self.commit()
        self.git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        self.set_card('model: modified-neutral', '.beads/roles/builder.md', night='no')
        r = self.run_night('local', '--dry-run')
        self.assertIn('go model=approved-neutral', r.stdout)
        neutral.unlink()
        r = self.run_night('local', '--dry-run')
        self.assertIn('would replace approved .beads/roles/builder.md', r.stdout)

    def test_operator_card_or_directory_override_can_select_a_new_role_path(self):
        self.set_card('model: legacy-model', '.claude/roles/builder.md', night='no')
        self.commit()
        self.git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        neutral = self.set_card('model: replacement-model', '.beads/roles/builder.md')
        self.env['BEADWORK_ROLE_CARD'] = str(neutral)
        r = self.run_night('local', '--dry-run')
        self.assertIn('go model=replacement-model', r.stdout)
        self.env.pop('BEADWORK_ROLE_CARD')
        self.env['BEADWORK_ROLE_DIR'] = '.beads/roles'
        r = self.run_night('local', '--dry-run')
        self.assertIn('go model=replacement-model', r.stdout)

    def test_absolute_role_directory_still_uses_reviewed_policy(self):
        self.env.pop('BEADWORK_ROLE_CARD')
        self.env['BEADWORK_ROLE_DIR'] = str(self.root / 'custom')
        card = self.set_card('model: reviewed-model', 'custom/builder.md')
        self.commit()
        self.git('update-ref', 'refs/remotes/origin/main', 'HEAD')
        card.write_text('---\nnight: no\nmodel: modified-model\n---\n')
        r = self.run_night('local', '--dry-run')
        self.assertIn('go model=reviewed-model', r.stdout)


if __name__ == '__main__':
    unittest.main()
