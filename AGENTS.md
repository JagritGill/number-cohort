# Working on number-cohort

Purpose: audit new numeric equality within one JSON cohort after binary64
conversion. Start with [README](README.md), [architecture](docs/architecture.md)
and [related work](docs/related-work.md). This is an offline read-only CLI.

## Map and invariants

- `number_cohort/input.py`: bounded local JSON loader, token preservation,
  duplicate/member/string validation and literal direct-field selection.
- `core.py`: exact rational source classes, binary64 groups, counts and witnesses.
- `report.py`, `__main__.py`: stable text/JSON reporting and exit contract.
- `examples/`: synthetic runnable fixtures; `cohort.txt` is exact CLI output.
- `tests/`: pairwise oracle, edge inputs, subprocess behavior and release mutations.
- `scripts/`: examples and release checks; `.github/workflows/ci.yml`: pinned CI.

Source equality is numeric, including signed zero. Never replace exact token
parsing with already-rounded floats. Never count pre-existing equal values as new
pairs. Exclude overflow from finite counts and fail its gate independently.
Evidence caps must not alter totals or exits. Preserve deterministic ranking,
one-based record references and non-disclosure of raw payload values. The derived
hex value is still information; do not call reports anonymized.

## Verified local commands

From the repo root, with installed Python (no setup/install step):

```sh
python3 -B -m unittest discover -s tests -v
python3.13 -B -m unittest discover -s tests -v
python3 -B scripts/check_examples.py
python3 -B scripts/check_release.py
python3 -B scripts/check_release.py --json
git diff --check
```

Local runtimes: CPython 3.15.0 (`python3`) and 3.13.5 (`python3.13`). Do not assume
those executable names on other machines. [README examples](README.md) specify
expected exits; findings exit 1 intentionally, invalid inputs exit 2. The examples
script asserts the expected codes and itself exits 0. No dependencies to install.
No configured static type checker or full linter: release syntax parsing is
neither. CI configuration is not a passed run; record actual final-commit status.

## Change boundaries and handoff

Preserve owner edits; inspect working tree and coordinate ownership before edits.
Only work in this repo. No private or employer inputs, live credentials, network
features, hardware, paid services or CodeRabbit. Do not push, merge, change account
settings or publish without applicable task authorization. Do not weaken CI or
hide failures. Use synthetic fixtures and local review/tests.

For semantic changes, add a counterexample/regression test and extend a direct
oracle where useful. Exercise actual CLI output/errors when changing parsing or
reporting. Keep limits explicit, validate before reporting, and preserve all
validation even for unselected payloads. Ordinary rounding alone is not a gate
failure. Do not add automatic repair or imply universal portability.

Update release inventory when adding intended files; rerun checks on the final
content and inspect staged scope. Handoff with exact commit, dirty paths, actual
commands/results, expected nonzero exits, unrun checks and limitations. Keep
machine-specific logs, local paths and coordination records outside the release.
See [NOTICE](NOTICE.md) and [LICENSE](LICENSE) before adding dependencies/material.
