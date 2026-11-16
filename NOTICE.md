# Attribution and dependencies

Original project files use the [MIT license](LICENSE). Implementation,
documentation, synthetic fixtures and tests were created with AI assistance.
This notice makes no claim of sole human authorship or algorithmic novelty.

Runtime: Python standard library only. Python provides JSON parsing, exact
Decimal construction, Fraction arithmetic and binary64 conversion under the
[Python license](https://docs.python.org/3/license.html). Python is not vendored
or relicensed here. No third-party runtime package, comparator code, fixture or
asset is included. Research sources and shared concepts are credited in
[related work](docs/related-work.md).

CI uses [actions/checkout](https://github.com/actions/checkout) and
[actions/setup-python](https://github.com/actions/setup-python), both MIT-licensed
upstream, pinned to full commit identifiers from a previously verified portfolio
workflow. The actions are referenced, not vendored or relicensed. The workflow
definition uses read-only repository permission and does not retain checkout
credentials. Release conventions and these action references follow earlier
personal portfolio work; application code and tests were implemented independently.

Local tests and CI are distinct observations. Consult the actual workflow run
for its commit and result; configuration alone is not proof that CI passed.
