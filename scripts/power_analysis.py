#!/usr/bin/env python3
"""Prospective power for the paired fidget-toy quiz study; no participant data."""

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
from statsmodels.stats.power import TTestPower


ROOT = Path(__file__).resolve().parents[1]
GROUPS = 4
QUIZ_QUESTIONS = 10
POWER_MODEL = TTestPower()


def paired_power(effect_size, participants, alpha=0.05):
    """nobs counts complete participant pairs, with effect size |mean(D)| / SD(D)."""
    return float(POWER_MODEL.power(
        effect_size=abs(effect_size), nobs=participants, alpha=alpha,
        alternative="two-sided",
    ))


def required_pairs(effect_size, alpha=0.05, target_power=0.80):
    """Return the continuous solution and the smallest qualifying integer n >= 2."""
    if paired_power(effect_size, 2, alpha) >= target_power:
        return 2.0, 2
    solution = float(POWER_MODEL.solve_power(
        effect_size=abs(effect_size), alpha=alpha, power=target_power,
        alternative="two-sided",
    ))
    count = max(2, math.ceil(solution))
    # Verify the integer boundary rather than relying solely on solver rounding.
    while paired_power(effect_size, count, alpha) < target_power:
        count += 1
    while count > 2 and paired_power(effect_size, count - 1, alpha) >= target_power:
        count -= 1
    return solution, count


def balanced_count(participants):
    return GROUPS * math.ceil(participants / GROUPS)


def planning_row(effect_size, args):
    _, required = required_pairs(effect_size, args.alpha, args.power)
    balanced = balanced_count(required)
    return {
        "effect_size_dz": effect_size,
        "minimum_complete_pairs": required,
        "balanced_complete_pairs": balanced,
        "complete_pairs_per_group": balanced // GROUPS,
        "initial_recruitment_target": balanced_count(math.ceil(balanced / (1 - args.loss_rate))),
        "power_at_selected_n": paired_power(effect_size, args.participants, args.alpha),
    }


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_power(args, target, output_dir):
    max_n = max(160, args.participants + 20, target + 20)
    counts = np.arange(4, max_n + 1)
    baseline_dz = args.mean_difference / args.difference_sd
    effects = sorted({0.2, 0.3, 0.4, 0.5, 0.8, round(baseline_dz, 12)})
    with plt.rc_context({"font.size": 11, "svg.hashsalt": "fidget-power"}):
        fig, ax = plt.subplots(figsize=(9, 5.6), layout="constrained")
        for dz in effects:
            baseline = math.isclose(dz, baseline_dz)
            powers = POWER_MODEL.power(dz, counts, alpha=args.alpha, alternative="two-sided")
            ax.plot(counts, powers, label=f"d_z = {dz:g}" + (" (planning assumption)" if baseline else ""),
                    linewidth=3 if baseline else 1.6)
        ax.axhline(args.power, color="#555555", linestyle="--", linewidth=1)
        ax.axvline(args.participants, color="#777777", linestyle=":", linewidth=1)
        selected_power = paired_power(baseline_dz, args.participants, args.alpha)
        ax.scatter([args.participants], [selected_power], color="black", s=32, zorder=5)
        ax.annotate(f"{args.participants} participants: {selected_power:.1%} power",
                    xy=(args.participants, selected_power), xytext=(12, -32),
                    textcoords="offset points", fontsize=10,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.9})
        ax.set(xlabel="Participants who complete both quizzes", ylabel="Power",
               xlim=(4, max_n), ylim=(0, 1.02),
               title=f"Fidget toy study: two-sided paired t-test\n"
                     f"alpha = {args.alpha:g}; target power = {args.power:.0%}")
        ax.set_yticks(np.arange(0, 1.01, 0.2), [f"{x:.0%}" for x in np.arange(0, 1.01, 0.2)])
        ax.grid(alpha=0.15)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(loc="lower right", framealpha=0.95, fontsize=9)
        fig.savefig(output_dir / "power_curve.png", dpi=180, metadata={"Software": "power_analysis.py"})
        fig.savefig(output_dir / "power_curve.svg", metadata={"Date": None})
        plt.close(fig)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mean-difference", type=float, default=1.0,
                        help="Smallest meaningful absolute mean difference in correct answers (default: 1).")
    parser.add_argument("--difference-sd", type=float, default=2.0,
                        help="Assumed SD of within-person differences, NOT either quiz's SD (default: 2).")
    parser.add_argument("--participants", type=int, default=36,
                        help="Complete participant pairs for sensitivity analysis (default: 36).")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--power", type=float, default=0.80)
    parser.add_argument("--loss-rate", type=float, default=0.10,
                        help="Assumed fraction without a usable pair (default: 0.10).")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "power")
    args = parser.parse_args(argv)
    for field in ("mean_difference", "difference_sd", "alpha", "power", "loss_rate"):
        if not math.isfinite(getattr(args, field)):
            parser.error(f"--{field.replace('_', '-')} must be finite")
    if not 0 < args.mean_difference <= QUIZ_QUESTIONS:
        parser.error("--mean-difference must be greater than 0 and at most 10 correct answers")
    if args.difference_sd <= 0:
        parser.error("--difference-sd must be positive")
    if not 0 < args.alpha < args.power < 1:
        parser.error("require 0 < alpha < power < 1")
    if not 0 <= args.loss_rate < 1:
        parser.error("--loss-rate must be in [0, 1)")
    if args.participants < 2:
        parser.error("--participants must be at least 2")
    return args


def run(args):
    effect = args.mean_difference / args.difference_sd
    solution, minimum = required_pairs(effect, args.alpha, args.power)
    target = balanced_count(minimum)
    initial_recruitment = balanced_count(math.ceil(target / (1 - args.loss_rate)))
    detectable_dz = float(POWER_MODEL.solve_power(
        effect_size=None, nobs=args.participants, alpha=args.alpha,
        power=args.power, alternative="two-sided",
    ))
    summary = {
        "analysis_type": "prospective planning; no observed participant data",
        "test": "two-sided paired t-test",
        "difference_definition": "quiz score with fidget minus quiz score without fidget",
        "quiz_questions": QUIZ_QUESTIONS,
        "mean_difference_questions": args.mean_difference,
        "assumed_sd_of_paired_differences": args.difference_sd,
        "effect_size_dz": effect,
        "alpha": args.alpha,
        "target_power": args.power,
        "continuous_sample_size_solution": solution,
        "minimum_complete_pairs": minimum,
        "power_at_minimum": paired_power(effect, minimum, args.alpha),
        "power_one_fewer_than_minimum": paired_power(effect, minimum - 1, args.alpha) if minimum > 2 else None,
        "balanced_complete_pairs": target,
        "complete_pairs_per_group": target // GROUPS,
        "power_at_balanced_target": paired_power(effect, target, args.alpha),
        "assumed_loss_rate": args.loss_rate,
        "initial_recruitment_target": initial_recruitment,
        "expected_complete_pairs_at_initial_recruitment": initial_recruitment * (1 - args.loss_rate),
        "probability_of_reaching_target_note": "Recruitment inflation is an expectation, not a guarantee.",
        "selected_complete_pairs": args.participants,
        "power_at_selected_n": paired_power(effect, args.participants, args.alpha),
        "detectable_dz_at_selected_n": detectable_dz,
        "detectable_mean_difference_at_selected_n": detectable_dz * args.difference_sd,
        "software": {"python": platform.python_version(), **{
            name: version(name) for name in ("numpy", "scipy", "statsmodels", "matplotlib")
        }},
    }
    effect_rows = [planning_row(dz, args) for dz in (0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.8)]
    sd_rows = [{"mean_difference_questions": args.mean_difference,
                "assumed_sd_of_paired_differences": sd,
                **planning_row(args.mean_difference / sd, args)}
               for sd in sorted({1.0, 1.5, 2.0, 2.5, 3.0, 4.0, args.difference_sd})]
    capacity_rows = [{"complete_pairs": n,
                      "power_at_planning_effect": paired_power(effect, n, args.alpha),
                      "detectable_dz": float(POWER_MODEL.solve_power(
                          effect_size=None, nobs=n, alpha=args.alpha, power=args.power,
                          alternative="two-sided")),
                      } for n in sorted({12, 16, 20, 24, 28, 32, 34, 36, 40, 48, 60, args.participants})]
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_csv(output_dir / "effect_size_sensitivity.csv", effect_rows)
    write_csv(output_dir / "difference_sd_sensitivity.csv", sd_rows)
    write_csv(output_dir / "sample_size_sensitivity.csv", capacity_rows)
    plot_power(args, target, output_dir)
    print(f"Planning effect: {args.mean_difference:g} question(s) / SD(D) {args.difference_sd:g} = d_z {effect:g}")
    print(f"Minimum: {minimum} complete pairs; four-group target: {target} ({target // GROUPS} per group)")
    print(f"Power at target: {summary['power_at_balanced_target']:.2%}")
    print(f"Initial recruitment target at {args.loss_rate:.0%} loss: {initial_recruitment} (not a guarantee)")
    print(f"Power at selected n={args.participants}: {summary['power_at_selected_n']:.2%}")
    print(f"Outputs: {output_dir}")
    return summary


if __name__ == "__main__":
    run(parse_args())
