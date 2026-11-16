"""Local allowlist, syntax, Markdown-target and heuristic disclosure checks."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import unquote, urlsplit

FILES = frozenset('''
.github/workflows/ci.yml
.gitignore
AGENTS.md
LICENSE
NOTICE.md
README.md
docs/architecture.md
docs/related-work.md
examples/cohort.json
examples/cohort.txt
examples/overflow.json
examples/records.json
examples/unchanged.json
examples/underflow.json
number_cohort/__init__.py
number_cohort/__main__.py
number_cohort/core.py
number_cohort/input.py
number_cohort/report.py
scripts/check_examples.py
scripts/check_release.py
tests/test_core.py
tests/test_input_cli.py
tests/test_release.py
'''.split())
IGNORED = {'.git', '__pycache__', 'out'}
PATTERNS = [
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?' + r'PRIVATE KEY-----'),
    re.compile(r'gh[pousr]_' + r'[A-Za-z0-9]{30,}'),
    re.compile(r'github_pat_' + r'[A-Za-z0-9_]{30,}'),
    re.compile(r'AKIA' + r'[A-Z0-9]{16}'),
    re.compile(r'/' + r'Users/[^\s/]+/'),
    re.compile(r'/' + r'home/[^\s/]+/'),
]


def check(root: Path) -> dict:
    found = set()
    for directory, dirs, names in os.walk(root, followlinks=False):
        current = Path(directory)
        for name in dirs + names:
            if (current / name).is_symlink():
                raise ValueError('symlink in release tree')
        dirs[:] = [d for d in dirs if d not in IGNORED]
        for name in names:
            if name.endswith('.pyc'):
                continue
            found.add((current / name).relative_to(root).as_posix())
    if found != FILES:
        raise ValueError(f'inventory mismatch: missing={sorted(FILES - found)}, extra={sorted(found - FILES)}')
    hashes = {}
    links = 0
    syntax = 0
    for name in sorted(FILES):
        path = root / name
        mode = path.stat().st_mode
        if not stat.S_ISREG(mode) or mode & 0o111:
            raise ValueError(f'non-regular or executable release entry: {name}')
        raw = path.read_bytes()
        if len(raw) > 128_000:
            raise ValueError(f'unexpectedly large release file: {name}')
        text = raw.decode('utf-8')
        if any(pattern.search(text) for pattern in PATTERNS):
            raise ValueError(f'credential/private-path heuristic match: {name}')
        if name.endswith('.py'):
            ast.parse(text, filename=name)
            syntax += 1
        if name.endswith('.md'):
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if urlsplit(target).scheme:
                    continue
                relative = unquote(target.split('#', 1)[0])
                if not relative:
                    continue
                resolved = (path.parent / relative).resolve()
                if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
                    raise ValueError(f'broken or escaping local Markdown target: {name}')
                links += 1
        hashes[name] = hashlib.sha256(raw).hexdigest()
    return {'files': len(hashes), 'local_links': links, 'python_syntax_files': syntax,
            'sha256': hashes, 'limits': 'Heuristic scan only; no static type check, remote links or Git history scan.'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        result = check(Path(__file__).resolve().parents[1])
    except (ValueError, OSError, SyntaxError) as exc:
        raise SystemExit(f'release check failed: {exc}') from None
    print(json.dumps(result, indent=2) if args.json else
          f"release checks passed: {result['files']} files, {result['local_links']} local links, "
          f"{result['python_syntax_files']} Python syntax parses; heuristic scan only")


if __name__ == '__main__':
    main()
