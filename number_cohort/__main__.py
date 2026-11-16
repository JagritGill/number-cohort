"""Offline CLI; 0=cohort gate passes, 1=collision/overflow, 2=invalid input."""

import argparse
import json
import sys

from .core import AuditError, analyze
from .input import load_numbers
from .report import text_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit new equality when JSON numeric values become binary64 keys.")
    parser.add_argument("input", help="stable local UTF-8 JSON array file")
    parser.add_argument("--field", help="literal direct member in each object; default: array of numbers")
    parser.add_argument("--top", type=int, default=10, help="collision groups to show (0..50; totals unaffected)")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    try:
        # Reject the option before any input read.
        if not 0 <= args.top <= 50:
            raise AuditError("top must be an integer from 0 to 50")
        result = analyze(load_numbers(args.input, field=args.field), top=args.top)
    except AuditError as exc:
        print(f"number-cohort: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result.to_dict(), indent=2, allow_nan=False) if args.format == "json"
          else text_report(result), end="\n" if args.format == "json" else "")
    return int(result.gate_failed)


if __name__ == "__main__":
    raise SystemExit(main())
