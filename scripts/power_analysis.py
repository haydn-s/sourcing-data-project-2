#!/usr/bin/env python3
"""Prospective power for two independent fidget-toy groups; no participant data."""

import argparse
import csv
import json
import math
import os
from pathlib import Path
import platform
import tempfile
from importlib.metadata import version

# Keep plotting caches outside the user's home directory and support headless runs.
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "fidget-power-mpl"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.stats.power import TTestIndPower


ROOT = Path(__file__).resolve().parents[1]
GROUPS = 2
QUIZ_QUESTIONS = 10
POWER_MODEL = TTestIndPower()


def independent_power(effect_size, participants_per_group, alpha=0.05):
    """Equal allocation; Cohen's d = |mean(F) - mean(C)| / common score SD.

    This is the equal-variance Student t planning model, not exact Welch power.
    nobs1 counts people in ONE group; the total is twice this number.
    """
    return float(POWER_MODEL.power(
        effect_size=abs(effect_size), nobs1=participants_per_group, alpha=alpha,
        ratio=1.0, alternative="two-sided",
    ))


def required_per_group(effect_size, alpha=0.05, target_power=0.80):
    """Return the continuous solution and minimum integer n >= 2 IN EACH GROUP."""
    if independent_power(effect_size, 2, alpha) >= target_power:
        return 2.0, 2
    solution = float(POWER_MODEL.solve_power(
        effect_size=abs(effect_size), alpha=alpha, power=target_power,
        ratio=1.0, alternative="two-sided",
    ))
    count = max(2, math.ceil(solution))
    # Verify the integer boundary rather than relying solely on solver rounding.
    while independent_power(effect_size, count, alpha) < target_power:
        count += 1
    while count > 2 and independent_power(effect_size, count - 1, alpha) >= target_power:
        count -= 1
    return solution, count


def planning_row(effect_size, args):
    _, required = required_per_group(effect_size, args.alpha, args.power)
    recruits_per_group = math.ceil(required / (1 - args.loss_rate))
    return {
        "effect_size_d": effect_size,
        "minimum_complete_participants_per_group": required,
        "total_complete_participants": GROUPS * required,
        "power_at_required_sample": independent_power(effect_size, required, args.alpha),
        "initial_recruitment_per_group": recruits_per_group,
        "initial_recruitment_total": GROUPS * recruits_per_group,
        "power_at_selected_total": independent_power(effect_size, args.participants // GROUPS, args.alpha),
    }


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot_power(args, target, output_dir):
    max_n = max(200, args.participants + 20, target + 20)
    totals = np.arange(4, max_n + 1, GROUPS)
    baseline_d = args.mean_difference / args.score_sd
    effects = sorted({0.2, 0.3, 0.4, 0.5, 0.8, round(baseline_d, 12)})
    with plt.rc_context({"font.size": 11, "svg.hashsalt": "fidget-power"}):
        fig, ax = plt.subplots(figsize=(9, 5.6), layout="constrained")
        for effect in effects:
            baseline = math.isclose(effect, baseline_d)
            powers = POWER_MODEL.power(effect, totals / GROUPS, alpha=args.alpha,
                                       ratio=1.0, alternative="two-sided")
            ax.plot(totals, powers, label=f"d = {effect:g}" + (" (planning assumption)" if baseline else ""),
                    linewidth=3 if baseline else 1.6)
        ax.axhline(args.power, color="#555555", linestyle="--", linewidth=1)
        ax.axvline(args.participants, color="#777777", linestyle=":", linewidth=1)
        selected_power = independent_power(baseline_d, args.participants // GROUPS, args.alpha)
        ax.scatter([args.participants], [selected_power], color="black", s=32, zorder=5)
        ax.annotate(f"{args.participants} total ({args.participants // GROUPS}/group): {selected_power:.1%} power",
                    xy=(args.participants, selected_power), xytext=(-12, -32), ha="right",
                    textcoords="offset points", fontsize=10,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9})
        ax.set(xlabel="Total participants completing one quiz (half in each group)", ylabel="Power",
               xlim=(4, max_n), ylim=(0, 1.02),
               title=f"Fidget toy study: two independent groups, equal allocation\n"
                     f"alpha = {args.alpha:g}; target power = {args.power:.0%}")
        ax.set_yticks(np.arange(0, 1.01, 0.2), [f"{x:.0%}" for x in np.arange(0, 1.01, 0.2)])
        ax.grid(alpha=0.15)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(loc="lower right", framealpha=0.95, fontsize=9)
        fig.savefig(output_dir / "power_curve.png", dpi=180, metadata={"Software": "power_analysis.py"})
        svg_path = output_dir / "power_curve.svg"
        fig.savefig(svg_path, metadata={"Date": None})
        # Keep generated text portable and avoid whitespace-only Git diff errors.
        svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines())
                            + "\n", encoding="utf-8")
        plt.close(fig)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mean-difference", type=float, default=1.0,
                        help="Smallest meaningful absolute mean difference in correct answers (default: 1).")
    parser.add_argument("--score-sd", type=float, default=2.0,
                        help="Assumed common within-group SD of individual quiz scores (default: 2).")
    parser.add_argument("--participants", type=int, default=128,
                        help="TOTAL complete participants, evenly divided between groups (default: 128).")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--power", type=float, default=0.80)
    parser.add_argument("--loss-rate", type=float, default=0.10,
                        help="Assumed fraction without a usable quiz, applied within each group (default: 0.10).")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "power")
    args = parser.parse_args(argv)
    for field in ("mean_difference", "score_sd", "alpha", "power", "loss_rate"):
        if not math.isfinite(getattr(args, field)):
            parser.error(f"--{field.replace('_', '-')} must be finite")
    if not 0 < args.mean_difference <= QUIZ_QUESTIONS:
        parser.error("--mean-difference must be greater than 0 and at most 10 correct answers")
    if args.score_sd <= 0:
        parser.error("--score-sd must be positive")
    if not 0 < args.alpha < args.power < 1:
        parser.error("require 0 < alpha < power < 1")
    if not 0 <= args.loss_rate < 1:
        parser.error("--loss-rate must be in [0, 1)")
    if args.participants < 4 or args.participants % GROUPS:
        parser.error("--participants must be an even total of at least 4 (at least 2 per group)")
    return args


def run(args):
    effect = args.mean_difference / args.score_sd
    solution, per_group = required_per_group(effect, args.alpha, args.power)
    target = GROUPS * per_group
    recruits_per_group = math.ceil(per_group / (1 - args.loss_rate))
    selected_per_group = args.participants // GROUPS
    detectable_d = float(POWER_MODEL.solve_power(
        effect_size=None, nobs1=selected_per_group, alpha=args.alpha,
        power=args.power, ratio=1.0, alternative="two-sided",
    ))
    summary = {
        "analysis_type": "prospective planning; no observed participant data",
        "design": "one video, one quiz per participant, two independent randomized groups",
        "planning_test": "two-sided independent-samples Student t-test, equal variances",
        "planned_outcome_test": "two-sided Welch independent-samples t-test",
        "power_model_note": "Equal-variance planning benchmark; not exact power for Welch's test.",
        "allocation_ratio_no_fidget_to_fidget": 1.0,
        "difference_definition": "mean quiz score in fidget group minus mean in no-fidget group",
        "quiz_questions": QUIZ_QUESTIONS,
        "mean_difference_questions": args.mean_difference,
        "assumed_common_within_group_score_sd": args.score_sd,
        "effect_size_d": effect,
        "alpha": args.alpha,
        "target_power": args.power,
        "continuous_sample_size_solution_per_group": solution,
        "minimum_complete_participants_per_group": per_group,
        "total_complete_participants": target,
        "quiz_administrations_at_target": target,
        "power_at_target": independent_power(effect, per_group, args.alpha),
        "power_one_fewer_per_group": independent_power(effect, per_group - 1, args.alpha) if per_group > 2 else None,
        "assumed_loss_rate": args.loss_rate,
        "initial_recruitment_per_group": recruits_per_group,
        "initial_recruitment_total": GROUPS * recruits_per_group,
        "expected_complete_participants_at_initial_recruitment": GROUPS * recruits_per_group * (1 - args.loss_rate),
        "probability_of_reaching_target_note": "Recruitment inflation is an expectation, not a guarantee.",
        "selected_total_complete_participants": args.participants,
        "selected_complete_participants_per_group": selected_per_group,
        "power_at_selected_total": independent_power(effect, selected_per_group, args.alpha),
        "detectable_d_at_selected_total": detectable_d,
        "detectable_mean_difference_at_selected_total": detectable_d * args.score_sd,
        "large_effect_scenario": {
            "mean_difference_questions_at_assumed_score_sd": 0.8 * args.score_sd,
            **planning_row(0.8, args),
        },
        "software": {"python": platform.python_version(), **{
            name: version(name) for name in ("numpy", "scipy", "statsmodels", "matplotlib")
        }},
    }
    effect_rows = [planning_row(dz, args) for dz in (0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.8)]
    sd_rows = [{"mean_difference_questions": args.mean_difference,
                "assumed_common_within_group_score_sd": sd,
                **planning_row(args.mean_difference / sd, args)}
               for sd in sorted({1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, args.score_sd})]
    capacity_rows = [{"total_complete_participants": n,
                      "complete_participants_per_group": n // GROUPS,
                      "power_at_planning_effect": independent_power(effect, n // GROUPS, args.alpha),
                      "power_at_d_0_8": independent_power(0.8, n // GROUPS, args.alpha),
                      "detectable_d": float(POWER_MODEL.solve_power(
                          effect_size=None, nobs1=n // GROUPS, alpha=args.alpha, power=args.power,
                          ratio=1.0, alternative="two-sided")),
                      } for n in sorted({16, 20, 24, 28, 32, 36, 40, 48, 52, 60, 80, 100, 128, args.participants})]
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_csv(output_dir / "effect_size_sensitivity.csv", effect_rows)
    write_csv(output_dir / "score_sd_sensitivity.csv", sd_rows)
    write_csv(output_dir / "sample_size_sensitivity.csv", capacity_rows)
    plot_power(args, target, output_dir)
    print(f"Planning effect: {args.mean_difference:g} question(s) / score SD {args.score_sd:g} = d {effect:g}")
    print(f"Minimum: {per_group} per independent group, {target} TOTAL complete participants")
    print(f"Power at target: {summary['power_at_target']:.2%} (equal-variance planning model)")
    print(f"Initial recruitment at {args.loss_rate:.0%} loss: {recruits_per_group} per group, "
          f"{GROUPS * recruits_per_group} total (not a guarantee)")
    print(f"Power at selected TOTAL n={args.participants}: {summary['power_at_selected_total']:.2%}")
    print(f"Outputs: {output_dir}")
    return summary


if __name__ == "__main__":
    run(parse_args())
