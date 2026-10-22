"""Validate independent-group power and the distinction between per-group and total n."""

import contextlib
import io
import math
import tempfile
import unittest
from pathlib import Path

from scipy.stats import nct, t

from scripts.power_analysis import independent_power, parse_args, planning_row, required_per_group, run


class PowerAnalysisTests(unittest.TestCase):
    def test_matches_independent_noncentral_t_both_tails(self):
        for per_group in (8, 26, 64):
            for effect in (0.0, 0.2, 0.5, 0.8):
                with self.subTest(per_group=per_group, effect=effect):
                    degrees_of_freedom = 2 * per_group - 2
                    critical = t.ppf(0.975, degrees_of_freedom)
                    noncentrality = effect * math.sqrt(per_group / 2)
                    expected = nct.cdf(-critical, degrees_of_freedom, noncentrality) + nct.sf(
                        critical, degrees_of_freedom, noncentrality)
                    self.assertAlmostEqual(independent_power(effect, per_group), expected, places=10)

    def test_minimum_is_first_integer_per_group_to_reach_target(self):
        for effect in (0.2, 0.3, 0.4, 0.5, 0.8):
            with self.subTest(effect=effect):
                _, per_group = required_per_group(effect)
                self.assertGreaterEqual(independent_power(effect, per_group), 0.8)
                self.assertLess(independent_power(effect, per_group - 1), 0.8)

    def test_teammate_reference_sample_sizes_and_recruitment(self):
        args = parse_args([])
        for effect, per_group, total, recruits in ((0.5, 64, 128, 144), (0.8, 26, 52, 58)):
            with self.subTest(effect=effect):
                row = planning_row(effect, args)
                self.assertEqual(row["minimum_complete_participants_per_group"], per_group)
                self.assertEqual(row["total_complete_participants"], total)
                self.assertEqual(row["initial_recruitment_total"], recruits)
                self.assertGreaterEqual(row["power_at_required_sample"], 0.8)

    def test_two_sided_symmetry_and_type_one_error(self):
        self.assertAlmostEqual(independent_power(0.5, 64), independent_power(-0.5, 64))
        self.assertAlmostEqual(independent_power(0, 64), 0.05, places=10)

    def test_selected_total_must_support_equal_allocation(self):
        for total in (2, 3, 25):
            with self.subTest(total=total), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    parse_args(["--participants", str(total)])
        self.assertEqual(parse_args(["--participants", "52"]).participants, 52)

    def test_score_sd_replaces_paired_difference_sd(self):
        for invalid in ("0", "-1", "nan", "inf"):
            with self.subTest(invalid=invalid), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    parse_args(["--score-sd", invalid])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parse_args(["--difference-sd", "2"])

    def test_generated_outputs_count_people_and_one_quiz_each(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            summary = run(parse_args(["--output-dir", directory]))
            self.assertEqual(summary["minimum_complete_participants_per_group"], 64)
            self.assertEqual(summary["total_complete_participants"], 128)
            self.assertEqual(summary["quiz_administrations_at_target"], 128)
            self.assertEqual(summary["large_effect_scenario"]["total_complete_participants"], 52)
            self.assertEqual(summary["large_effect_scenario"]["mean_difference_questions_at_assumed_score_sd"], 1.6)
            self.assertTrue((Path(directory) / "score_sd_sensitivity.csv").exists())
            self.assertFalse((Path(directory) / "difference_sd_sensitivity.csv").exists())


if __name__ == "__main__":
    unittest.main()
