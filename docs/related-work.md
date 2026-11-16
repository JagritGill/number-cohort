# Related work and provenance

Research date: 2026-11-16, before implementation. Queries included:

- `JSON numeric identifier precision collision audit tool binary64 github`
- `JSON number precision loss checker large integer duplicate collisions tool`
- `site:github.com binary64 json number collisions lossless-json`
- `JSON "precision" "collision" "audit" numbers github tool`
- `numeric key rounding collision detector JSON binary64 distinct identifiers`
- `"number-cohort" github`

The local portfolio and public personal repository names were also checked.
Search results are not proof of name availability or worldwide novelty.

## Closest documented alternatives

| Primary source | Substantial overlap | Deliberate scope here |
| --- | --- | --- |
| [json-portage](https://github.com/KanadeK/json-portage) | An offline Python portability CLI preserving numeric spellings and detecting unsafe integers, range and Unicode hazards. Its documented profile excludes ordinary decimal rounding checks. | Audit the actual many-to-one mapping of a supplied numeric cohort, including decimal rounding. Separate pre-existing numeric equality from newly equal record pairs. This is not a replacement for its broader wire checks. |
| [ToolsFYI JSON Number Precision Inspector](https://www.toolsfyi.com/tools/data-tools/json-number-precision-inspector) | Browser inspection of raw numeric tokens, unsafe integers and nonfinite binary64 conversion, with paths and offsets. It explicitly does not flag every decimal rounding difference. | Report collision groups and one-based record witnesses for selected values. The CLI does not provide a general document-path inspector or browser UI. |
| [lossless-json](https://github.com/josdejong/lossless-json) | A JavaScript parsing/stringifying library that preserves numeric information and provides safe conversion and numeric comparison helpers. | An offline audit rather than a parser replacement: diagnose which selected exact values collapse under conversion, without rewriting the input or providing a JavaScript integration. |

These descriptions concern published documentation, not exhaustive feature
testing. No claim is made that cohort auditing is globally unique or unavailable
elsewhere. No comparator implementation, tests, fixtures or documentation prose
were copied, cloned or translated. No online tool processed project data.

## Standards and implementation concepts

- [RFC 8259, numbers](https://www.rfc-editor.org/rfc/rfc8259#section-6)
  defines JSON number grammar and discusses interoperable range/precision.
- [RFC 7493, I-JSON](https://www.rfc-editor.org/rfc/rfc7493)
  provides established binary64 interoperability context. This tool is not an
  I-JSON conformance validator.
- Python's [Decimal](https://docs.python.org/3/library/decimal.html) and
  [numeric types](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex)
  supply exact decimal construction, integer ratios and binary floating-point
  conversion. Exact rational equality and counting unordered pairs are standard
  techniques, not new algorithms claimed by this project.

The runnable example combines integers above 2^53, unequal decimal spellings
that round to the same binary64 number, and spellings already equal as exact
numbers. It demonstrates why a warning about a single unsafe value is a different
question from whether *this collection* acquires new equality.

Runtime implementation, examples and tests were created from scratch with AI
assistance for this project. Python's standard library supplies parsing and
arithmetic; no runtime dependencies are vendored. Portfolio release conventions
and previously verified CI action pins are reused, not another project's
substantive implementation. See [notices](../NOTICE.md) for licensing and
[architecture](architecture.md) for the exact model and limits.
