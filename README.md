# sourcing-data-project-2

Project 2 for Duke University AIPI-510 (Sourcing Data for Analytics), taken in Fall 2026.

## Assessment prototype

A shared assessment template for either project idea. It has a name-entry start page,
25 questions shown one at a time, and four choices (A–D) per question. All question
and answer text is intentionally blank. Participants must select an answer before
continuing and can use **Previous** to review and change earlier answers.

### Run locally

Open `index.html` directly in a modern browser. No install, internet connection, or
backend is required. Alternatively, serve the folder:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Then visit <http://localhost:8000>. If Node.js is installed, `npm start` runs the same
server and `npm test` checks the timing and CSV export logic (no dependencies to install).

### Add questions and answers

Edit `questions.js`. Each entry has a `prompt` and four `answers` in A–D order.
Keep all 25 entries and their sequential `id` values. For example:

```js
{ id: 1, prompt: "Your question here", answers: ["First choice", "Second choice", "Third choice", "Fourth choice"] },
```

### Results and timing

Pressing **Begin assessment** starts timing immediately. Pressing **Submit assessment**
on question 25 stops timing and automatically downloads `{TAKER_NAME}_Assessment.csv`.
The completion page also has a button to download the same results again and a button
to start a fresh assessment. Filename characters that are invalid on common operating
systems are replaced with underscores; the participant's entered name is preserved in
the CSV. Repeated runs use the same requested filename; the browser may append a number
or ask before replacing an existing download.

Each CSV contains 25 data rows, one per question, with these columns:

| Columns | Content |
| --- | --- |
| `run_id`, `taker_name` | Unique identifier for the run and participant name |
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
refreshed or closed; the browser warns before leaving an active assessment. Completed
CSV downloads are ignored by Git to keep participant data out of the repository.

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
- **Dependent variable:** quiz score after a ~4.5-minute video (number of questions to be decided)

**How we'll test it**

- Every participant does both conditions (within-subjects)
- Two different videos with matching quizzes of similar difficulty (see [`videos/`](videos/))
- Order of conditions and videos is randomized
- Watch video → take quiz → short break → watch second video in other condition → take quiz

**Statistical test:** Paired t-test (Wilcoxon signed-rank if data isn't normal)

**Sample size:** About 34 participants (d = 0.5, α = 0.05, power = 0.80)

### Side-by-Side Comparison

| | Idea 1: Exercise & Attention | Idea 2: Fidget Toy & Learning |
| --- | --- | --- |
| Independent variable | Sitting vs. 2 min jumping jacks | No fidget toy vs. fidget toy |
| Dependent variable | Stroop reaction time & accuracy | Quiz score |
| Design | Within-subjects, randomized order | Within-subjects, randomized order |
| Session length | Practice + 2 conditions + 5 min rest | 2 videos (~4.5 min each) + 2 quizzes |
| Statistical test | Paired t-test / Wilcoxon signed-rank | Paired t-test / Wilcoxon signed-rank |
| Target sample | ~34 (d = 0.5, α = 0.05, power = 0.80) | ~34 (d = 0.5, α = 0.05, power = 0.80) |

## Recruitment Flyer

The recruitment flyer was made in Canva and is in [`flyer/`](flyer/):

- [`flyer.pdf`](flyer/flyer.pdf) is the printable letter-size version.
- [`flyer.png`](flyer/flyer.png) is the image version for sending to friends by text or social media.

![Recruitment flyer](flyer/flyer.png)

The flyer advertises a 20-minute session on Thursday, Oct 22 (before 6:00 PM) and Friday, Oct 23
(after 11:30 AM), with candy as a thank-you. Its QR code opens the Google Form where participants
pick their available time slots. We then confirm each person's slot and the room on campus.

**Note for the write-up:** the flyer shows squishy toys, so participants may guess that the study
is about fidget toys. This could shape their expectations, so we should mention it as a limitation.

## Status

Idea 2 (fidget toy and learning) is the study we are moving forward with. No data collection or
analysis has started yet — see the [To-Do's](#to-dos) above for the current plan.
