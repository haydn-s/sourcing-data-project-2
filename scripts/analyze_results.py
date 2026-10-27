#!/usr/bin/env python3
"""Score the fidget-toy quiz responses and run the planned Welch comparison."""

import argparse
import csv
import json
import math
import os
from pathlib import Path
import platform
import statistics
import tempfile
from importlib.metadata import version

# Keep plotting caches outside the user's home directory and support headless runs.
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "fidget-results-mpl"))
import matplotlib

matplotlib.use("Agg")
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.power import TTestIndPower


ROOT = Path(__file__).resolve().parents[1]
QUIZ_QUESTIONS = 10
VIDEO_ID = "A"
ALPHA = 0.05
PLANNING_EFFECTS = (0.5, 0.8)
GROUPS = {"1": "Fidget toy", "2": "No fidget toy"}
GROUP_COLORS = {"1": "#2a78d6", "2": "#eb6834"}
# Runs completed by members of the research team, who knew the hypothesis and the quiz.
# They are identified by run_id so that no names appear here or in any output.
RESEARCH_TEAM_RUN_IDS = frozenset({
    "31fed147-3a59-4df6-ab8f-97b9a55ae7a8",
    "aa7ac8d9-d8a9-4f21-b6f9-171ea6be7dc6",
})
RUN_COLUMNS = ("run_id", "taker_name", "participant_group", "video_id", "condition",
               "started_at", "total_time_seconds")
QUESTION_COLUMNS = ("question_number", "answer_letter", "question_time_seconds")


def load_answer_key(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        key = {int(row["question_number"]): row["correct_letter"]
               for row in csv.DictReader(handle) if row["video_id"] == VIDEO_ID}
    if sorted(key) != list(range(1, QUIZ_QUESTIONS + 1)):
        raise ValueError(f"{path}: expected answers for questions 1-{QUIZ_QUESTIONS} of video {VIDEO_ID}")
    return key


def load_runs(raw_dir):
    """Read and validate one completed quiz per *_Assessment.csv file."""
    runs = []
    for path in sorted(Path(raw_dir).glob("*_Assessment.csv")):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = [column for column in RUN_COLUMNS + QUESTION_COLUMNS if column not in (reader.fieldnames or ())]
            if missing:
                raise ValueError(f"{path.name}: missing columns {missing}")
            rows = list(reader)
        run = {}
        for column in RUN_COLUMNS:
            values = {row[column] for row in rows}
            if len(values) != 1:
                raise ValueError(f"{path.name}: {column} is missing or differs between rows")
            run[column] = values.pop()
        questions = sorted(int(row["question_number"]) for row in rows)
        if questions != list(range(1, QUIZ_QUESTIONS + 1)):
            raise ValueError(f"{path.name}: expected one row for each of questions 1-{QUIZ_QUESTIONS}")
        if run["video_id"] != VIDEO_ID:
            raise ValueError(f"{path.name}: expected video {VIDEO_ID}, found {run['video_id']!r}")
        if GROUPS.get(run["participant_group"]) != run["condition"]:
            raise ValueError(f"{path.name}: group {run['participant_group']!r} does not match "
                             f"condition {run['condition']!r}")
        run["answers"] = {int(row["question_number"]): row["answer_letter"] for row in rows}
        if not set(run["answers"].values()) <= set("ABCD"):
            raise ValueError(f"{path.name}: every question needs an answer from A to D")
        run["question_times"] = {int(row["question_number"]): float(row["question_time_seconds"]) for row in rows}
        run["total_time_seconds"] = float(run["total_time_seconds"])
        run["source"] = path.name
        runs.append(run)
    if not runs:
        raise ValueError(f"No *_Assessment.csv files found in {raw_dir}")
    # Each person contributes one independent score; repeats must be resolved before analysis.
    for field, label in (("run_id", "run"), ("taker_name", "participant")):
        seen = {}
        for run in runs:
            value = run[field].strip().casefold()
            if value in seen:
                raise ValueError(f"Repeated {label} in {seen[value]} and {run['source']}")
            seen[value] = run["source"]
    return runs


def score_runs(runs, key, research_team_run_ids=RESEARCH_TEAM_RUN_IDS):
    """Score each run and replace names with IDs (P01, P02, ...) in order of quiz start."""
    unknown = set(research_team_run_ids) - {run["run_id"] for run in runs}
    if unknown:
        raise ValueError(f"Research-team run IDs not found in the raw data: {sorted(unknown)}")
    participants = []
    ordered = sorted(runs, key=lambda run: (run["started_at"], run["run_id"]))
    for number, run in enumerate(ordered, start=1):
        correct = {q: int(run["answers"][q] == key[q]) for q in range(1, QUIZ_QUESTIONS + 1)}
        participants.append({
            "participant_id": f"P{number:02d}",
            "session_date_utc": run["started_at"][:10],
            "participant_group": run["participant_group"],
            "condition": run["condition"],
            "research_team": int(run["run_id"] in research_team_run_ids),
            "score": sum(correct.values()),
            "total_time_seconds": run["total_time_seconds"],
            "answers": run["answers"],
            "question_times": run["question_times"],
            "correct": correct,
        })
    return participants


def describe_group(members):
    scores = [p["score"] for p in members]
    times = [p["total_time_seconds"] for p in members]
    return {
        "n": len(members),
        "mean_score": statistics.fmean(scores),
        "sd_score": statistics.stdev(scores),
        "median_score": float(statistics.median(scores)),
        "min_score": min(scores),
        "max_score": max(scores),
        "mean_total_time_seconds": statistics.fmean(times),
        "median_total_time_seconds": statistics.median(times),
    }


def compare_groups(participants):
    """Two-sided Welch test of fidget minus no-fidget mean score, with effect sizes."""
    fidget = [p for p in participants if p["participant_group"] == "1"]
    control = [p for p in participants if p["participant_group"] == "2"]
    if len(fidget) < 2 or len(control) < 2:
        raise ValueError("Each group needs at least two participants for the Welch test")
    fidget_scores = [p["score"] for p in fidget]
    control_scores = [p["score"] for p in control]
    n1, n2 = len(fidget_scores), len(control_scores)
    pooled_df = n1 + n2 - 2
    welch = stats.ttest_ind(fidget_scores, control_scores, equal_var=False)
    interval = welch.confidence_interval(1 - ALPHA)
    difference = statistics.fmean(fidget_scores) - statistics.fmean(control_scores)
    pooled_sd = math.sqrt(((n1 - 1) * statistics.variance(fidget_scores)
                           + (n2 - 1) * statistics.variance(control_scores)) / pooled_df)
    cohens_d = difference / pooled_sd if pooled_sd else None
    # Hedges' small-sample correction J = 1 - 3 / (4 df - 1), df = n1 + n2 - 2.
    hedges_g = cohens_d * (1 - 3 / (4 * pooled_df - 1)) if cohens_d is not None else None
    return {
        "participants": n1 + n2,
        "fidget": describe_group(fidget),
        "no_fidget": describe_group(control),
        "mean_difference_fidget_minus_no_fidget": difference,
        "welch_t": float(welch.statistic),
        "welch_df": float(welch.df),
        "p_value": float(welch.pvalue),
        "ci_95_low": float(interval.low),
        "ci_95_high": float(interval.high),
        "pooled_within_group_score_sd": pooled_sd,
        # Chi-square interval for the common SD, assuming normal scores within each group.
        "pooled_sd_ci_95_low": pooled_sd * math.sqrt(pooled_df / stats.chi2.ppf(1 - ALPHA / 2, pooled_df)),
        "pooled_sd_ci_95_high": pooled_sd * math.sqrt(pooled_df / stats.chi2.ppf(ALPHA / 2, pooled_df)),
        "cohens_d": cohens_d,
        "hedges_g": hedges_g,
        # Power for the prespecified planning effects at the achieved group sizes, not observed power.
        **{f"power_at_planning_d_{str(effect).replace('.', '_')}": float(TTestIndPower().power(
            effect_size=effect, nobs1=n1, ratio=n2 / n1, alpha=ALPHA, alternative="two-sided"))
           for effect in PLANNING_EFFECTS},
    }


def item_rows(participants, key):
    rows = []
    for q in range(1, QUIZ_QUESTIONS + 1):
        row = {"question_number": q, "correct_letter": key[q],
               "proportion_correct": statistics.fmean(p["correct"][q] for p in participants)}
        for group, name in (("1", "fidget"), ("2", "no_fidget")):
            members = [p for p in participants if p["participant_group"] == group]
            row[f"proportion_correct_{name}"] = statistics.fmean(p["correct"][q] for p in members)
        for letter in "ABCD":
            row[f"answers_{letter.lower()}"] = sum(p["answers"][q] == letter for p in participants)
        row["median_question_time_seconds"] = statistics.median(p["question_times"][q] for p in participants)
        rows.append(row)
    return rows


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_scores(participants, primary, output_dir):
    with plt.rc_context({"font.size": 11, "svg.hashsalt": "fidget-results"}):
        fig, ax = plt.subplots(figsize=(7.5, 5.6), layout="constrained")
        labels = []
        for x, (group, condition) in enumerate(GROUPS.items()):
            members = [p for p in participants if p["participant_group"] == group]
            color = GROUP_COLORS[group]
            tied = {}
            for p in members:
                tied.setdefault(p["score"], []).append(p)
            # Integer scores tie often; spread tied points sideways so each person stays visible.
            for score, people in tied.items():
                for i, p in enumerate(people):
                    offset = (i - (len(people) - 1) / 2) * 0.09
                    ax.scatter(x - 0.12 + offset, score, s=90, linewidths=2, zorder=3, edgecolors=color,
                               facecolors="white" if p["research_team"] else color)
            scores = [p["score"] for p in members]
            mean = statistics.fmean(scores)
            half_width = stats.t.ppf(1 - ALPHA / 2, len(scores) - 1) * statistics.stdev(scores) / math.sqrt(len(scores))
            ax.errorbar(x + 0.22, mean, yerr=half_width, fmt="D", color="#0b0b0b", markersize=8,
                        capsize=6, linewidth=2, zorder=4)
            ax.annotate(f"{mean:.2f}", xy=(x + 0.22, mean), xytext=(10, 0), textcoords="offset points",
                        va="center", color="#52514e", fontsize=10)
            labels.append(f"{condition}\n(n = {len(members)})")
        ax.set_xticks(range(len(GROUPS)), labels)
        ax.set(xlim=(-0.6, len(GROUPS) - 0.4), ylim=(0, QUIZ_QUESTIONS + 0.4),
               ylabel=f"Correct answers (out of {QUIZ_QUESTIONS})")
        ax.set_yticks(range(0, QUIZ_QUESTIONS + 1, 2))
        ax.set_title("Quiz scores by condition\n"
                     f"Fidget − no fidget: {primary['mean_difference_fidget_minus_no_fidget']:+.2f} questions "
                     f"(95% CI {primary['ci_95_low']:.2f} to {primary['ci_95_high']:.2f}; "
                     f"Welch p = {primary['p_value']:.2f})", fontsize=11)
        ax.grid(axis="y", alpha=0.15)
        ax.spines[["top", "right"]].set_visible(False)
        handles = [
            Line2D([], [], marker="o", linestyle="", markersize=9, color="#52514e", label="Participant"),
            Line2D([], [], marker="o", linestyle="", markersize=9, markerfacecolor="white",
                   markeredgecolor="#52514e", markeredgewidth=2, label="Research team member"),
            Line2D([], [], marker="D", color="#0b0b0b", markersize=7, linewidth=2, label="Group mean, 95% CI"),
        ]
        ax.legend(handles=handles, loc="lower right", framealpha=0.95, fontsize=9)
        fig.savefig(output_dir / "score_plot.png", dpi=180, metadata={"Software": "analyze_results.py"})
        svg_path = output_dir / "score_plot.svg"
        fig.savefig(svg_path, metadata={"Date": None})
        # Keep generated text portable and avoid whitespace-only Git diff errors.
        svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines())
                            + "\n", encoding="utf-8")
        plt.close(fig)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--answer-key", type=Path, default=ROOT / "videos" / "answer_key.csv")
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed",
                        help="Where to write the de-identified participant scores.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "analysis")
    return parser.parse_args(argv)


def run(args, research_team_run_ids=RESEARCH_TEAM_RUN_IDS):
    key = load_answer_key(args.answer_key)
    participants = score_runs(load_runs(args.raw_dir), key, research_team_run_ids)
    analyses = {
        "primary_all_participants": compare_groups(participants),
        "sensitivity_excluding_research_team": compare_groups(
            [p for p in participants if not p["research_team"]]),
    }
    summary = {
        "analysis_type": "confirmatory outcome analysis prespecified in reports/power-analysis.md",
        "design": "one video, one quiz per participant, two independent groups",
        "outcome": f"number of correct answers out of {QUIZ_QUESTIONS}",
        "test": "two-sided Welch independent-samples t-test",
        "alpha": ALPHA,
        "difference_definition": "mean quiz score in fidget group minus mean in no-fidget group",
        "effect_size_note": "Cohen's d and Hedges' g use the pooled within-group SD.",
        "power_note": "Power is for the prespecified planning effects at the achieved group sizes; "
                      "it is not post hoc power at the observed effect.",
        "completed_quizzes": len(participants),
        "research_team_participants": sum(p["research_team"] for p in participants),
        "session_dates_utc": sorted({p["session_date_utc"] for p in participants}),
        **analyses,
        "software": {"python": platform.python_version(), **{
            name: version(name) for name in ("numpy", "scipy", "statsmodels", "matplotlib")
        }},
    }
    score_rows = [{
        **{field: p[field] for field in ("participant_id", "session_date_utc", "participant_group",
                                         "condition", "research_team", "score", "total_time_seconds")},
        **{f"q{q:02d}_correct": p["correct"][q] for q in range(1, QUIZ_QUESTIONS + 1)},
    } for p in participants]
    group_rows = [{"analysis": name, "participant_group": group, "condition": GROUPS[group],
                   **result["fidget" if group == "1" else "no_fidget"]}
                  for name, result in analyses.items() for group in GROUPS]
    processed_dir = args.processed_dir.resolve()
    output_dir = args.output_dir.resolve()
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(processed_dir / "scores.csv", score_rows)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_csv(output_dir / "group_summary.csv", group_rows)
    write_csv(output_dir / "item_summary.csv", item_rows(participants, key))
    plot_scores(participants, analyses["primary_all_participants"], output_dir)
    for name, result in analyses.items():
        print(f"{name}: fidget {result['fidget']['mean_score']:.2f} (n={result['fidget']['n']}) vs "
              f"no fidget {result['no_fidget']['mean_score']:.2f} (n={result['no_fidget']['n']}); "
              f"difference {result['mean_difference_fidget_minus_no_fidget']:+.2f} "
              f"[{result['ci_95_low']:.2f}, {result['ci_95_high']:.2f}], "
              f"Welch t({result['welch_df']:.2f}) = {result['welch_t']:.3f}, p = {result['p_value']:.3f}, "
              f"g = {result['hedges_g']:.2f}")
    print(f"Scores: {processed_dir / 'scores.csv'}")
    print(f"Outputs: {output_dir}")
    return summary


if __name__ == "__main__":
    run(parse_args())
