# number-cohort

**Find distinct JSON numbers that become the same binary64 key.**

Before a numeric-ID collection crosses into JavaScript or another binary64
consumer, audit whether conversion introduces new equality in that collection.
An unsafe number warning is useful, but it does not say which records actually
collide. This offline CLI counts those collisions and gives bounded record
witnesses, without rewriting your input or materializing pairs.

For example, `9007199254740992` and `9007199254740993` become one binary64 value.
So do `0.1` and `0.10000000000000001`. But `1`, `1.0` and `1e0` were already equal
as exact numbers; the tool does not count them as new collisions.

## Run

Use an existing CPython 3.13 or 3.15 on an IEEE 754 binary64 host. From this
repository's root, no install, service, network connection or dependency download
is needed:

```sh
python3 -B -m number_cohort examples/cohort.json
```

This intentionally exits **1**, with exactly:

```text
records=8 exact=5 rounded=3 underflow=0 overflow=0
finite source values=5 binary64 keys=3 lost distinctions=2
collision groups=2 new equal pairs=3
gate=FAIL
  0x1.0000000000000p+53: records=3 exact values=2 new pairs=2; first records [1 x2, 2 x1] omitted values=0
  0x1.999999999999ap-4: records=2 exact values=2 new pairs=1; first records [4 x1, 5 x1] omitted values=0
```

`first records [1 x2, 2 x1]` means two distinct exact values, first seen at
records 1 and 2, occurring twice and once respectively. Their conversion creates
two new equal record pairs. It is not a listing of every colliding record.

More runnable examples:

```sh
python3 -B -m number_cohort examples/cohort.json --format json
python3 -B -m number_cohort examples/cohort.json --top 0 --format json
python3 -B -m number_cohort examples/records.json --field id --format json
python3 -B -m number_cohort examples/unchanged.json
python3 -B -m number_cohort examples/underflow.json
python3 -B -m number_cohort examples/overflow.json
python3 -B -m number_cohort --help
```

The unchanged example and help exit 0; all other examples above exit 1. The
records example has one new equal pair. Underflow collapses three distinct
values to zero, creating three pairs. Overflow reports an unsupported nonfinite
conversion, independently of collisions. `--top 0` hides collision evidence but
still fails the gate. To check every example with the expected statuses:

```sh
python3 -B scripts/check_examples.py
```

## Input and interpretation

- Supply one stable local UTF-8 JSON file whose root is an array of numbers.
  Alternatively, `--field NAME` selects a **literal direct member** in each object.
  It is not a path language; empty names and names containing slashes are literal.
- Every selected value must be numeric. Missing fields, strings, booleans, null,
  duplicate object names, NaN/Infinity and malformed JSON are errors. No coercion
  or skipping. Duplicate names and invalid strings are rejected even in payloads.
- Equality is mathematical numeric equality. Signed zero is one source and target
  key, matching numeric key equality rather than sign-sensitive `Object.is`.
  This does not audit string identifiers, integer-width casts or decimal databases.
- Exact, rounded, underflow and overflow row counts partition the selected input.
  Underflow means a nonzero exact value becomes zero. Negative-zero rows are an
  additional subset of finite rows and include negative underflow.
- Finite source values count distinct exact numbers whose conversions are finite.
  Binary64 keys count their distinct converted values. The difference is lost
  distinctions. Overflow rows are excluded from both counts and all collision groups.
- New equal pairs count unordered pairs of source **records** that were numerically
  unequal but now compare equal. Already-equal repetitions contribute no new pair.
- Evidence sorts by new equal pairs descending, then first record ascending. Show
  at most 50 groups (default 10), three distinct-value representatives per group,
  and five overflow records. One-based records are array positions, not line numbers.

| Exit | Meaning |
| --- | --- |
| 0 | No newly equal values or overflow in this cohort; input can be empty. |
| 1 | At least one collision group or overflow. A complete report is emitted. |
| 2 | Invalid/unsupported input or CLI argument. No partial report. |

**Exit 0 does not promise value preservation.** A single rounded `0.1`, or even a
single underflowed value, can pass because no other selected value collides with
it. Future values may collide. This is a collection equality gate, not a general
precision, schema, uniqueness or I-JSON validator. Applications should usually
use strings for identifiers requiring exact transport; this tool does not repair
or migrate them.

Reports omit original lexemes and payloads, but include derived target values in
hexadecimal and positional evidence. **Reports are not anonymized.** Error
messages from data validation avoid payload values; argparse may echo invalid
command arguments. Use synthetic input when sharing examples.

## API

```python
from number_cohort import analyze

report = analyze(["9007199254740992", "9007199254740993"], top=10)
assert report.new_equal_pairs == 1
assert report.gate_failed
```

`analyze` accepts a list of JSON numeric **spellings**, not already-rounded Python
floats. `load_numbers(path, field=None)` preserves the input tokens for it.
`Report.to_dict()` yields the JSON-ready schema (version 1). `AuditError` indicates
invalid input. See [architecture](docs/architecture.md) for bounds and algorithms.

## Verify and contribute

```sh
python3 -B -m unittest discover -s tests -v
python3 -B scripts/check_examples.py
python3 -B scripts/check_release.py
python3 -B scripts/check_release.py --json
git diff --check
```

Local verification used CPython 3.13.5 and 3.15.0. CI is configured for 3.13 and
3.15 on Linux; check the actual run for its result. Tests include a direct
pairwise oracle over 7,381 small cohorts, boundary conversions, actual CLI
invocations, invalid inputs and mutated release fixtures. The release script
parses Python syntax, checks inventory/local Markdown targets and scans selected
credential/private-path patterns. It is **not a static type checker**, full linter
or guarantee of secret/provenance safety. No static checker is configured.

See [AGENTS.md](AGENTS.md) for exact contributor commands and handoff boundaries,
[related work](docs/related-work.md) for substantial overlap with existing tools
and the narrower cohort use case, and [notices](NOTICE.md) for attribution.
Original project files use [MIT](LICENSE); AI assistance is disclosed.
