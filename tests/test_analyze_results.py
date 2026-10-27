"""Validate scoring, de-identification, and the Welch comparison of quiz results."""

import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from scipy import stats

from scripts.analyze_results import (
    GROUPS, RESEARCH_TEAM_RUN_IDS, ROOT, compare_groups, load_answer_key, load_runs, parse_args, run,
    score_runs,
)

KEY = load_answer_key(ROOT / "videos" / "answer_key.csv")
COLUMNS = ("run_id", "taker_name", "participant_group", "quiz_number", "video_id", "condition",
           "started_at", "total_time_seconds", "question_number", "answer_letter", "question_time_seconds")


def wrong(letter):
    return "A" if letter != "A" else "B"


def write_run(directory, run_id, name, group, correct, started_at, **overrides):
    """Write one raw CSV answering the first `correct` questions correctly."""
    rows = [{
        "run_id": run_id, "taker_name": name, "participant_group": group, "quiz_number": "1",
        "video_id": "A", "condition": GROUPS[group], "started_at": started_at, "total_time_seconds": "100.000",
        "question_number": str(q), "answer_letter": KEY[q] if q <= correct else wrong(KEY[q]),
        "question_time_seconds": "10.000",
    } for q in range(1, 11)]
    for row in rows:
        row.update(overrides)
    path = Path(directory) / f"{name}_VideoA_{run_id}_Assessment.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


# (run_id, name, group, correct answers, start time); listed out of chronological order on purpose.
SAMPLE = (
    ("run-c", "Carol Example", "1", 6, "2026-10-22T19:30:00.000Z"),
    ("run-a", "Alice Example", "1", 8, "2026-10-22T19:10:00.000Z"),
    ("run-e", "Erin Example", "1", 7, "2026-10-22T19:50:00.000Z"),
    ("run-b", "Bob Example", "2", 9, "2026-10-22T19:20:00.000Z"),
    ("run-d", "Dan Example", "2", 8, "2026-10-22T19:40:00.000Z"),
    ("run-f", "Fay Example", "2", 10, "2026-10-26T15:00:00.000Z"),
)


class AnalyzeResultsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.raw = self.root / "raw"
        self.raw.mkdir()
        for entry in SAMPLE:
            write_run(self.raw, *entry)

    def tearDown(self):
        self.directory.cleanup()

    def run_analysis(self, team=frozenset({"run-f"})):
        args = parse_args(["--raw-dir", str(self.raw), "--processed-dir", str(self.root / "processed"),
                           "--output-dir", str(self.root / "results")])
        with contextlib.redirect_stdout(io.StringIO()):
            return run(args, research_team_run_ids=team)

    def test_scores_against_key_with_chronological_ids(self):
        participants = score_runs(load_runs(self.raw), KEY, frozenset({"run-f"}))
        self.assertEqual([(p["participant_id"], p["score"]) for p in participants],
                         [("P01", 8), ("P02", 9), ("P03", 6), ("P04", 8), ("P05", 7), ("P06", 10)])
        self.assertEqual([p["research_team"] for p in participants], [0, 0, 0, 0, 0, 1])
        self.assertEqual(participants[5]["session_date_utc"], "2026-10-26")

    def test_outputs_contain_no_names_or_run_ids(self):
        self.run_analysis()
        outputs = [*(self.root / "processed").iterdir(), *(self.root / "results").iterdir()]
        self.assertTrue(outputs)
        for path in outputs:
            if path.suffix == ".png":
                continue
            text = path.read_text(encoding="utf-8")
            for run_id, name, *_ in SAMPLE:
                with self.subTest(path=path.name, name=name):
                    self.assertNotIn(name, text)
                    self.assertNotIn(run_id, text)

    def test_welch_comparison_matches_scipy_and_effect_size_formulas(self):
        result = compare_groups(score_runs(load_runs(self.raw), KEY, frozenset()))
        fidget, control = [8, 6, 7], [9, 8, 10]
        expected = stats.ttest_ind(fidget, control, equal_var=False)
        self.assertAlmostEqual(result["mean_difference_fidget_minus_no_fidget"], -2.0)
        self.assertAlmostEqual(result["welch_t"], expected.statistic)
        self.assertAlmostEqual(result["welch_df"], expected.df)
        self.assertAlmostEqual(result["p_value"], expected.pvalue)
        self.assertAlmostEqual(result["ci_95_low"], expected.confidence_interval().low)
        self.assertAlmostEqual(result["ci_95_high"], expected.confidence_interval().high)
        # Both groups have SD 1, so the pooled SD is 1 and d equals the mean difference.
        self.assertAlmostEqual(result["pooled_within_group_score_sd"], 1.0)
        self.assertAlmostEqual(result["pooled_sd_ci_95_low"], (4 / stats.chi2.ppf(0.975, 4)) ** 0.5)
        self.assertAlmostEqual(result["pooled_sd_ci_95_high"], (4 / stats.chi2.ppf(0.025, 4)) ** 0.5)
        self.assertAlmostEqual(result["cohens_d"], -2.0)
        self.assertAlmostEqual(result["hedges_g"], -2.0 * (1 - 3 / (4 * 4 - 1)))
        self.assertLess(result["power_at_planning_d_0_5"], result["power_at_planning_d_0_8"])

    def test_sensitivity_analysis_drops_only_research_team(self):
        summary = self.run_analysis()
        primary = summary["primary_all_participants"]
        sensitivity = summary["sensitivity_excluding_research_team"]
        self.assertEqual((primary["fidget"]["n"], primary["no_fidget"]["n"]), (3, 3))
        self.assertEqual((sensitivity["fidget"]["n"], sensitivity["no_fidget"]["n"]), (3, 2))
        self.assertAlmostEqual(sensitivity["no_fidget"]["mean_score"], 8.5)
        saved = json.loads((self.root / "results" / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(saved["research_team_participants"], 1)
        with (self.root / "processed" / "scores.csv").open(encoding="utf-8", newline="") as handle:
            self.assertEqual(len(list(csv.DictReader(handle))), 6)

    def test_rejects_raw_data_that_breaks_the_design(self):
        cases = {
            "missing columns": lambda: (self.raw / "Alice Example_VideoA_run-a_Assessment.csv").write_text(
                "run_id,taker_name\n", encoding="utf-8"),
            "repeated question": lambda: write_run(self.raw, "run-g", "Gus", "1", 5, "2026-10-22T20:00:00Z",
                                                   question_number="1"),
            "condition mismatch": lambda: write_run(self.raw, "run-g", "Gus", "1", 5, "2026-10-22T20:00:00Z",
                                                    condition="No fidget toy"),
            "unanswered question": lambda: write_run(self.raw, "run-g", "Gus", "1", 5, "2026-10-22T20:00:00Z",
                                                     answer_letter=""),
            "repeat participant": lambda: write_run(self.raw, "run-g", "alice example", "2", 5,
                                                    "2026-10-22T20:00:00Z"),
            "repeat run": lambda: write_run(self.raw, "run-a", "Gus", "2", 5, "2026-10-22T20:00:00Z"),
        }
        for label, corrupt in cases.items():
            with self.subTest(label):
                self.tearDown()
                self.setUp()
                corrupt()
                with self.assertRaises(ValueError):
                    load_runs(self.raw)

    def test_unknown_research_team_run_is_an_error(self):
        with self.assertRaises(ValueError):
            score_runs(load_runs(self.raw), KEY, frozenset({"not-a-run"}))

    def test_research_team_runs_exist_in_collected_data(self):
        run_ids = {run["run_id"] for run in load_runs(ROOT / "data" / "raw")}
        self.assertLessEqual(RESEARCH_TEAM_RUN_IDS, run_ids)


if __name__ == "__main__":
    unittest.main()
