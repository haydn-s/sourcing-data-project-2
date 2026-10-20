"""Check the scientific calculation against the noncentral t distribution."""

import math
import unittest

from scipy.stats import nct, t

from scripts.power_analysis import balanced_count, paired_power, required_pairs


class PowerAnalysisTests(unittest.TestCase):
    def test_matches_noncentral_t_both_tails(self):
        for n in (12, 36, 100):
            for effect in (0.0, 0.2, 0.5, 0.8):
                with self.subTest(n=n, effect=effect):
                    critical = t.ppf(0.975, n - 1)
                    noncentrality = effect * math.sqrt(n)
                    expected = nct.cdf(-critical, n - 1, noncentrality) + nct.sf(critical, n - 1, noncentrality)
                    self.assertAlmostEqual(paired_power(effect, n), expected, places=10)

    def test_minimum_is_first_integer_to_reach_target(self):
        for effect in (0.2, 0.3, 0.4, 0.5, 0.8):
            with self.subTest(effect=effect):
                _, n = required_pairs(effect)
                self.assertGreaterEqual(paired_power(effect, n), 0.8)
                self.assertLess(paired_power(effect, n - 1), 0.8)
        self.assertEqual(required_pairs(0.5)[1], 34)

    def test_balanced_target_and_two_sided_symmetry(self):
        self.assertEqual(balanced_count(34), 36)
        self.assertEqual(balanced_count(36), 36)
        self.assertAlmostEqual(paired_power(0.5, 36), paired_power(-0.5, 36))
        self.assertAlmostEqual(paired_power(0, 36), 0.05, places=10)


if __name__ == "__main__":
    unittest.main()
