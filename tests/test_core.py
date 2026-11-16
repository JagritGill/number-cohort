from decimal import localcontext
from fractions import Fraction
from itertools import combinations, product
import unittest
from unittest.mock import patch

from number_cohort import AuditError, analyze
from number_cohort.core import MAX_RECORDS


class CoreTests(unittest.TestCase):
    def test_demonstration(self):
        r = analyze(["9007199254740992", "9007199254740993", "9007199254740992",
                     "0.1", "0.10000000000000001", "1", "1.0", "1e0"])
        self.assertEqual((r.records, r.exact_rows, r.rounded_rows), (8, 5, 3))
        self.assertEqual((r.finite_source_values, r.binary64_keys, r.lost_distinctions), (5, 3, 2))
        self.assertEqual((r.collision_groups, r.new_equal_pairs), (2, 3))
        self.assertEqual([[(w.record, w.occurrences) for w in c.witnesses] for c in r.collisions],
                         [[(1, 2), (2, 1)], [(4, 1), (5, 1)]])
        self.assertTrue(r.gate_failed)

    def test_already_equal_and_signed_zero(self):
        r = analyze(["1", "1.0", "1e0", "-0", "0", "-0.0"])
        self.assertEqual((r.finite_source_values, r.binary64_keys, r.new_equal_pairs), (2, 2, 0))
        self.assertEqual(r.negative_zero_rows, 2)
        self.assertFalse(r.gate_failed)

    def test_isolated_rounding_pass_is_not_exactness(self):
        r = analyze(["0.1", "9007199254740993"])
        self.assertEqual(r.rounded_rows, 2)
        self.assertFalse(r.gate_failed)

    def test_positive_negative_ties_to_even(self):
        for sign in ("", "-"):
            r = analyze([sign + s for s in ("9007199254740992", "9007199254740993",
                                           "9007199254740995", "9007199254740996")])
            self.assertEqual((r.collision_groups, r.new_equal_pairs, r.rounded_rows), (2, 2, 2))

    def test_underflow_joining_signed_zero(self):
        r = analyze(["-1e-400", "0", "1e-400", "-0"])
        self.assertEqual((r.exact_rows, r.underflow_rows, r.new_equal_pairs), (2, 2, 5))
        self.assertEqual(r.negative_zero_rows, 2)
        self.assertEqual(r.collisions[0].binary64_hex, "0x0.0p+0")

    def test_subnormal_boundary_and_overflow(self):
        r = analyze(["2e-324", "3e-324", "4e-324", "1.7976931348623157e308", "1e400", "-1e400"])
        self.assertEqual((r.underflow_rows, r.rounded_rows, r.overflow_rows), (1, 3, 2))
        self.assertEqual((r.collision_groups, r.new_equal_pairs), (1, 1))
        self.assertEqual(r.overflow_records, (5, 6))
        self.assertTrue(r.gate_failed)

    def test_overflow_witness_bound_and_empty_input(self):
        r = analyze(["1e400"] * 9)
        self.assertEqual((r.finite_source_values, r.binary64_keys, r.collision_groups), (0, 0, 0))
        self.assertEqual((r.overflow_records, r.omitted_overflow_records), ((1, 2, 3, 4, 5), 4))
        self.assertFalse(analyze([]).gate_failed)

    def test_evidence_truncation_order_and_value_cap(self):
        tokens = ["1.00000000000000000" + str(i) for i in range(6)] + ["2", "2.00000000000000001"]
        r = analyze(tokens, top=1)
        self.assertEqual((r.collision_groups, r.new_equal_pairs, r.omitted_collision_groups), (2, 16, 1))
        self.assertEqual(r.collisions[0].omitted_exact_values, 3)
        hidden = analyze(tokens, top=0)
        self.assertEqual(hidden.new_equal_pairs, r.new_equal_pairs)
        self.assertTrue(hidden.gate_failed)
        self.assertEqual(hidden.collisions, ())
        tied = analyze(["2", "2.00000000000000001", "1", "1.00000000000000001"])
        self.assertEqual([c.witnesses[0].record for c in tied.collisions], [1, 3])

    def test_invalid_api_and_bounds(self):
        for token in ["01", "+1", ".1", "1.", " 1", "1\n", "NaN", "Infinity", "1e401",
                      "1e-401", "1e" + "9" * 110, "1" * 129, True, 1, None]:
            with self.subTest(token_type=type(token).__name__), self.assertRaises(AuditError):
                analyze([token])
        for data in [("1",), ["1"] * (MAX_RECORDS + 1), "1"]:
            with self.assertRaises(AuditError):
                analyze(data)
        for top in [True, -1, 51, "1", 1.0]:
            with self.assertRaises(AuditError):
                analyze(["1"], top=top)
        self.assertEqual(analyze(["1"] * MAX_RECORDS).records, MAX_RECORDS)
        with patch("number_cohort.core.struct.calcsize", return_value=4), self.assertRaises(AuditError):
            analyze(["1"])

    def test_decimal_context_and_input_unchanged(self):
        values = ["0.1", "0.10000000000000001", "1e-400", "1e400"]
        original = values[:]
        baseline = analyze(values)
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(analyze(values), baseline)
        self.assertEqual(values, original)

    def test_exhaustive_direct_pair_oracle(self):
        # Pairwise definition, independent of the implementation's frequency formula.
        alphabet = ["0", "-0", "1e-400", "-1e-400", "1", "1.0",
                    "1.00000000000000001", "9007199254740992", "9007199254740993"]
        scenarios = 0
        for length in range(5):
            for values in product(alphabet, repeat=length):
                exact = [Fraction(s) for s in values]
                targets = [float(s) for s in values]
                newly_equal = [(i, j) for i, j in combinations(range(length), 2)
                               if exact[i] != exact[j] and targets[i] == targets[j]]
                result = analyze(list(values), top=0)
                self.assertEqual(result.new_equal_pairs, len(newly_equal))
                self.assertEqual(result.lost_distinctions, len(set(exact)) - len(set(targets)))
                self.assertEqual(result.gate_failed, bool(newly_equal))
                scenarios += 1
        self.assertEqual(scenarios, 7381)


if __name__ == "__main__":
    unittest.main()
