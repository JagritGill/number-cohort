# Architecture and tradeoffs

## Flow

1. `input.py` reads at most 2 MiB + 1 bytes from a stable regular file and decodes
   UTF-8. Standard JSON parsing uses number callbacks to preserve lexical tokens
   and object-pair callbacks to reject duplicate names. An iterative tree walk
   validates bounds and strings; then a numeric array or direct field is selected.
2. `core.py` parses each selected token as an exact Decimal and integer ratio,
   represented by Fraction. It separately converts the original token to the
   host's binary64 float. Decimal context precision does not round string parsing.
3. Nonfinite conversions are counted as overflow and excluded from finite groups.
   Other rows are partitioned into exact, rounded, or nonzero-to-zero underflow.
4. A map from binary64 numeric key to exact-value frequencies records counts and
   first record positions. For a group of n records with exact-value frequencies
   c, newly equal pairs are `n*(n-1)/2 - sum(c*(c-1)/2)`. No record pairs are built.
5. Groups with multiple exact values are ranked; `report.py` formats bounded text
   evidence. `__main__.py` emits text/JSON and applies the equality/overflow gate.

`Report`, `Collision` and `Witness` are frozen dataclasses. The input list is not
mutated. JSON schema version 1 mirrors the dataclasses and includes `gate_failed`.
Plain integers are used for aggregate counts. If a different downstream report
consumer introduces its own number conversion, that consumer needs its own checks.

## Deliberate semantics

Numeric equality, not spelling, defines source classes. `1`, `1.0`, and `1e0`
are equal before conversion. Signed zeros share one numeric class; the displayed
zero-group target is normalized to positive zero. Negative binary64 zero gets a
separate row count. Overflow cannot masquerade as a finite collision. A rounded
value with no partner does not fail the equality gate.

The tool relies on the installed Python decimal parser and float conversion,
not an independent implementation of IEEE rounding. Host checks require radix 2,
53-bit precision, exponent limit 1024, nearest rounding and an 8-byte double.
These checks plus tests support the intended environment; they do not certify
every parser or platform. No JavaScript runtime is needed to use the CLI.

## Bounds

| Resource | Limit |
| --- | --- |
| Input bytes | 2,097,152; one bounded read, not streaming |
| Root array records / API token list | 10,000 |
| Number spelling anywhere in input | 128 characters |
| Selected Decimal tuple exponent | -400 through +400, inclusive |
| Decoded nesting depth | 64, root at depth 0 |
| Decoded nodes, including object keys | 100,000 |
| Decoded string or key / field selector | 16,384 Unicode code points; no unpaired surrogates |
| Collision evidence | 0..50 groups, 3 distinct-value witnesses each |
| Overflow evidence | First 5 record positions |

The Decimal tuple exponent accounts for fractional digits: `1.0e-400` has tuple
exponent -401 and is rejected even though `1e-400` is allowed. This explicit
resource rule is not a judgment that the first value is invalid JSON. The API
rejects non-string tokens and non-list collections. Unselected numeric payloads
receive token-length checks but are not subject to selected-value exponent analysis.

The JSON decoder allocates the bounded document **before** decoded depth/node
checks; recursion errors are rejected. Memory includes raw bytes, decoded text,
the parsed tree and aggregate maps. Expected hashing work is linear in record
count plus token/rational arithmetic; sorting g collision groups takes O(g log g).
Storage is O(input size + distinct exact values). These are design bounds, not
measured speed or memory claims.

## Limits and safety

Only one selected cohort is compared. There is no nested selector, cross-file
join, automatic key discovery, general JSON validator, correction, upload or
network operation. Numbers already rounded by an upstream serializer cannot be
recovered. Only the supplied sample is audited; it says nothing about future IDs.

Use trusted, stable local files. Symlinks, directories and devices are rejected,
but the path check and open are not a defense against malicious concurrent
replacement. The reader is not a hostile-filesystem sandbox. Output omits source
lexemes and payloads, but derived hex values and record positions still disclose
information. The [release checker](../scripts/check_release.py) uses a finite
allowlist and heuristics, not comprehensive security or provenance analysis.

## Testing and ownership

The checked-in pairwise oracle directly enumerates record pairs over 7,381 small
cohorts. It tests the frequency-based algorithm against the definition, including
pre-existing equality and signed underflow. Separate boundary and subprocess tests
cover tie-to-even conversion, subnormals, overflow, evidence caps and exit behavior.
Release tests mutate isolated temporary copies only. CI action pins and external
attribution are documented in [NOTICE](../NOTICE.md).

Contributor boundaries and commands are in [AGENTS.md](../AGENTS.md).
