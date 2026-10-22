# sourcing-data-project-2

Project 2 for Duke University AIPI-510 (Sourcing Data for Analytics), taken in Fall 2026.

## Streamlit assessment

Deploy `streamlit_app.py` from the `streamlit-form` branch. Participants enter their ID,
confirm their group and quiz, and answer one multiple-choice question at a time. They
can go back and change an answer. Submitting the final question automatically saves a
CSV in **`data/raw/`**, the repository's existing raw-data directory. A download button
also provides a backup copy.

The current study uses **Video A only**: select **Group 1, first quiz** for the fidget
condition or **Group 2, first quiz** for no fidget toy. Video A's 10 questions are filled
in. Video B is still a blank template; the Streamlit app prevents starting that quiz.
See [`videos/README.md`](videos/README.md) for the session protocol and answer key.

### Run locally

Use Python 3.12 and run these commands from the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
QUIZ_STORAGE=local streamlit run streamlit_app.py
```

Open the local address printed by Streamlit (normally <http://localhost:8501>).
Local mode writes directly to this checkout's `data/raw/`, regardless of the working
directory. It needs no GitHub token. Do not use local mode for Community Cloud data
collection: its server filesystem is temporary and local writes do not update GitHub.

### Deploy on Streamlit Community Cloud

1. Push the completed `streamlit-form` branch to GitHub.
2. In Streamlit, create an app with repository **`haydn-s/sourcing-data-project-2`**,
   branch **`streamlit-form`**, and main file **`streamlit_app.py`**. Choose Python 3.12
   in Advanced settings. `requirements.txt` installs Streamlit automatically.
3. Create a [fine-grained GitHub personal access token](https://github.com/settings/personal-access-tokens/new)
   restricted to this repository with **Contents: Read and write**. The account issuing
   the token must have write access. Set an expiration covering the collection session.
4. In the app's **Advanced settings → Secrets**, paste the contents of
   [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example), replacing the
   placeholder token:

   ```toml
   [storage]
   backend = "github"

   [github]
   repository = "haydn-s/sourcing-data-project-2"
   branch = "data-collection-scaffolding"
   token = "YOUR_FINE_GRAINED_TOKEN"
   ```

5. Deploy. Complete a test quiz and verify that a CSV appears in `data/raw/` on the
   **`data-collection-scaffolding` branch** before collecting real responses. Remove
   that test file afterward.

Each submission creates a commit containing one CSV on the configured output branch.
That branch must already exist and allow the token to create commits. The existing
`data-collection-scaffolding` branch is the recommended output branch. Keep it separate
from the deployed `streamlit-form` branch so response commits do not cause Streamlit to
reload the app while other participants are answering. If you deploy another branch
later, keep the output branch separate from it too. Pull the output branch to retrieve
the CSVs on your computer.

The GitHub token stays on the server; participants do not need GitHub accounts. Never
commit an actual `.streamlit/secrets.toml`; it is ignored by Git. For local testing of
GitHub saving, copy the example to that ignored path, fill in the token, and run
`streamlit run streamlit_app.py` without `QUIZ_STORAGE=local`. Without configured
credentials, the app blocks new assessments instead of silently writing temporary files.

For setup details, see [Streamlit's Secrets guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
and [GitHub's Contents API permissions](https://docs.github.com/en/rest/repos/contents#create-or-update-file-contents).

### Results and recovery

Files are named `{PARTICIPANT}_Video{A_or_B}_{RUN_UUID}_Assessment.csv`. Separate
participants and repeated runs never share a filename. Repeated saving of the same run
is idempotent, and existing data is never overwritten. The original participant entry
is preserved in the CSV; unsafe filename characters are replaced with underscores.

The completion page confirms success only after the local write or GitHub commit is
confirmed. On failure, the answers and original timing stay in the session; the
participant can **Try saving again** or **Download a copy of results** as a backup.
Starting another assessment stays disabled until saving succeeds. Do not refresh or
close the page before confirmation: unfinished and unsaved sessions are held in memory
and can be lost on refresh, disconnection or an app restart.

Use participant IDs (P01, P02, …), as described in the protocol. This repository is
public, so committed CSV contents and filenames are publicly visible.

Each CSV contains one data row per question and preserves the HTML quiz's 19 columns:

| Columns | Content |
| --- | --- |
| `run_id`, `taker_name` | Unique run identifier and the entered participant ID or name |
| `participant_group`, `quiz_number` | Group 1–4 and first or second quiz |
| `video_id`, `video_title`, `condition` | Video and condition determined by the assignment |
| `started_at`, `completed_at` | UTC timestamps in ISO 8601 format |
| `total_time_seconds` | Time from Begin through final submission, repeated on each row |
| `question_number`, `question_text` | Question number and configured prompt |
| `option_a`, `option_b`, `option_c`, `option_d` | The four configured choices |
| `answer_letter`, `answer_text` | Final selected choice and its text |
| `question_time_seconds` | Time spent on that question, including repeat visits |

Timing uses the server's monotonic clock, includes network and screen transitions,
and is exported to three decimal places. Time spent saving is excluded. Question
durations add up to the total apart from millisecond rounding. Formula-like text is
prefixed with an apostrophe so spreadsheets treat it as text. CSVs use UTF-8 with a BOM.

### Questions and assignments

Edit **[`questions.json`](questions.json)**, the shared question bank for Streamlit
and the original HTML quiz. Each video has an `id`, `title` and list of questions:

```json
{"id": 1, "prompt": "Your question here", "answers": ["First choice", "Second choice", "Third choice", "Fourth choice"]}
```

Each question needs four answers in A–D order and sequential IDs starting at 1. Both
videos must have the same number of questions. An assigned video with any blank prompt
or answer cannot start in Streamlit. The app does not expose correct answers or scores;
[`videos/answer_key.csv`](videos/answer_key.csv) is available for later scoring.

The original counterbalancing remains available if the two-video design is resumed:

| Group | First quiz | Second quiz |
| --- | --- | --- |
| 1 | Video A, fidget toy | Video B, no fidget toy |
| 2 | Video A, no fidget toy | Video B, fidget toy |
| 3 | Video B, fidget toy | Video A, no fidget toy |
| 4 | Video B, no fidget toy | Video A, fidget toy |

**Start the next quiz** appears only when its questions are filled in. It preserves
the participant and group. **Start a new assessment** clears the participant details.

### Verification

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
npm test
```

The Python checks exercise a full Streamlit quiz, review and answer changes, separate
participant sessions, automatic local storage, save failures and retries, CSV schema,
timing, and mocked GitHub requests. GitHub tests do not create real commits. The Node
checks cover the original HTML quiz logic and need no installed Node dependencies.

### Original HTML version

The HTML version remains available for reference. Serve the repository over HTTP with
`npm start` or `python3 -m http.server 8000 --bind 127.0.0.1`, then open
<http://localhost:8000>. Opening `index.html` directly as a local file is no longer
supported because both frontends now load `questions.json`. The HTML version downloads
CSVs in the browser; automatic server-side saving is provided by Streamlit.

## Data collection

- [`data/raw/`](data/raw/): original response CSVs; keep unchanged during analysis.
- [`data/processed/`](data/processed/): cleaned or combined outputs derived from raw data.

The `.gitkeep` files preserve empty directories after cloning. Assessment CSVs in these
directories can be committed normally; loose downloads elsewhere are ignored. Use the
`data-collection-scaffolding` branch for collected responses and pull before pushing
manual changes to it.

## To-Do's

Project plan for the fidget toy study ([Idea 2](#idea-2-does-using-a-fidget-toy-help-or-hurt-learning), below).

### By Friday (Oct 16), before class

- [x] **Sabrina:** Pick the video(s) for the study (see [`videos/`](videos/))
- [x] **Sabrina:** Create the recruitment flyer to send to friends
- [ ] **Sabrina:** Create the Google form for participant intake
- [x] **Haydn:** Build the HTML quiz form, leaving the questions blank so we can fill them in once the videos are picked

### GitHub branches and PRs

- [x] **Sabrina:** `flyer` branch, with a PR to add the recruitment flyer to the repo (and document it in the README)
- [x] **Sabrina:** `videos` branch, with a PR to add the video links and quiz questions to the repo
- [x] **Haydn:** `question-form-template` branch, with [PR #2](https://github.com/haydn-s/sourcing-data-project-2/pull/2) to add the HTML quiz form
- [x] **Haydn:** `html-form-updates` branch, with [PR #4](https://github.com/haydn-s/sourcing-data-project-2/pull/4) to add one question set per video and record each run's group, video and condition
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
- **Dependent variable:** quiz score out of 10 after a 4.5-minute video

**How we'll test it**

- Two independent groups (between-subjects): each participant is randomly assigned to the fidget
  toy group or the no-fidget-toy group
- Everyone watches the same video and takes the same 10-question quiz (see [`videos/`](videos/))
- Fidget group holds a squishy toy while watching; the no-fidget group doesn't
- Watch video → take quiz (about 10 minutes per participant)

**Statistical test:** Independent-samples t-test, using Welch's version if the group variances
differ (Mann-Whitney U if the data isn't normal)

**Sample size:** With two independent groups, a two-sided test at α = 0.05 and 80% power needs
about 26 per group (52 total) to detect a large effect (d = 0.8), or about 64 per group (128 total)
for a medium effect (d = 0.5). The power analysis needs to be updated for this design.

### Side-by-Side Comparison

| | Idea 1: Exercise & Attention | Idea 2: Fidget Toy & Learning |
| --- | --- | --- |
| Independent variable | Sitting vs. 2 min jumping jacks | No fidget toy vs. fidget toy |
| Dependent variable | Stroop reaction time & accuracy | Quiz score |
| Design | Within-subjects, randomized order | Between-subjects, two randomized groups |
| Session length | Practice + 2 conditions + 5 min rest | 1 video (4.5 min) + 1 quiz |
| Statistical test | Paired t-test / Wilcoxon signed-rank | Independent-samples t-test / Mann-Whitney U |
| Target sample | ~34 (d = 0.5, α = 0.05, power = 0.80) | ~52 (d = 0.8) to ~128 (d = 0.5), α = 0.05, power = 0.80 |

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

Idea 2 (fidget toy and learning) is the study we are moving forward with. No data collection or
analysis has started yet — see the [To-Do's](#to-dos) above for the current plan.
