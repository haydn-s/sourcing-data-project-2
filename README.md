# sourcing-data-project-2

Project 2 for Duke University AIPI-510 (Sourcing Data for Analytics), taken in Fall 2026.

## Assessment prototype

The quiz the participant takes after each video. It has a start page for the participant's
name, group and quiz number, one question set per study video, and the questions shown one
at a time with four choices (A–D) each. All question and answer text is intentionally blank
until the quizzes are written. Participants must select an answer before continuing and can
use **Previous** to review and change earlier answers.

### Run locally

Open `index.html` directly in a modern browser. No install, internet connection, or
backend is required. Alternatively, serve the folder:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Then visit <http://localhost:8000>. If Node.js is installed, `npm start` runs the same
server and `npm test` checks the counterbalancing, timing, and CSV export logic (no
dependencies to install).

### One question set per video

Edit `questions.js`. It holds one entry per study video — `A` and `B`, matching the videos
in [`videos/README.md`](videos/README.md) — and each entry has a `title` and its own list
of questions. Each question has a `prompt` and four `answers` in A–D order:

```js
{ id: 1, prompt: "Your question here", answers: ["First choice", "Second choice", "Third choice", "Fourth choice"] },
```

Both videos need the same number of questions, with sequential `id` values starting at 1,
so the two conditions stay comparable. The template ships with 10 blank questions per video
to match the quiz score out of 10 in the study design; add or remove entries in both sets
together and the form picks up the new count. If the two sets get out of step, the form
refuses to start and says what is wrong instead of collecting unusable data.

### Group, video and condition

The start page asks for the participant's group (1–4) and whether this is their first or
second quiz. Those two answers fix the video and condition from the counterbalancing table
in [`videos/README.md`](videos/README.md), so the recorded pair can never contradict the
group assignment:

| Group | First quiz | Second quiz |
| --- | --- | --- |
| 1 | Video A, fidget toy | Video B, no fidget toy |
| 2 | Video A, no fidget toy | Video B, fidget toy |
| 3 | Video B, fidget toy | Video A, no fidget toy |
| 4 | Video B, no fidget toy | Video A, fidget toy |

The assigned video and condition appear on the start page before beginning, in the quiz
header while answering, and in every row of the CSV. After a first quiz, **Start the next
quiz** keeps the participant's name and group and preselects the second quiz.

### Results and timing

Pressing **Begin assessment** starts timing immediately. Pressing **Submit quiz** on the
last question stops timing and automatically downloads
`{TAKER_NAME}_Video{A or B}_Assessment.csv`, so a participant's two quizzes land in separate
files. The completion page also has a button to download the same results again and a button
to start the next quiz. Filename characters that are invalid on common operating systems are
replaced with underscores; the participant's entered name is preserved in the CSV. Repeated
runs use the same requested filename; the browser may append a number or ask before replacing
an existing download.

Each CSV contains one data row per question (10 by default), with these columns:

| Columns | Content |
| --- | --- |
| `run_id`, `taker_name` | Unique identifier for the run and participant name |
| `participant_group`, `quiz_number` | Assigned group 1–4, and whether this was the participant's first or second quiz |
| `video_id`, `video_title` | Which video this quiz covers |
| `condition` | Fidget toy or no fidget toy, from the group assignment |
| `started_at`, `completed_at` | UTC timestamps in ISO 8601 format |
| `total_time_seconds` | Elapsed time from Begin through final submission, repeated on each row |
| `question_number`, `question_text` | Question number and configured text |
| `option_a`, `option_b`, `option_c`, `option_d` | All four configured choices |
| `answer_letter`, `answer_text` | Final selected choice and its configured text |
| `question_time_seconds` | Total time spent on that question, including repeat visits |

Times are recorded to three decimal places using a monotonic browser clock. Timing
continues while the tab is in the background. The per-question durations add up to the
total (apart from rounding to milliseconds). Unanswered choices cannot be submitted.
Blank answer text still produces an A–D selection in the CSV. Formula-like text is
prefixed with an apostrophe so spreadsheets treat it as text.

Results download to the browser's configured download location; there is no server-side
storage or upload. An unfinished run is held in memory and is lost if the page is
refreshed or closed; the browser warns before leaving an active quiz. Completed
CSV downloads are ignored by Git to keep participant data out of the repository.

## Power analysis

The power analysis follows the **one-video, two-independent-group design** in
[PR #7](https://github.com/haydn-s/sourcing-data-project-2/pull/7). Each participant
watches the same video and completes the same 10-question quiz once. With α = 0.05,
80% desired power, and equal group sizes, the independent-samples t-test planning model gives:

| Assumed effect | Completers per group | Total completers | Initial recruits at 10% assumed loss |
| --- | --- | --- | --- |
| d = 0.50: 1-question difference / within-group score SD of 2 | 64 | 128 | 144 total (72 per group) |
| d = 0.80: 1.6-question difference / within-group score SD of 2 | 26 | 52 | 58 total (29 per group) |

The default preserves the selected **one-question** threshold. The 52-total scenario
assumes a larger effect; it has only 42.4% power for a one-question difference when
the within-group score SD is 2. Variability and loss rate are planning assumptions,
not pilot estimates. Recruitment inflation is an expectation, not a guarantee.
The equal-variance planning model approximates power for the planned Welch analysis.

See the [full power analysis and suggested report wording](reports/power-analysis.md)
for hypotheses, calculations, sensitivity tables, design limitations, and references.
The [generated results](results/power/) contain calculated planning values, with no
participant data.

To reproduce with Python 3.12 or newer, run from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/power_analysis.py
.venv/bin/python -m unittest discover -s tests -p 'test_power_analysis.py' -v
```

Use `--help` to see adjustable assumptions. To explore another scenario without replacing
the baseline outputs:

```sh
.venv/bin/python scripts/power_analysis.py --mean-difference 1.6 --participants 52 --output-dir /tmp/fidget-power-large-effect
```

`--participants` is the **total** across both groups, split equally; `--score-sd` is the
common within-group score SD. The former paired-design `--difference-sd` flag is removed.

## To-Do's

Project plan for the fidget toy study ([Idea 2](#idea-2-does-using-a-fidget-toy-help-or-hurt-learning), below).

### By Friday (Oct 16), before class

- [x] **Sabrina:** Pick the video(s) for the study (see [`videos/`](videos/))
- [x] **Sabrina:** Create the recruitment flyer to send to friends
- [ ] **Sabrina:** Create the Google form for participant intake
- [x] **Haydn:** Build the HTML quiz form, leaving the questions blank so we can fill them in once the videos are picked

### GitHub branches and PRs

- [x] **Sabrina:** `flyer` branch, with a PR to add the recruitment flyer to the repo (and document it in the README)
- [ ] **Sabrina:** `videos` branch, with a PR to add the video links and quiz questions to the repo
- [x] **Haydn:** `question-form-template` branch, with [PR #2](https://github.com/haydn-s/sourcing-data-project-2/pull/2) to add the HTML quiz form
- [x] **Haydn:** `html-form-updates` branch, with [PR #4](https://github.com/haydn-s/sourcing-data-project-2/pull/4) to add one question set per video and record each run's group, video and condition
- [ ] Each of us reviews and approves the other's PRs before merging

### Next week (Oct 19–23)

- [x] Run the power analysis to figure out how many participants we need (see [Power analysis](#power-analysis))
- [ ] Send the flyer out to friends throughout the week to recruit participants
- [ ] Decide on the final details of the experiment

### Running the experiment

- [ ] Thursday, Oct 22 and Friday, Oct 23

## Project Ideas Under Consideration

We considered two experiments built around attention and learning measures that are cheap
to collect in person. The selected fidget-toy study now uses two independent groups.

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
- **Dependent variable:** score on a 10-question quiz after a ~4.5-minute video

**How we'll test it**

- Two independent groups: randomly assign each participant to fidget toy or no fidget toy
- Everyone watches *The surprising reasons animals play dead* and takes the same
  10-question quiz once; the updated protocol and questions are supplied by
  [PR #7](https://github.com/haydn-s/sourcing-data-project-2/pull/7)
- Fidget participants hold a squishy while watching; controls have no toy
- Use Group 1 (fidget) or Group 2 (control), first quiz only, in the existing form
- Watch video → take quiz; stop after that quiz (about 10 minutes per participant)

**Statistical test:** Two-sided Welch independent-samples t-test. Power planning uses
an equal-variance independent-samples t-test approximation. Any Mann-Whitney U sensitivity
analysis must state its assumptions and the different hypothesis it addresses.

**Sample size:** For α = 0.05 and 80% power, d = 0.50 requires 64 per group (128 total);
d = 0.80 requires 26 per group (52 total). See [Power analysis](#power-analysis) for
the raw score assumptions, recruitment estimates, and sensitivity at smaller sample sizes.

### Side-by-Side Comparison

| | Idea 1: Exercise & Attention | Idea 2: Fidget Toy & Learning |
| --- | --- | --- |
| Independent variable | Sitting vs. 2 min jumping jacks | No fidget toy vs. fidget toy |
| Dependent variable | Stroop reaction time & accuracy | Quiz score |
| Design | Within-subjects, randomized order | Between-subjects, two randomized groups |
| Session length | Practice + 2 conditions + 5 min rest | 1 video (4.5 min) + 1 quiz |
| Statistical test | Paired t-test / Wilcoxon signed-rank | Welch independent-samples t-test |
| Target sample | ~34 (d = 0.5, α = 0.05, power = 0.80) | 128 total at d = 0.50; 52 total at d = 0.80 (α = 0.05, power ≥ 0.80) |

## Recruitment Flyer

The recruitment flyer is in [`flyer/`](flyer/):

- [`flyer.pdf`](flyer/flyer.pdf) is the printable letter-size version.
- [`flyer.png`](flyer/flyer.png) is the image version for sending to friends by text or social media.
- [`flyer.html`](flyer/flyer.html) and [`qr.svg`](flyer/qr.svg) are the source files. Edit the HTML,
  then re-export the PDF and PNG.

![Recruitment flyer](flyer/flyer.png)

The flyer advertises a 15-minute session on Thursday, Oct 22 (before 6:00 PM) and Friday, Oct 23
(after 11:30 AM), with free candy as a thank-you. Its QR code opens the Google Form where
participants pick their available time slots. We then confirm each person's slot and the room on
campus.

The flyer describes the study only as watching short videos and answering a few questions. It
deliberately doesn't mention or show fidget toys, so participants don't know what is being tested
and their expectations don't skew the results.

## Status

Idea 2 (fidget toy and learning) is the study we are moving forward with. The prospective
power analysis is complete. Participant data collection and outcome analysis have not
started — see the [To-Do's](#to-dos) above for the current plan.
