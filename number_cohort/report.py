"""Deterministic, bounded human-readable summaries."""

from .core import Report


def text_report(report: Report) -> str:
    lines = [
        f"records={report.records} exact={report.exact_rows} rounded={report.rounded_rows} "
        f"underflow={report.underflow_rows} overflow={report.overflow_rows}",
        f"finite source values={report.finite_source_values} binary64 keys={report.binary64_keys} "
        f"lost distinctions={report.lost_distinctions}",
        f"collision groups={report.collision_groups} new equal pairs={report.new_equal_pairs}",
        "gate=FAIL" if report.gate_failed else "gate=PASS (cohort equality only)",
    ]
    for c in report.collisions:
        witnesses = ", ".join(f"{w.record} x{w.occurrences}" for w in c.witnesses)
        lines.append(f"  {c.binary64_hex}: records={c.records} exact values={c.distinct_exact_values} "
                     f"new pairs={c.new_equal_pairs}; first records [{witnesses}] "
                     f"omitted values={c.omitted_exact_values}")
    if report.omitted_collision_groups:
        lines.append(f"omitted collision groups={report.omitted_collision_groups}")
    if report.overflow_rows:
        lines.append(f"overflow records={','.join(map(str, report.overflow_records))}; "
                     f"omitted={report.omitted_overflow_records}")
    if report.negative_zero_rows:
        lines.append(f"negative binary64 zero rows={report.negative_zero_rows} (numeric zero equality)")
    return "\n".join(lines) + "\n"
