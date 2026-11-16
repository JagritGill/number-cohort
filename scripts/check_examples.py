"""Exercise every documented CLI example with explicit expected exit status."""

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cases = [
        (['examples/cohort.json'], 1),
        (['examples/cohort.json', '--format', 'json'], 1),
        (['examples/cohort.json', '--top', '0', '--format', 'json'], 1),
        (['examples/records.json', '--field', 'id', '--format', 'json'], 1),
        (['examples/unchanged.json'], 0),
        (['examples/underflow.json'], 1),
        (['examples/overflow.json'], 1),
        (['--help'], 0),
    ]
    for args, expected in cases:
        p = subprocess.run([sys.executable, '-B', '-m', 'number_cohort', *args], cwd=ROOT,
                           capture_output=True, text=True, check=False)
        if p.returncode != expected or p.stderr:
            raise SystemExit(f'example failed: {args}, exit={p.returncode}, stderr={p.stderr}')
        if args == ['examples/cohort.json'] and p.stdout != (ROOT / 'examples/cohort.txt').read_text():
            raise SystemExit('text example changed')
        if '--format' in args:
            result = json.loads(p.stdout)
            expected_pairs = 1 if '--field' in args else 3
            if result['new_equal_pairs'] != expected_pairs or not result['gate_failed']:
                raise SystemExit('JSON example counts changed')
    print(f'{len(cases)} CLI examples passed (including intentional exit 1 findings)')


if __name__ == '__main__':
    main()
