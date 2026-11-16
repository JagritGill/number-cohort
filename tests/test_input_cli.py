import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from number_cohort import AuditError, load_numbers
from number_cohort.input import MAX_BYTES

ROOT = Path(__file__).resolve().parents[1]


class InputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "input.json"

    def read(self, text, **kwargs):
        self.path.write_text(text, encoding="utf-8")
        return load_numbers(self.path, **kwargs)

    def test_preserves_tokens_and_literal_field_names(self):
        self.assertEqual(self.read('[1,1.00,-0,1e+2]'), ["1", "1.00", "-0", "1e+2"])
        self.assertEqual(self.read('[{"a/b~.☃": 0.10000000000000001}]', field="a/b~.☃"),
                         ["0.10000000000000001"])
        self.assertEqual(self.read('[{"": 2}]', field=""), ["2"])

    def test_rejects_bad_json_and_non_numeric_selection(self):
        for value in ['[true]', '[null]', '["1"]', '[{}]', '{}', '[1,]', '[NaN]', '[Infinity]',
                      '[-Infinity]', '[01]', '[1] trailing', '\ufeff[1]', '[{"id":1,"id":2}]',
                      '[{"id":1,"\\u0069d":2}]', '["\\ud800"]']:
            with self.subTest(value=value), self.assertRaises(AuditError):
                self.read(value)
        for text in ['[{}]', '[1]', '[{"id":"2"}]', '[{"id":false}]']:
            with self.assertRaises(AuditError):
                self.read(text, field="id")
        with self.assertRaises(AuditError):
            self.read('[1]', field=True)

    def test_nonselected_payload_is_validated_without_emitting_values(self):
        self.assertEqual(self.read('[{"id":2,"payload":"synthetic"}]', field="id"), ["2"])
        for payload in ['{"x":1,"x":2}', '"\\udfff"', 'NaN']:
            with self.assertRaises(AuditError):
                self.read('[{"id":2,"payload":' + payload + '}]', field="id")

    def test_file_errors_and_byte_bound(self):
        with self.assertRaises(AuditError):
            load_numbers(self.path)
        self.path.write_bytes(b'[1,\xff]')
        with self.assertRaises(AuditError):
            load_numbers(self.path)
        with self.assertRaises(AuditError):
            load_numbers(Path(self.temp.name))
        link = Path(self.temp.name) / "link.json"
        link.symlink_to(self.path)
        with self.assertRaises(AuditError):
            load_numbers(link)
        self.path.write_bytes(b'[]' + b' ' * (MAX_BYTES - 2))
        self.assertEqual(load_numbers(self.path), [])
        with self.path.open('ab') as f:
            f.write(b' ')
        with self.assertRaises(AuditError):
            load_numbers(self.path)

    def test_structural_limits(self):
        for text in ['[' + ','.join(['1'] * 10001) + ']', '[' + '1' * 129 + ']',
                     '[' * 70 + '0' + ']' * 70, '[' * 2000 + '0' + ']' * 2000]:
            with self.assertRaises(AuditError):
                self.read(text)
        with self.assertRaises(AuditError):
            self.read('[{"id":1,"payload":"' + 'a' * 16385 + '"}]', field="id")
        with patch('number_cohort.input.MAX_NODES', 5), self.assertRaises(AuditError):
            self.read('[{"id":1,"payload":[2,3,4]}]', field="id")


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', '-m', 'number_cohort', *args],
                              cwd=ROOT, text=True, capture_output=True, check=False)

    def test_json_example_and_no_payload(self):
        p = self.run_cli('examples/cohort.json', '--format', 'json')
        self.assertEqual(p.returncode, 1, p.stderr)
        result = json.loads(p.stdout)
        self.assertEqual((result['new_equal_pairs'], result['lost_distinctions']), (3, 2))
        self.assertNotIn('9007199254740993', p.stdout)
        self.assertEqual(p.stderr, '')
        p = self.run_cli('examples/records.json', '--field', 'id', '--format', 'json')
        self.assertEqual(p.returncode, 1)
        self.assertEqual(json.loads(p.stdout)['new_equal_pairs'], 1)
        self.assertNotIn('synthetic', p.stdout)

    def test_text_snapshot_and_exit_codes(self):
        p = self.run_cli('examples/cohort.json')
        self.assertEqual(p.returncode, 1)
        self.assertEqual(p.stdout, (ROOT / 'examples/cohort.txt').read_text())
        for example, expected in [('unchanged', 0), ('underflow', 1), ('overflow', 1)]:
            p = self.run_cli(f'examples/{example}.json')
            self.assertEqual(p.returncode, expected, p.stderr)
        p = self.run_cli('--help')
        self.assertEqual(p.returncode, 0)

    def test_invalid_arguments_and_data_no_partial_report(self):
        for args in [('absent.json',), ('examples/cohort.json', '--top', '-1'),
                     ('examples/cohort.json', '--top', 'x'), ('examples/cohort.json', '--format', 'yaml'),
                     ('examples/records.json', '--field', 'missing')]:
            p = self.run_cli(*args)
            self.assertEqual(p.returncode, 2)
            self.assertEqual(p.stdout, '')
            self.assertNotIn('Traceback', p.stderr)

    def test_zero_evidence_still_fails(self):
        p = self.run_cli('examples/cohort.json', '--top', '0', '--format', 'json')
        self.assertEqual(p.returncode, 1)
        result = json.loads(p.stdout)
        self.assertEqual(result['collisions'], [])
        self.assertEqual(result['omitted_collision_groups'], 2)
        self.assertEqual(result['new_equal_pairs'], 3)


if __name__ == '__main__':
    unittest.main()
