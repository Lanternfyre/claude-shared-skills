"""Host metadata and relocated-plugin smoke checks; no external services required."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SharedPackages(unittest.TestCase):
    def test_each_marketplace_plugin_has_matching_host_identity(self):
        catalog = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text())
        for item in catalog['plugins']:
            with self.subTest(plugin=item['name']):
                plugin = ROOT / item['source']
                claude = json.loads((plugin / '.claude-plugin/plugin.json').read_text())
                portable = json.loads((plugin / 'plugin.json').read_text())
                for field in ('name', 'version', 'description', 'author'):
                    self.assertEqual(claude[field], portable[field])
                self.assertEqual(portable['name'], item['name'])
                self.assertTrue(list((plugin / 'skills').glob('*/SKILL.md')))

    def test_operator_invocation_policy_agrees_between_hosts(self):
        for skill in (ROOT / 'plugins').glob('*/skills/*/SKILL.md'):
            with self.subTest(skill=skill):
                header = skill.read_text().split('---', 2)[1]
                operator_only = re.search(r'^disable-model-invocation:\s*true\s*$', header, re.M)
                metadata = (skill.parent / 'agents/openai.yaml').read_text()
                explicit = re.search(r'^\s+allow_implicit_invocation:\s*false\s*$', metadata, re.M)
                self.assertEqual(bool(operator_only), bool(explicit))
                self.assertIn('interface:', metadata)

    def test_codex_hook_uses_same_existing_context_script(self):
        plugin = ROOT / 'plugins/beadwork'
        manifest = json.loads((plugin / 'plugin.json').read_text())
        hooks_path = manifest['extensions']['com.openai']['hooks']
        self.assertTrue(hooks_path.startswith('./'))
        self.assertNotIn('..', Path(hooks_path).parts)
        config = json.loads((plugin / hooks_path).read_text())
        handlers = config['hooks']['SessionStart'][0]['hooks']
        self.assertEqual(len(handlers), 1)
        command = handlers[0]['command']
        self.assertEqual(command, 'bash "${PLUGIN_ROOT}/hooks/session-start.sh"')
        self.assertTrue((plugin / 'hooks/session-start.sh').is_file())

    def test_copied_docs_package_runs_in_unrelated_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            plugin = temp / 'cache/docs/local'
            shutil.copytree(ROOT / 'plugins/docs', plugin)
            project = temp / 'project'
            project.mkdir()
            (project / 'README.md').write_text('# Test project\n\nA minimal reader page.\n')
            r = subprocess.run(['python3', str(plugin / 'scripts/docs.py'), 'check'],
                               cwd=project, capture_output=True, text=True, timeout=10)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            self.assertIn('structural check passed', r.stdout)

    def test_repository_and_project_instructions_share_a_source(self):
        self.assertTrue((ROOT / 'AGENTS.md').samefile(ROOT / 'CLAUDE.md'))
        self.assertTrue((ROOT / 'templates/AGENTS.md').samefile(ROOT / 'templates/CLAUDE.md'))


if __name__ == '__main__':
    unittest.main()
