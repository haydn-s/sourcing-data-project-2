"""Quiz assignment, timing and CSV format shared by the Streamlit screens."""

from copy import deepcopy
import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import time
from uuid import uuid4


ROOT = Path(__file__).resolve().parent
LETTERS = "ABCD"
GROUPS = {
    1: "Fidget toy",
    2: "No fidget toy",
}
CSV_COLUMNS = (
    "run_id", "taker_name", "participant_group", "quiz_number", "video_id",
    "video_title", "condition", "started_at", "completed_at", "total_time_seconds",
    "question_number", "question_text", "option_a", "option_b", "option_c",
    "option_d", "answer_letter", "answer_text", "question_time_seconds",
)


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def load_videos(path=ROOT / "questions.json"):
    videos = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(videos, list) or len(videos) != 1:
        raise ValueError("The question bank must contain only Quiz A.")
    for video, video_id in zip(videos, ("A",)):
        if not isinstance(video, dict) or video.get("id") != video_id:
            raise ValueError("The question bank must contain only Quiz A.")
        if not isinstance(video.get("title"), str) or not video["title"].strip():
            raise ValueError(f"Video {video_id} needs a title.")
        if not isinstance(video.get("embed_url"), str) or not video["embed_url"].startswith("https://embed.ted.com/talks/"):
            raise ValueError("Quiz A needs its TED video embed URL.")
        questions = video.get("questions")
        if not isinstance(questions, list) or not questions:
            raise ValueError(f"Video {video_id} needs at least one question.")
        for number, question in enumerate(questions, 1):
            if (not isinstance(question, dict) or question.get("id") != number
                    or not isinstance(question.get("prompt"), str)
                    or not isinstance(question.get("answers"), list)
                    or len(question["answers"]) != 4
                    or any(not isinstance(answer, str) for answer in question["answers"])):
                raise ValueError(f"Video {video_id} question {number} needs its sequential id, prompt and four text answers.")
    return videos


def assignment_for(group):
    if type(group) is not int or group not in GROUPS:
        raise ValueError("Choose participant group 1 or 2.")
    return "A", GROUPS[group]


def video_ready(video):
    return all(q["prompt"].strip() and all(a.strip() for a in q["answers"])
               for q in video["questions"])


def csv_cell(value):
    if isinstance(value, str) and re.match(r"^[\s\ufeff]*[=+@-]", value):
        return "'" + value
    return value


class Session:
    def __init__(self, name, group, videos, *, clock=time.perf_counter,
                 timestamp=utc_timestamp, run_id=None):
        self.name = name.strip()
        if not self.name or len(self.name) > 120:
            raise ValueError("Enter a participant ID or name of at most 120 characters.")
        self.video_id, self.condition = assignment_for(group)
        video = next(v for v in videos if v["id"] == self.video_id)
        if not video_ready(video):
            raise ValueError(f"Video {self.video_id}'s quiz is not ready. Please check the assignment with the researcher.")
        self.group = group
        self.part = 1  # Retain quiz_number in the existing CSV schema.
        self.video_title = video["title"]
        self.questions = deepcopy(video["questions"])
        self.run_id = run_id or str(uuid4())
        self.clock, self.timestamp = clock, timestamp
        self.started_at = timestamp()
        self.started_tick = self.question_started_tick = clock()
        self.current_index = 0
        self.answers = [None] * len(self.questions)
        self.question_times = [0.0] * len(self.questions)
        self.completed_at = None
        self.total_seconds = None

    @property
    def answered_count(self):
        return sum(answer is not None for answer in self.answers)

    @property
    def filename(self):
        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]', "_", self.name).rstrip(". ")
        safe_name = safe_name.encode("utf-8")[:100].decode("utf-8", errors="ignore") or "Participant"
        return f"{safe_name}_Video{self.video_id}_{self.run_id}_Assessment.csv"

    def select(self, answer):
        if self.completed_at:
            raise ValueError("This assessment is already complete.")
        if type(answer) is not int or answer not in range(4):
            raise ValueError("Choose an answer from A through D.")
        self.answers[self.current_index] = answer

    def go_to(self, index):
        if self.completed_at:
            raise ValueError("This assessment is already complete.")
        if type(index) is not int or index not in range(len(self.questions)):
            raise ValueError("Invalid question number.")
        tick = self.clock()
        self.question_times[self.current_index] += tick - self.question_started_tick
        self.current_index = index
        self.question_started_tick = tick

    def finish(self):
        if self.completed_at:
            return
        if self.answered_count != len(self.questions):
            raise ValueError("Please answer every question before submitting.")
        tick = self.clock()
        self.question_times[self.current_index] += tick - self.question_started_tick
        self.total_seconds = tick - self.started_tick
        self.completed_at = self.timestamp()

    def to_csv(self):
        if not self.completed_at:
            raise ValueError("Complete the assessment before exporting results.")
        output = io.StringIO(newline="")
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        writer.writerow(CSV_COLUMNS)
        for index, question in enumerate(self.questions):
            answer = self.answers[index]
            row = (
                self.run_id, self.name, self.group, self.part, self.video_id,
                self.video_title, self.condition, self.started_at, self.completed_at,
                f"{self.total_seconds:.3f}", question["id"], question["prompt"],
                *question["answers"], LETTERS[answer], question["answers"][answer],
                f"{self.question_times[index]:.3f}",
            )
            writer.writerow([csv_cell(value) for value in row])
        return output.getvalue().encode("utf-8-sig")
