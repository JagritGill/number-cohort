"""Compare exact decimal equality to finite binary64 numeric equality."""

from dataclasses import asdict, dataclass, field
from decimal import Decimal, DecimalException
from fractions import Fraction
import math
import re
import struct
import sys

MAX_RECORDS = 10_000
MAX_TOKEN = 128
MAX_EXPONENT = 400
MAX_TOP = 50
NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\Z")


class AuditError(ValueError):
    """Unsupported or invalid input; messages do not include payload values."""


@dataclass(frozen=True)
class Witness:
    record: int
    occurrences: int


@dataclass(frozen=True)
class Collision:
    binary64_hex: str
    records: int
    distinct_exact_values: int
    new_equal_pairs: int
    witnesses: tuple[Witness, ...]
    omitted_exact_values: int


@dataclass(frozen=True)
class Report:
    records: int
    exact_rows: int
    rounded_rows: int
    underflow_rows: int
    overflow_rows: int
    negative_zero_rows: int
    finite_source_values: int
    binary64_keys: int
    lost_distinctions: int
    collision_groups: int
    new_equal_pairs: int
    collisions: tuple[Collision, ...]
    omitted_collision_groups: int
    overflow_records: tuple[int, ...]
    omitted_overflow_records: int

    @property
    def gate_failed(self) -> bool:
        return self.collision_groups > 0 or self.overflow_rows > 0

    def to_dict(self) -> dict:
        return {"schema_version": 1, "gate_failed": self.gate_failed, **asdict(self)}


@dataclass
class _Group:
    first_record: int
    # Exact value -> [count, first one-based record]. Insertion order is evidence order.
    values: dict[Fraction, list[int]] = field(default_factory=dict)
    records: int = 0


def _check_platform() -> None:
    f = sys.float_info
    if (f.radix, f.mant_dig, f.max_exp, f.rounds, struct.calcsize("d")) != (2, 53, 1024, 1, 8):
        raise AuditError("requires an IEEE 754 binary64 host with nearest rounding")


def _exact(token: str, record: int) -> Fraction:
    if type(token) is not str or len(token) > MAX_TOKEN or NUMBER.fullmatch(token) is None:
        raise AuditError(f"record {record}: expected a JSON number token of at most {MAX_TOKEN} characters")
    try:
        value = Decimal(token)  # Exact string construction, independent of context precision.
    except DecimalException:
        raise AuditError(f"record {record}: decimal exponent exceeds supported bounds") from None
    exponent = value.as_tuple().exponent
    if not isinstance(exponent, int) or abs(exponent) > MAX_EXPONENT:
        raise AuditError(f"record {record}: decimal tuple exponent must be within +/-{MAX_EXPONENT}")
    return Fraction(*value.as_integer_ratio())


def analyze(literals: list[str], *, top: int = 10) -> Report:
    """Audit a bounded list of exact JSON number spellings, without mutating it.

    Equality is numeric: source spellings 1/1.0/1e0 and signed zeros are already
    equal. Overflow is an independent gate failure, excluded from finite groups.
    Evidence truncation never changes totals or the gate.
    """
    _check_platform()
    if type(literals) is not list or len(literals) > MAX_RECORDS:
        raise AuditError(f"expected a list of at most {MAX_RECORDS} number tokens")
    if type(top) is not int or not 0 <= top <= MAX_TOP:
        raise AuditError(f"top must be an integer from 0 to {MAX_TOP}")
    groups: dict[float, _Group] = {}
    counts = {"exact": 0, "rounded": 0, "underflow": 0, "overflow": 0}
    overflow_records: list[int] = []
    negative_zero = 0
    for record, token in enumerate(literals, 1):
        exact = _exact(token, record)
        target = float(token)
        if not math.isfinite(target):
            counts["overflow"] += 1
            if len(overflow_records) < 5:
                overflow_records.append(record)
            continue
        if target == 0 and math.copysign(1.0, target) < 0:
            negative_zero += 1
        kind = ("underflow" if exact != 0 and target == 0 else
                "exact" if exact == Fraction.from_float(target) else "rounded")
        counts[kind] += 1
        group = groups.setdefault(target, _Group(record))
        group.records += 1
        value_count = group.values.setdefault(exact, [0, record])
        value_count[0] += 1

    ranked: list[tuple[int, int, Collision]] = []
    source_values = 0
    for target, group in groups.items():
        source_values += len(group.values)
        if len(group.values) < 2:
            continue
        n = group.records
        pairs = n * (n - 1) // 2 - sum(c * (c - 1) // 2 for c, _ in group.values.values())
        witnesses = tuple(Witness(first, count) for count, first in list(group.values.values())[:3])
        evidence = Collision(
            (0.0 if target == 0 else target).hex(), n, len(group.values), pairs,
            witnesses, max(0, len(group.values) - len(witnesses)),
        )
        ranked.append((-pairs, group.first_record, evidence))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return Report(
        len(literals), counts["exact"], counts["rounded"], counts["underflow"],
        counts["overflow"], negative_zero, source_values, len(groups),
        source_values - len(groups), len(ranked), sum(-r[0] for r in ranked),
        tuple(r[2] for r in ranked[:top]), max(0, len(ranked) - top),
        tuple(overflow_records), counts["overflow"] - len(overflow_records),
    )
