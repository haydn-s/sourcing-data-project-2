# sourcing-data-project-2

Project 2 for Duke University AIPI-510 (Sourcing Data for Analytics), taken in Fall 2026.

## To-Do's

Project plan for the fidget toy study ([Idea 2](#idea-2-does-using-a-fidget-toy-help-or-hurt-learning), below).

### By Friday (Oct 16), before class

- [ ] **Sabrina:** Pick the video(s) for the study
- [ ] **Sabrina:** Create the recruitment flyer to send to friends
- [ ] **Haydn:** Build the HTML quiz form, leaving the questions blank so we can fill them in once the videos are picked

### GitHub branches and PRs

- [ ] **Sabrina:** `flyer` branch, with a PR to add the recruitment flyer to the repo (and document it in the README)
- [ ] **Sabrina:** `videos` branch, with a PR to add the video links and quiz questions to the repo
- [ ] **Haydn:** `quiz-form` branch, with a PR to add the HTML quiz form
- [ ] Each of us reviews and approves the other's PRs before merging

### Next week (Oct 19–23)

- [ ] Run the power analysis to figure out how many participants we need
- [ ] Send the flyer out to friends throughout the week to recruit participants
- [ ] Decide on the final details of the experiment

### Running the experiment

- [ ] Thursday, Oct 22 and Friday, Oct 23

## Project Ideas Under Consideration

We are weighing two candidate experiments. Both are within-subjects designs built around
attention/learning measures that are cheap to collect in person.

### Idea 1: Does a Short Burst of Exercise Improve Attention?

**Research question:** Does doing 2 minutes of jumping jacks before an attention task change
performance compared to sitting for 2 minutes?

**Why it's interesting:** Exercise is widely studied as a way to improve attention, especially in
ADHD research. We want to know if even a tiny 2-minute burst makes a difference.

**Hypotheses**

- **H₀:** There is no difference in attention task performance after exercise vs. after sitting.
- **H₁:** There is a difference in attention task performance after exercise vs. after sitting.

**Variables**

- **Independent variable:** sitting vs. jumping jacks (2 minutes)
- **Dependent variable:** Stroop test reaction time and accuracy

**How we'll test it**

- One control group
- Order is randomized (half sit first, half exercise first)
- Practice round first, then condition → Stroop test → 5-minute rest → other condition → Stroop test

**Statistical test:** Paired t-test (Wilcoxon signed-rank if data isn't normal)

**Sample size:** About 34 participants (d = 0.5, α = 0.05, power = 0.80)

### Idea 2: Does Using a Fidget Toy Help or Hurt Learning?

**Research question:** Does using a fidget toy while watching a short video change how much a
person remembers?

**Why it's interesting:** Fidget toys are marketed as focus tools for ADHD, but research is mixed,
and some studies suggest they may actually hurt learning.

**Hypotheses**

- **H₀:** There is no difference in quiz scores with vs. without a fidget toy.
- **H₁:** There is a difference in quiz scores with vs. without a fidget toy.

**Variables**

- **Independent variable:** fidget toy vs. no fidget toy
- **Dependent variable:** quiz score out of 10 after a 5-minute video

**How we'll test it**

- Every participant does both conditions (within-subjects)
- Two different videos with matching quizzes of similar difficulty
- Order of conditions and videos is randomized
- Watch video → take quiz → short break → watch second video in other condition → take quiz

**Statistical test:** Paired t-test (Wilcoxon signed-rank if data isn't normal)

**Sample size:** About 34 participants (d = 0.5, α = 0.05, power = 0.80)

### Side-by-Side Comparison

| | Idea 1: Exercise & Attention | Idea 2: Fidget Toy & Learning |
| --- | --- | --- |
| Independent variable | Sitting vs. 2 min jumping jacks | No fidget toy vs. fidget toy |
| Dependent variable | Stroop reaction time & accuracy | Quiz score (out of 10) |
| Design | Within-subjects, randomized order | Within-subjects, randomized order |
| Session length | Practice + 2 conditions + 5 min rest | 2 videos (5 min each) + 2 quizzes |
| Statistical test | Paired t-test / Wilcoxon signed-rank | Paired t-test / Wilcoxon signed-rank |
| Target sample | ~34 (d = 0.5, α = 0.05, power = 0.80) | ~34 (d = 0.5, α = 0.05, power = 0.80) |

## Status

Idea 2 (fidget toy and learning) is the study we are moving forward with. No data collection or
analysis has started yet — see the [To-Do's](#to-dos) above for the current plan.
