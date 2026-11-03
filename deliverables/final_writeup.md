# Does a Fidget Toy Help or Hurt Learning? A Two-Group Pilot Experiment

**Authors:** Sabrina Grewal and Haydn Stucker · Duke University, AIPI 510: Sourcing Data for Analytics, Fall 2026

## Abstract

Fidget toys are widely marketed as focus aids, especially for people with ADHD, yet earlier studies found that fidget spinners can increase inattention and reduce memory. We ran an in-person, two-group experiment to test whether holding a squishy toy while watching a short educational video changes how much people remember. Participants were placed in groups by the research team rather than at random. Twelve participants watched the same 4.5-minute TED-Ed video, six holding a squishy and six without one, then completed a 10-question multiple-choice quiz. Mean scores were 7.67 (SD 1.37) with the toy and 7.83 (SD 0.75) without it. A two-sided Welch t-test found no significant difference: the mean difference was −0.17 questions (90% CI −1.36 to 1.02), t(7.78) = −0.26, p = 0.80, Hedges’ g = −0.14. Excluding the two research-team participants gave the same result. Because the study reached 12 of the 102 participants its power analysis called for, it had about 21% power to detect a one-question effect, so the results are inconclusive and are reported as pilot data. The observed score SD of 1.10 suggests a follow-up needs about 16 participants per group at α = 0.10.

## Background & Motivation

Fidget toys such as squishies, spinners and poppers are sold as tools to help people focus, and they are often recommended for people with ADHD. ADHD is common: an estimated 15.5 million U.S. adults (6.0%) had a current ADHD diagnosis in 2023 (Staley et al., 2024). If fidget toys actually pull attention away from learning, that matters for the many students who rely on them.

The evidence so far points the other way from the marketing. In 60 young children with ADHD, fidget spinners increased inattention during class (Graziano et al., 2020). College students who used a fidget spinner during a video lecture remembered less of it than students who did not (Soares & Storm, 2020).

Both studies used spinners, which are visual and make noise. Squishies are quiet and can be used without looking at them, so it is an open question whether they also interfere with learning. Our study tests that question with a short educational video and an immediate recall quiz.

## Null and Alternative Hypotheses

**Research question:** Does using a fidget toy while watching a short educational video change immediate recall, measured by a 10-question quiz, compared with watching without one?

Let μ_F and μ_C be the population mean quiz scores in the fidget-toy and no-toy (control) conditions.

- **H₀:** μ_F − μ_C = 0. Mean quiz scores are the same with and without a fidget toy.
- **H₁:** μ_F − μ_C ≠ 0. Mean quiz scores differ between the two conditions.

The test is two-sided because a fidget toy could plausibly help recall, as its marketing suggests, or hurt it, as earlier spinner studies found.

## Description of Experimental Design

We used a between-subjects design with two groups. Group assignment was not randomized: the research team decided who joined each group. Each participant watched one video and took one quiz, in person, in a single session of about 10 minutes.

| Element | Our study |
| --- | --- |
| Independent variable | Fidget toy condition: a squishy toy held while watching (Group 1) vs. no toy (Group 2) |
| Dependent variable | Number of correct answers on a 10-question multiple-choice quiz (0–10), taken right after the video |
| Control condition | The no-toy group: identical video, quiz app, setting and procedure, without a squishy |
| Group assignment | Participants assigned in pairs, one to each group. The research team chose which member of each pair joined which group, so assignment was not random |
| Stimulus | TED-Ed lesson “The surprising reasons animals play dead” (Tierney Thys, 4:31), chosen as an engaging topic few people already know |
| Outcome measure | 10 four-option questions written from the video, spread across its content, scored against an answer key |

**Procedure.** Every session followed the same steps, run by a member of the research team:

1. The researcher entered the participant’s ID and group in our Streamlit quiz app and confirmed the condition on screen.
2. Fidget group only: the researcher handed over the squishy and told the participant they could squeeze it while watching.
3. The participant watched the full video in the app’s embedded player at a fixed volume.
4. The researcher took the squishy back. The participant pressed Begin assessment, which hid the video and started the quiz timer.
5. The participant answered the 10 questions one at a time and could go back to change answers before submitting.
6. On submission, the app saved the answers and timing as a CSV file.

## Power Analysis

The power analysis called for 51 completers per group (102 total) to detect a one-question difference with 80% power at α = 0.10. It uses an equal-variance independent-samples t-test as the planning model for the planned Welch test.

| Assumption | Value and rationale |
| --- | --- |
| Smallest meaningful difference | 1 correct answer out of 10 (10 percentage points), chosen by the team |
| Assumed within-group score SD | 2 questions (a planning assumption, not a pilot estimate) |
| Standardized effect | Cohen’s d = 1 / 2 = 0.50 |
| Significance level | α = 0.10, two-sided (see below) |
| Desired power | 80% |
| Allocation | Equal group sizes (ratio 1) |
| Assumed loss rate | 10% per group, used only to set recruitment |

We computed sample sizes in Python with statsmodels `TTestIndPower` (script: [`scripts/power_analysis.py`](../scripts/power_analysis.py)):

```python
TTestIndPower().solve_power(effect_size=0.50, alpha=0.10, power=0.80, ratio=1.0, alternative="two-sided")
```

| Assumed effect | Completers per group | Total completers | Recruits at 10% loss |
| --- | --- | --- | --- |
| d = 0.50 (planned) | 51 | 102 | 114 |
| d = 0.80 (large) | 21 | 42 | 48 |

**Why α = 0.10.** Because this is a small exploratory study, we set α = 0.10 and report 90% confidence intervals, which gives more power at the cost of a 10% rather than 5% false-positive risk. Methodological guidance supports looser thresholds for pilot studies, suggesting 85% or 75% confidence intervals instead of 95% (Lee et al., 2014).

## Data Collection & Cleaning Procedures

Twelve participants completed the quiz between October 22 and October 31, 2026: six in the fidget group and six in the control group.

**Recruitment.** We recruited friends and classmates with a flyer offering free candy for a 15-minute session. A QR code on the flyer linked to a Google Form where people chose available time slots. The flyer described the study only as watching short videos and answering questions, so participants would not know the hypothesis.

**Sessions.** Every session was run in person by a member of the research team. Seven quizzes were taken on October 22, two on October 26, one on October 28 and two on October 31. One person assigned to the fidget group did not take the quiz, and a later participant took that place, giving 6 per group. Two participants were members of the research team, one in each group.

**Data capture.** The Streamlit app saved one CSV per quiz to [`data/raw/`](../data/raw/) in the GitHub repository. Each file records the participant ID, group, condition, every answer and the time spent on each question.

**Cleaning.** The script [`scripts/results_analysis.py`](../scripts/results_analysis.py) checks each raw file before scoring:

- exactly one answer for each of the 10 questions
- the recorded group matches the recorded condition
- no person or run appears twice

All 12 files passed, so no quiz was excluded. The script then scores each quiz against [`study/answer_key.csv`](../study/answer_key.csv) and writes [`data/processed/scores.csv`](../data/processed/scores.csv), which uses de-identified IDs P01–P12 in order of quiz start and flags the two research-team participants. Rerunning the script reproduces the outputs byte for byte.

**Sensitive data.** The raw CSV file names and contents include participants’ names. All processed data, results and figures use IDs only.

## Statistical Analysis

A two-sided Welch independent-samples t-test found no significant difference in quiz scores between the fidget and control groups (p = 0.80).

**Test and rationale.** We compared mean quiz scores with Welch’s t-test, specified in the power analysis before data collection. It fits our design (two independent groups, one score per person) and does not assume equal variances, which mattered here because the fidget group’s scores were more spread out.

**Assumptions checked.**

- **Independence:** each person took the quiz once and was in only one group, by design.
- **Equal variances:** not assumed. The group SDs were 1.37 and 0.75, so Welch’s test is the appropriate choice over Student’s t-test.
- **Normality:** with 6 scores per group, a formal normality test has almost no power and was not used. Scores are whole numbers from 6 to 9, so we interpret the p-value cautiously.

**Descriptive statistics.**

| Group | n | Mean | SD | Median | Range |
| --- | --- | --- | --- | --- | --- |
| Fidget toy | 6 | 7.67 | 1.37 | 8 | 6–9 |
| No fidget toy | 6 | 7.83 | 0.75 | 8 | 7–9 |

**Test results (fidget minus no fidget, α = 0.10).**

| Statistic | All participants (6 vs. 6) | Excluding research team (5 vs. 5) |
| --- | --- | --- |
| Mean difference | −0.17 questions | −0.20 questions |
| 90% confidence interval | −1.36 to 1.02 | −1.70 to 1.30 |
| Welch t (df) | −0.26 (7.78) | −0.26 (6.23) |
| p-value | 0.80 | 0.80 |
| Hedges’ g | −0.14 | −0.15 |

The pooled within-group SD was 1.10 questions (90% CI 0.82 to 1.76).

**Sensitivity analysis.** Two participants were members of the research team who knew the hypothesis and helped write the quiz. Excluding them, decided after data collection, gave the same conclusion (right column above).

**Post hoc tests.** None were needed: the study compares only two groups, so there are no pairwise comparisons beyond the main test. Completion time was examined descriptively only (median 119.5 s fidget vs. 145.2 s control) and was not tested.

## Interpretation of Results

We fail to reject H₀: our data show no detectable difference in recall between people who held a squishy and people who did not. This is not evidence that squishies have no effect.

**The confidence interval is wide.** The 90% interval for the difference runs from −1.36 to +1.02 questions. It includes zero, but it also includes our one-question threshold for a meaningful effect in both directions. The data are compatible with a squishy hurting recall by more than a question, helping by about a question, or doing nothing.

**The study had low power.** At 6 per group and α = 0.10, the study had about 21% power to detect the planned effect (d = 0.50) and 36% to detect a large one (d = 0.80), compared with 80% at the 102 participants the power analysis requires. A real effect of the planned size would usually produce a nonsignificant result at this sample size.

**Small-sample estimates are unstable.** With the first nine participants, the difference was −1.00 questions (p = 0.19). Three more quizzes moved it to −0.17. The direction matches earlier spinner studies, but neither estimate is precise enough to rely on.

**Quiz items.** Question 2 was answered correctly by all 12 people, and questions 9 and 10 by 11 of 12, so they did little to separate participants. Question 5 was the hardest: half chose “fight or flight” instead of the correct “resting and digesting,” and every wrong answer was that same option. Easy items narrow the spread of scores, which makes group differences harder to detect.

## Limitations

The main limitation is sample size: 12 completers against the 102 the power analysis requires, which leaves every result underpowered.

- **Sample size and power.** Running every session in person, with a researcher present, kept conditions controlled but limited recruitment to 12 people in about 10 days. Power to detect the planned effect was about 21%.
- **Groups not randomized.** We assigned participants in pairs to keep the groups equal, but the research team chose which member of each pair joined which group rather than using chance. The groups could therefore differ in ways other than the toy, such as prior knowledge or attention (selection bias).
- **No ADHD screening.** ADHD motivated the study, but participants were not screened for it. The results cannot speak to people with ADHD, the group fidget toys are often marketed to.
- **Research-team participants.** Two of the 12 participants knew the hypothesis and helped write the quiz. Excluding them was decided after data collection; both analyses are reported and agree.
- **Convenience sample.** Participants were friends and classmates of the research team, so results may not generalize to other students or ages.
- **Protocol deviations.** One no-show in the fidget group was replaced by a later participant. Five quizzes were taken after the planned October 22–23 sessions, and two on October 26 started 22 seconds apart rather than one at a time.
- **Quiz quality.** One question was at ceiling, two more were nearly so, and one may have been misleading, which limits how well scores separate people.
- **Short-term recall only.** The quiz measured recall immediately after one 4.5-minute video. Effects on longer lectures, delayed recall or other kinds of learning were not tested.

## Conclusion and Recommendations

Holding a squishy while watching a short video made no detectable difference to recall in our pilot (−0.17 questions, p = 0.80), but the study was too small to rule out a meaningful effect in either direction.

**Practical implications.**

- **Students and teachers:** there is no evidence from our study that a squishy improves what people remember from a video. Until stronger evidence exists, fidget toys are better treated as a comfort preference than as a learning tool.
- **People with ADHD:** focus claims made for fidget toys need to be tested with ADHD participants. Combined with the earlier spinner findings, our results do not support assuming these toys help learning.

**Recommendations for a follow-up study.**

- **Recruit enough participants.** Our pooled SD of 1.10 questions implies about 16 per group at α = 0.10 for 80% power to detect a one-question difference. Because that SD estimate is rough, plan for more: an SD of 1.5 would need about 29 per group, and an SD at the upper end of its 90% interval (1.76) about 39.
- Randomize group assignment, for example with a coin flip within each pair, so that any difference between groups other than the toy is due to chance.
- Prespecify the sample size and the stopping rule before collecting data, and exclude research-team members from the start.
- Screen for ADHD so effects can be compared between people with and without it.
- Improve the quiz by replacing the ceiling items (questions 2, 9 and 10) and rewording question 5.
- Allow more participants per day, for example by running several controlled sessions in parallel, while keeping the in-person procedure.

## References

- Graziano, P. A., Garcia, A. M., & Landis, T. D. (2020). To fidget or not to fidget, that is the question: A systematic classroom evaluation of fidget spinners among young children with ADHD. *Journal of Attention Disorders, 24*(1), 163–171. [doi:10.1177/1087054718770009](https://doi.org/10.1177/1087054718770009). Summary: [Learning and the Brain](https://www.learningandthebrain.com/blog/do-fidget-spinners-help-children-with-adhd/)
- Lee, E. C., Whitehead, A. L., Jacques, R. M., & Julious, S. A. (2014). The statistical interpretation of pilot trials: Should significance thresholds be reconsidered? *BMC Medical Research Methodology, 14*, 41. [doi:10.1186/1471-2288-14-41](https://doi.org/10.1186/1471-2288-14-41)
- Soares, J. S., & Storm, B. C. (2020). Putting a negative spin on it: Using a fidget spinner can impair memory for a video lecture. *Applied Cognitive Psychology, 34*(1), 277–284. [doi:10.1002/acp.3610](https://doi.org/10.1002/acp.3610). Summary: [PsyPost](https://www.psypost.org/2019/11/study-finds-using-a-fidget-spinner-can-impair-memory-and-attention-54904)
- Staley, B. S., et al. (2024). Attention-deficit/hyperactivity disorder diagnosis, treatment, and telehealth use in adults — National Center for Health Statistics Rapid Surveys System, United States, October–November 2023. *Morbidity and Mortality Weekly Report, 73*(40), 890–895. [doi:10.15585/mmwr.mm7340a1](https://doi.org/10.15585/mmwr.mm7340a1). Summary: [HealthDay](https://www.healthday.com/healthpro-news/neurology/155-million-adults-had-current-adhd-diagnosis-in-2023)
- Thys, T. (n.d.). *The surprising reasons animals play dead* [Video]. TED-Ed. [ted.com](https://www.ted.com/talks/tierney_thys_the_surprising_reasons_animals_play_dead)

Project repository: [haydn-s/sourcing-data-project-2](https://github.com/haydn-s/sourcing-data-project-2) (code, raw and processed data, power analysis and results). Analysis used Python 3.12, SciPy 1.18 and statsmodels 0.15.
