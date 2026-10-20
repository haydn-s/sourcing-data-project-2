# Power analysis for the fidget toy learning study

The planning target is **36 participants who complete both quizzes**, ideally 9 in each
of the four counterbalancing groups. This gives approximately **83.1% power** to detect
an average difference of **1 correct answer out of 10**, provided the standard deviation
of the within-person score differences is **2 questions**. Initially recruiting **40
participants** allows for 10% unusable or incomplete pairs in expectation; it does not
guarantee 36 complete pairs or equal group sizes.

This is a prospective power analysis. The one-question target is the investigators'
chosen smallest meaningful difference. The variability and loss rate are explicit
planning assumptions, rather than estimates from pilot data or published fidget-toy studies.

## Research question and hypotheses

Does using a fidget toy while watching a short educational video change immediate
recall, measured by a 10-question quiz, compared with watching without a fidget toy?

Each participant watches two different videos and completes both conditions. Define
`D = score with fidget − score without fidget`, measured in correct answers. The primary
hypotheses are `H₀: μD = 0` and `H₁: μD ≠ 0`. A two-sided test is appropriate because the
toy could help or hurt recall. The primary outcome is total quiz score; quiz completion
time and any subgroup comparisons are exploratory and are not covered by this power analysis.

## Planning assumptions

| Input | Value and rationale |
| --- | --- |
| Primary test | Paired t-test on each participant's score difference |
| Significance level | Two-sided α = 0.05, chosen before data collection |
| Desired power | 0.80, a practical planning target for this small course experiment |
| Smallest meaningful mean difference | 1 correct answer out of 10, or 10 percentage points in average accuracy |
| Assumed standard deviation of differences | σD = 2 correct answers, with sensitivity analysis below |
| Standardized paired effect | d_z = \|μD\| / σD = 1 / 2 = 0.50 |
| Allocation | Four counterbalanced sequences, with equal group sizes as the goal |
| Assumed unusable or incomplete fraction | 10%, used only for recruitment planning |

The one-question threshold reflects the practical value of changing performance by one
quiz item on average. It does not assert that the true effect is this large. Choosing a
meaningful effect and examining uncertainty in the planning inputs follows the approach
described by [Lakens (2022)](https://doi.org/10.1525/collabra.33267).

For a paired test, σD is the standard deviation of the **differences**, not the pooled
standard deviation of the two quiz scores. If only marginal score variability and the
within-person correlation are available, then
`σD = sqrt(σF² + σC² − 2ρσFσC)`. For illustration, both condition SDs equal to 2 and a
within-person correlation of 0.50 imply σD = 2. Neither those marginal SDs nor that
correlation has been measured here. No additional correlation input is needed when σD
is specified directly.

## Calculation and sample size

The calculation uses Python and
[`statsmodels.stats.power.TTestPower`](https://www.statsmodels.org/stable/generated/statsmodels.stats.power.TTestPower.solve_power.html),
which supports paired tests with `nobs` equal to the number of participant pairs.
Under independent normally distributed differences, the test statistic under the
alternative has a noncentral t distribution with `df = n − 1` and noncentrality
`λ = d_z × sqrt(n)`. The power calculation includes both rejection tails:

```text
c = t quantile at 1 − α/2, with n − 1 degrees of freedom
Power(n) = P(T < −c) + P(T > c), where T ~ noncentral_t(n − 1, λ)

TTestPower().solve_power(effect_size=0.50, alpha=0.05,
                        power=0.80, alternative="two-sided")
= 33.3671
```

Rounding up gives **34 complete participant pairs**. Power at 33 is 79.5%; at 34 it is
80.8%, confirming that 34 is the smallest integer sample meeting the target. Rounding
again to a multiple of four gives **36 complete pairs**, 9 per sequence, with **83.1%
power**. This is 36 people and 72 quiz administrations. The four sequences do not
represent four independent treatment comparisons, and the 720 individual question
responses are not independent participants.

The initial recruitment target is `ceil(36 / (1 − 0.10)) = 40`. Missing data can leave
fewer than 36 complete pairs or imbalance across sequences, so plan replacement sessions
according to rules set before inspecting scores. Fix the completion target, collection
deadline, and eligibility rules before collecting data. Do not stop or extend recruitment
based on interim p-values. Retain all eligible complete pairs, and report actual group
counts and reasons for exclusions.

## Sensitivity to variability and recruitment

For the same one-question mean difference, greater variability reduces power:

| Assumed SD of paired differences | d_z | Minimum complete pairs | Target rounded to four groups | Power with 36 pairs |
| --- | --- | --- | --- | --- |
| 1.5 questions | 0.667 | 20 | 20 | 97.3% |
| 2.0 questions | 0.500 | 34 | 36 | 83.1% |
| 2.5 questions | 0.400 | 52 | 52 | 64.6% |
| 3.0 questions | 0.333 | 73 | 76 | 49.4% |
| 4.0 questions | 0.250 | 128 | 128 | 30.8% |

Thus, 36 completers meets the planning goal only under sufficiently favorable
variability. A target of **52 completers** accommodates σD = 2.5, while **76 completers**
accommodates σD = 3.0 at the same one-question threshold. The default target uses the
repository's existing d_z = 0.5 scenario; it is not a guarantee of adequate power for
every plausible score distribution.

If recruitment is constrained, the power at d_z = 0.50 is:

| Complete participants | Power |
| --- | --- |
| 16 | 46.5% |
| 20 | 56.5% |
| 24 | 65.0% |
| 28 | 72.3% |
| 32 | 78.2% |
| 36 | 83.1% |

At 36 completers, an effect of d_z ≈ 0.480, or about 0.96 questions when σD = 2, has
80% power. This is a sensitivity threshold, not a guarantee that smaller effects cannot
produce significant results. If fewer participants are available, report the achieved
sample size and the corresponding sensitivity rather than claiming 80% power.

![Power across complete participant counts and assumed paired effects](../results/power/power_curve.png)

## Design considerations and limits

The paired design controls for stable differences in participants' ability. The four
sequences balance video identity and period across the fidget and no-fidget conditions
when group sizes are equal. Balance does not eliminate participant-level variability,
carryover, or differences in how individual participants respond to the two videos.
The current session instructions assign groups in rotation; that is counterbalancing,
but it is not random assignment. Before collection, prefer randomly shuffled blocks
containing each group once and preserve the allocation record.

The noncentral t calculation is exact for independent normal differences. Differences
between bounded integer quiz scores are not exactly normal, so actual power is
approximate. Check the distribution of participant differences, outliers, and floor or
ceiling effects. Pilot the quizzes to make them comparable and avoid near-perfect scores;
estimate SD(D) using both quiz conditions if possible, and revise assumptions before the
main study. A small pilot's variance estimate will itself be uncertain.

For the final analysis, report the paired mean difference with a 95% confidence interval,
the paired t-test p-value, and observed d_z = mean(D) / SD(D). Retain the prespecified
primary test rather than automatically switching tests after a normality test. If a
Wilcoxon signed-rank sensitivity analysis is used, account for ties and zero differences
and state its symmetry assumption; it is not the same test of the population mean.
This calculation does not establish power for Wilcoxon tests, interactions, or subgroup
effects. No post hoc multiple-comparison tests are needed for the single primary contrast.
A nonsignificant result does not establish equivalence or absence of a meaningful effect;
use the confidence interval to describe the remaining uncertainty.

## Reproduction and outputs

From the repository root, with Python 3.12 or newer:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/power_analysis.py
.venv/bin/python -m unittest discover -s tests -p 'test_power_analysis.py' -v
```

The saved outputs under [`results/power/`](../results/power/) contain the numerical
summary, sensitivity tables, and PNG and SVG figures. They contain calculated planning
values and no participant data. For a different assumption, preserve the baseline by
writing to another directory, for example:

```sh
.venv/bin/python scripts/power_analysis.py --difference-sd 2.5 --output-dir /tmp/fidget-power-sd25
```

The baseline was verified with Python 3.12.14, statsmodels 0.15.0, SciPy 1.18.1,
NumPy 2.5.4, and Matplotlib 3.11.2. Tests compare the power values against both tails of
the [SciPy noncentral t distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.nct.html)
and check the integer sample-size boundary.

## Suggested report wording

An a priori power analysis was conducted for a two-sided paired t-test comparing quiz
scores with and without a fidget toy. We defined a one-question difference on a
10-question quiz as the smallest meaningful average effect. Assuming a standard
deviation of 2 questions for the within-person differences gives a standardized paired
effect of d_z = 0.50. With α = 0.05 and desired power of 0.80, a noncentral t calculation
using Python statsmodels required 34 complete participant pairs. We set the planning
target at 36 complete pairs to allow 9 participants in each of four counterbalancing
sequences, yielding approximately 83.1% power under these assumptions. The initial
recruitment target is 40 participants, allowing for 10% incomplete or unusable pairs in
expectation. The difference-score standard deviation and loss rate are planning
assumptions, not pilot estimates; sensitivity analysis requires 52 or 76 complete pairs
if the difference-score standard deviation is 2.5 or 3 questions, respectively.

## References

- Lakens, D. (2022). Sample size justification. *Collabra: Psychology, 8*(1), 33267.
  [https://doi.org/10.1525/collabra.33267](https://doi.org/10.1525/collabra.33267)
- statsmodels developers. *TTestPower.solve_power* documentation.
  [Paired test power calculations](https://www.statsmodels.org/stable/generated/statsmodels.stats.power.TTestPower.solve_power.html)
- SciPy developers. *scipy.stats.nct* documentation.
  [Noncentral t distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.nct.html)
