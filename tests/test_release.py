import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('release_check', ROOT / 'scripts/check_release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in release.FILES:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def test_current_inventory(self):
        self.assertEqual(release.check(self.root)['files'], len(release.FILES))

    def test_unintended_file_and_symlink(self):
        path = self.root / 'unexpected.txt'
        path.write_text('synthetic')
        with self.assertRaises(ValueError):
            release.check(self.root)
        path.unlink()
        (self.root / 'README.md').unlink()
        (self.root / 'README.md').symlink_to(self.root / 'NOTICE.md')
        with self.assertRaises(ValueError):
            release.check(self.root)

    def test_sensitive_patterns_and_broken_link(self):
        path = self.root / 'README.md'
        for text in ['gh' + 'p_' + 'a' * 36, '/' + 'Users/example/private.txt', '[missing](missing.md)']:
            with self.subTest(kind=text[:3]):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    release.check(self.root)

    def test_syntax_and_mode(self):
        path = self.root / 'number_cohort/core.py'
        path.write_text('def broken(:\n')
        with self.assertRaises(SyntaxError):
            release.check(self.root)
        path.write_text('pass\n')
        path.chmod(0o755)
        with self.assertRaises(ValueError):
            release.check(self.root)


if __name__ == '__main__':
    unittest.main()
