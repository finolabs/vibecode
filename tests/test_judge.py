"""Offline judge contract tests: the judge is the small host model and makes no network call."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from tests.data_root_fixture import account

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('package_judge', ROOT / 'scripts/judge.py')
judge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(judge)
# A valid matrix with its own consent that still names the retired Jev.
JEV_MATRIX = '## Assignment matrix\n\n- Consent: yes (2026-11-09)\n- Judge: jev\n- codex: levels 1-5; roles code-review\n'


class JudgeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = account(self, Path(self.tmp.name) / 'home')
        clean = mock.patch.dict(os.environ, {}, clear=True)
        clean.start()
        self.addCleanup(clean.stop)

    def test_host_quotes_are_verbatim_and_nonempty(self):
        for quote, expected in [('added guard', 'yes'), ('guard added', 'insufficient'),
                                ('', 'insufficient'), (' ', 'insufficient'), (None, 'insufficient')]:
            with self.subTest(quote=quote):
                out = judge.check_host(dict(answer='yes', quote=quote), '+ added guard\n')
                self.assertEqual(out['answer'], expected)
                self.assertEqual(out['quote_ok'], expected == 'yes')
                self.assertIsNone(out['p'])
        for answer in ('no', 'insufficient'):
            self.assertEqual(judge.check_host(dict(answer=answer), '')['answer'], answer)

    def test_host_rejects_wrong_schema_and_stale_bindings(self):
        for value in ([], {}, dict(answer='maybe'), dict(answer='yes', extra=True)):
            with self.assertRaises(ValueError):
                judge.check_host(value, '')
        packet = dict(answer='yes', quote='added guard', evidence_sha256=hashlib.sha256(b'added guard').hexdigest(), question='Q')
        self.assertEqual(judge.check_host(packet, 'added guard', 'Q')['answer'], 'yes')
        self.assertEqual(judge.check_host(packet, 'guard changed', 'Q')['answer'], 'insufficient')
        self.assertEqual(judge.check_host(packet, 'added guard', 'other')['answer'], 'insufficient')

    def test_absent_and_malformed_judge_configuration_default_to_host(self):
        self.assertEqual(judge.configured_judge(), 'host')
        path = self.home / '.finolabs/vibecode/host.md'
        path.parent.mkdir(parents=True)
        # Retired 13/11/2026: a legacy `## Agent roles` section alone never chooses Jev, however well formed.
        for text in ('## Agent roles\n- judge: jev\n',
                     '## Agents on this machine\n| Codex | yes | synthetic |\n\n## Agent roles\n- judge: jev\n- code review: codex\n',
                     '## Agent roles\n- judge: invalid\n', JEV_MATRIX):
            with self.subTest(text=text):
                path.write_text(text)
                self.assertEqual(judge.configured_judge(), 'host')

    def test_validation_harness_uses_the_host_answers_and_records_agreement(self):
        cases = [dict(id='case1', question='A guard was added.', evidence='added guard', expected='yes'),
                 dict(id='case2', question='A guard was added.', evidence='removed guard', expected='no')]
        answers = {'case1': dict(answer='yes', quote='added guard'), 'case2': dict(answer='no')}
        local = judge.validate_cases(cases, 'host', answers)
        self.assertEqual(local['counts'], dict(agree=2, insufficient=0, wrong=0))
        self.assertEqual((local['source'], local['validation'], local['fallback']), ('host', 'unvalidated', False))
        answers['case1']['quote'] = 'missing'
        self.assertEqual(judge.validate_cases(cases, 'host', answers)['counts']['insufficient'], 1)
        with self.assertRaises(ValueError):
            judge.validate_cases(cases * 13, 'host', answers)
        with self.assertRaises(ValueError):
            judge.validate_cases(cases, 'jev', answers)

    def test_cli_host_check_dry_run_and_unavailable_are_bounded(self):
        evidence = Path(self.tmp.name) / 'evidence'
        evidence.write_text('added guard')
        answers = Path(self.tmp.name) / 'answers.json'
        answers.write_text(json.dumps(dict(answer='yes', quote='added guard')))
        def run(*args):
            return subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/judge.py'), *args], capture_output=True, text=True)
        checked = run('check-host', '--answers', str(answers), '--evidence-file', str(evidence))
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertEqual(json.loads(checked.stdout)['answer'], 'yes')
        dry = run('ask', '--question', 'Sensitive question', '--evidence-file', str(evidence), '--dry-run')
        self.assertEqual(dry.returncode, 0)
        self.assertEqual(set(json.loads(dry.stdout)['fields']), {'question', 'evidence'})
        self.assertNotIn('Sensitive', dry.stdout)
        unavailable = run('ask', '--question', 'Q', '--evidence-file', str(evidence), '--judge', 'host')
        self.assertEqual(unavailable.returncode, 3)
        self.assertEqual(json.loads(unavailable.stdout)['answer'], 'insufficient')
        self.assertIn('unavailable', unavailable.stderr)

    def test_short_and_punctuation_quotes_do_not_support_yes(self):
        for quote in ('guard', 'a', '        ', '...........', ' a.....b ', 'abcdefg'):
            with self.subTest(length=len(quote)):
                self.assertEqual(judge.check_host(dict(answer='yes', quote=quote), quote)['answer'], 'insufficient')
        self.assertEqual(judge.check_host(dict(answer='yes', quote='abcdefgh'), 'abcdefgh')['answer'], 'yes')

    def test_closed_site_schemas_and_utf8_field_and_body_caps(self):
        for site, schema in judge.SITE_SCHEMAS.items():
            with self.subTest(site=site):
                judge.payload('The guard was added.', 'added guard', site)
                for fields in ({'question': 'Q', 'evidence': 'E', 'extra': 'x'}, {'question': 'Q'}):
                    with self.assertRaises(judge.Unavailable):
                        judge.site_fields(site, fields)
                for name, cap in schema.items():
                    fields = dict(question='Q', evidence='E')
                    fields[name] = 'é' * (cap // 2 + 1)
                    with self.assertRaises(judge.Unavailable):
                        judge.site_fields(site, fields)
        judge.payload('The guard was added.', json.dumps({'head': 'a' * 40}))
        for site in ('unknown', 'instructions', ''):
            with self.assertRaises(judge.Unavailable):
                judge.payload('Q', 'E', site)
        # Escaping can overflow the body even when each input field fits.
        with self.assertRaises(judge.Unavailable):
            judge.payload('Q', '\x01' * 12000)

    def test_sensitive_payload_refuses_and_names_only_the_field(self):
        secrets = ('sk-' + 'x' * 24, 'password=synthetic-password',
                   'ghp_' + 's' * 30, '-----BEGIN PRIVATE KEY-----',
                   'https://person:synthetic-pass@example.com')
        paths = ('/Us' + 'ers/synthetic/private', '/ho' + 'me/synthetic/private',
                 'C:' + chr(92) + 'Us' + 'ers' + chr(92) + 'synthetic' + chr(92) + 'private', '~/private', '/root/private')
        for site in judge.SITE_SCHEMAS:
            for field in ('question', 'evidence'):
                for value in (*secrets, *paths):
                    fields = dict(question='Q', evidence='E')
                    fields[field] = value
                    with self.assertRaises(judge.Unavailable) as raised:
                        judge.payload(fields['question'], fields['evidence'], site)
                    self.assertEqual(str(raised.exception), 'field: ' + field)

    def test_no_copy_can_reach_a_network_or_read_the_judge_key(self):
        # Retired 26/11/2026: the judge makes no network call in any copy.
        import ast
        copies = [ROOT / 'scripts/judge.py', *sorted(ROOT.glob('skills/*/scripts/judge.py'))]
        self.assertEqual(len(copies), 4)
        for path in copies:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                text = path.read_text()
                modules = set()
                for node in ast.walk(ast.parse(text)):
                    if isinstance(node, ast.Import):
                        modules.update(alias.name.split('.')[0] for alias in node.names)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        modules.add(node.module.split('.')[0])
                self.assertFalse(modules & {'urllib', 'http', 'ssl', 'socket', 'requests', 'os', 'subprocess'}, modules)
                for needle in ('TYPESAFE_API_KEY', 'typesafe.ai', 'environ'):
                    self.assertNotIn(needle, text)

    def test_jev_requested_or_recorded_reads_as_host_with_one_retirement_line(self):
        host = self.home / '.finolabs/vibecode/host.md'
        host.parent.mkdir(parents=True)
        host.write_text(JEV_MATRIX)
        self.assertEqual(judge.configured_judge(), 'host')
        for requested, says in (('jev', True), (None, True), ('host', False)):
            with self.subTest(requested=requested), contextlib.redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(judge.judge_source(requested), 'host')
            self.assertEqual(errors.getvalue().count(judge.RETIRED), 1 if says else 0)
        host.write_text(JEV_MATRIX.replace('Judge: jev', 'Judge: host'))
        with contextlib.redirect_stderr(io.StringIO()) as errors:
            judge.judge_source(None)
        self.assertEqual(errors.getvalue(), '')
        with mock.patch('data_root.read_data', side_effect=KeyError('unresolved')), \
                contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(judge.judge_source(None), 'host')
        self.assertEqual(errors.getvalue(), '')

    def test_cli_jev_flag_uses_the_supplied_host_answer(self):
        evidence = Path(self.tmp.name) / 'cli-evidence'
        evidence.write_text('added guard')
        answers = Path(self.tmp.name) / 'cli-answers'
        answers.write_text(json.dumps(dict(answer='yes', quote='added guard')))
        argv = ['judge.py', 'ask', '--question', 'The guard was added.', '--evidence-file', str(evidence),
                '--judge', 'jev', '--answers', str(answers)]
        with mock.patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()) as output, \
                contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(judge.main(), 0)
        out = json.loads(output.getvalue())
        self.assertEqual((out['source'], out['answer']), ('host', 'yes'))
        self.assertIn(judge.RETIRED, errors.getvalue())
        with mock.patch.object(sys, 'argv', [*argv[:3], 'Q', '--evidence-file', str(evidence), '--base-url', 'http://127.0.0.1:1']), \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            judge.main()


class AwayEvaluationSiteTest(unittest.TestCase):
    """Away evaluation: the closed `away-evaluation` site weighs two to six options and decides nothing; no network."""
    OPTIONS = ['Keep one schema', 'Split the schema']

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = account(self, Path(self.tmp.name) / 'home')
        clean = mock.patch.dict(os.environ, {}, clear=True)
        clean.start()
        self.addCleanup(clean.stop)

    def test_site_is_closed_and_separate_from_the_yes_no_sites(self):
        self.assertNotIn('away-evaluation', judge.SITE_SCHEMAS)
        self.assertEqual(set(judge.CHOICE_SITES), {'away-evaluation'})
        self.assertFalse(hasattr(judge, 'SETTLE_THRESHOLD'))
        self.assertEqual(set(judge.CHOICE_SITES['away-evaluation']), {'question', 'options', 'evidence'})
        body = judge.choice_payload('Which schema fits the spec?', self.OPTIONS, 'The spec asks for one table.')
        self.assertEqual(body, {'question': 'Which schema fits the spec?', 'options': {'1': 'Keep one schema', '2': 'Split the schema'},
                                'evidence': 'The spec asks for one table.'})
        # The yes/no payload never serves the choice site, and the choice payload never serves a yes/no site.
        with self.assertRaises(judge.Unavailable):
            judge.payload('Q', 'E', 'away-evaluation')
        for site in ('verification', 'navigator', 'unknown', ''):
            with self.assertRaises(judge.Unavailable):
                judge.choice_payload('Q', self.OPTIONS, 'E', site)

    def test_option_count_type_duplicates_and_byte_caps_refuse(self):
        caps = judge.CHOICE_SITES['away-evaluation']
        _, _, option_cap = caps['options']
        for options in ([], ['Only one'], ['o%d' % n for n in range(7)], ['Same', 'Same'], ['Fine', ''],
                        ['Fine', '   '], ['Fine', 7], 'Keep, Split', ['Fine', 'é' * (option_cap // 2 + 1)]):
            with self.subTest(options=str(options)[:40]):
                with self.assertRaises(judge.Unavailable):
                    judge.choice_payload('Which?', options, 'E')
        for count in (2, 6):
            judge.choice_payload('Which?', ['o%d' % n for n in range(count)], 'E')
        for name in ('question', 'evidence'):
            fields = dict(question='Which?', evidence='E')
            fields[name] = 'é' * (caps[name] // 2 + 1)
            with self.assertRaises(judge.Unavailable):
                judge.choice_payload(fields['question'], self.OPTIONS, fields['evidence'])
        with self.assertRaises(judge.Unavailable):
            judge.choice_payload('   ', self.OPTIONS, 'E')

    def test_secret_and_path_patterns_refuse_and_name_only_the_field(self):
        values = ('sk-' + 'x' * 24, 'password=synthetic-password', '/Us' + 'ers/synthetic/private', '~/private')
        for field in ('question', 'options', 'evidence'):
            for value in values:
                fields = dict(question='Which?', options=list(self.OPTIONS), evidence='E')
                if field == 'options':
                    fields['options'][1] = value
                else:
                    fields[field] = value
                with self.subTest(field=field, value=value[:8]):
                    with self.assertRaises(judge.Unavailable) as raised:
                        judge.choice_payload(fields['question'], fields['options'], fields['evidence'])
                    self.assertEqual(str(raised.exception), 'field: ' + field)

    def test_a_sensitive_assignment_is_refused(self):
        fixture = 'session_cookie: "\n  synthetic-fixture-1234567890\n"'
        for question, options, evidence in (('Which?', self.OPTIONS, fixture), ('password: demo', self.OPTIONS, 'E'),
                                            ('Which?', ['Keep', 'token=abc'], 'E')):
            with self.subTest(question=question, options=options), self.assertRaises(judge.Unavailable):
                judge.choice_payload(question, options, evidence)
        judge.choice_payload('Which?', self.OPTIONS, 'The password setting is described in the next section.')

    def test_the_assignment_scan_stays_linear_on_long_text(self):
        started = time.monotonic()
        self.assertFalse(judge.assigns_sensitive('a' * 65536))
        self.assertLess(time.monotonic() - started, 1)

    def test_cli_choice_site_dry_run_refusals_and_unavailable(self):
        evidence = Path(self.tmp.name) / 'evidence'
        evidence.write_text('The spec asks for one table.')
        def run(*args):
            with mock.patch.object(sys, 'argv', ['judge.py', *args]), contextlib.redirect_stdout(io.StringIO()) as out, \
                    contextlib.redirect_stderr(io.StringIO()) as err:
                code = judge.main()
            return code, out.getvalue(), err.getvalue()
        base = ('ask', '--site', 'away-evaluation', '--question', 'Which schema?', '--evidence-file', str(evidence))
        code, out, _ = run(*base, '--option', 'Keep', '--option', 'Split', '--dry-run')
        self.assertEqual(code, 0)
        self.assertEqual(set(json.loads(out)['fields']), {'question', 'options', 'evidence'})
        self.assertNotIn('Keep', out)
        # Too few options and options on a yes/no site are refused.
        code, out, _ = run(*base, '--option', 'Keep', '--dry-run')
        self.assertEqual(code, 3)
        code, _, _ = run('ask', '--question', 'Q', '--evidence-file', str(evidence), '--option', 'A', '--option', 'B', '--dry-run')
        self.assertEqual(code, 2)
        # The host's small model writes the table, and check-table checks it; a Jev request reads as host.
        for extra in ((), ('--judge', 'jev')):
            code, out, err = run(*base, '--option', 'Keep', '--option', 'Split', *extra)
            self.assertEqual(code, 3)
            self.assertEqual(json.loads(out), {'source': 'host-small', 'of': 2, 'probabilities': None})
            self.assertIn('check-table', err)
            self.assertEqual(judge.RETIRED in err, bool(extra))

    def test_check_table_accepts_only_the_closed_shape(self):
        table = Path(self.tmp.name) / 'table.json'
        def run(content, of='2'):
            table.write_text(content if isinstance(content, str) else json.dumps(content))
            with mock.patch.object(sys, 'argv', ['judge.py', 'check-table', '--file', str(table), '--of', of]), \
                    contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
                code = judge.main()
            return code, out.getvalue()
        good = {'source': 'host-small', 'of': 3, 'probabilities': [0.2, 0.5, 0.3]}
        code, out = run(good, '3')
        self.assertEqual((code, json.loads(out)), (0, good))
        for bad, of in ((good, '2'), (dict(good, source='host'), '3'), (dict(good, source='jev'), '3'), (dict(good, of='3'), '3'), (dict(good, of=True), '3'),
                        (dict(good, probabilities=[0.2, 0.5]), '3'), (dict(good, probabilities=[0.2, 0.5, 1.5]), '3'),
                        (dict(good, probabilities=[0.2, 0.5, -0.1]), '3'), (dict(good, probabilities=[0.2, 0.5, True]), '3'),
                        (dict(good, probabilities=[0.2, 0.5, '0.3']), '3'), (dict(good, probabilities='0.2'), '3'),
                        (dict(good, extra=1), '3'), ({'source': 'host-small', 'of': 3}, '3'), ([0.2, 0.5, 0.3], '3'),
                        ('{"source": "host-small", "of": 3, "probabilities": [0.2, 0.5, NaN]}', '3'),
                        ('{"source": "host-small", "of": 3, "probabilities": [0.2, 0.5, Infinity]}', '3'),
                        ('x' * (judge.TABLE_LIMIT + 1), '3'), ('not json', '3')):
            with self.subTest(bad=str(bad)[:60], of=of):
                self.assertEqual(run(bad, of)[0], 2)
        for of in ('1', '7', 'x'):
            with self.subTest(of=of), self.assertRaises(SystemExit):
                run(good, of)



if __name__ == '__main__':
    unittest.main()
