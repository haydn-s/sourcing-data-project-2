/* Timing, counterbalancing, and CSV logic are independent of the page so they can be verified. */
(function (root) {
  "use strict";

  const LETTERS = ["A", "B", "C", "D"];
  const VIDEO_IDS = ["A", "B"];
  const CONDITION_LABELS = { toy: "Fidget toy", none: "No fidget toy" };
  const GROUP_NUMBERS = [1, 2, 3, 4];
  const PARTS = [1, 2];
  // Counterbalancing from videos/README.md: the video order and the condition order
  // rotate across groups, so each video is watched with and without the fidget toy
  // equally often and each condition comes first equally often.
  const GROUPS = {
    1: [{ video: "A", condition: "toy" }, { video: "B", condition: "none" }],
    2: [{ video: "A", condition: "none" }, { video: "B", condition: "toy" }],
    3: [{ video: "B", condition: "toy" }, { video: "A", condition: "none" }],
    4: [{ video: "B", condition: "none" }, { video: "A", condition: "toy" }],
  };

  function validateQuestions(questions, label = "The quiz") {
    if (!Array.isArray(questions) || questions.length === 0) {
      throw new Error(`${label} needs at least one question.`);
    }
    questions.forEach((question, index) => {
      if (question.id !== index + 1 || typeof question.prompt !== "string" ||
          !Array.isArray(question.answers) || question.answers.length !== 4 ||
          question.answers.some((answer) => typeof answer !== "string")) {
        throw new Error(`${label} question ${index + 1} needs its sequential id, a prompt, and exactly four text answers.`);
      }
    });
    return questions;
  }

  function validateVideos(videos) {
    if (!Array.isArray(videos) || videos.length !== VIDEO_IDS.length) {
      throw new Error(`questions.js must contain one question set per video: ${VIDEO_IDS.join(" and ")}.`);
    }
    videos.forEach((video, index) => {
      if (!video || video.id !== VIDEO_IDS[index]) {
        throw new Error(`Question set ${index + 1} needs the id "${VIDEO_IDS[index]}".`);
      }
      if (typeof video.title !== "string" || !video.title.trim()) {
        throw new Error(`Video ${video.id} needs a title.`);
      }
      validateQuestions(video.questions, `Video ${video.id}`);
    });
    const [first, ...rest] = videos;
    if (rest.some((video) => video.questions.length !== first.questions.length)) {
      throw new Error("Both videos need the same number of questions so the two quizzes stay comparable.");
    }
    return videos;
  }

  // Which video and condition a participant gets, from their group and whether this
  // is their first or second quiz.
  function assignmentFor(group, part) {
    const groupNumber = Number(group);
    const partNumber = Number(part);
    if (!GROUP_NUMBERS.includes(groupNumber)) {
      throw new Error(`Choose a participant group from ${GROUP_NUMBERS[0]} through ${GROUP_NUMBERS.at(-1)}.`);
    }
    if (!PARTS.includes(partNumber)) {
      throw new Error("Choose whether this is the participant's first or second quiz.");
    }
    const { video, condition } = GROUPS[groupNumber][partNumber - 1];
    return { group: groupNumber, part: partNumber, video, condition, conditionLabel: CONDITION_LABELS[condition] };
  }

  function csvCell(value) {
    let text = String(value ?? "");
    // Keep participant names and editable content from becoming spreadsheet formulas.
    if (typeof value === "string" && /^[\s﻿]*[=+@-]/u.test(text)) text = "'" + text;
    return '"' + text.replace(/"/g, '""') + '"';
  }

  function filenameFor(name, videoId) {
    const safeName = name.trim().replace(/[<>:"/\\|?*\u0000-\u001f\u007f]/g, "_").replace(/[. ]+$/g, "") || "Participant";
    const video = VIDEO_IDS.includes(videoId) ? `_Video${videoId}` : "";
    return `${safeName}${video}_Assessment.csv`;
  }

  class Session {
    constructor({ name, group, part } = {}, videos, { clock = () => performance.now(), timestamp = () => new Date().toISOString(), runId = () => crypto.randomUUID() } = {}) {
      const library = validateVideos(videos);
      if (!String(name ?? "").trim()) throw new Error("Please enter your name.");
      const assignment = assignmentFor(group, part);
      const video = library.find((entry) => entry.id === assignment.video);
      this.name = String(name).trim();
      this.group = assignment.group;
      this.part = assignment.part;
      this.condition = assignment.condition;
      this.conditionLabel = assignment.conditionLabel;
      this.videoId = video.id;
      this.videoTitle = video.title;
      this.questions = video.questions.map((question) => ({ ...question, answers: [...question.answers] }));
      this.clock = clock;
      this.timestamp = timestamp;
      this.runId = runId();
      this.startedAt = timestamp();
      this.startedTick = clock();
      this.questionStartedTick = this.startedTick;
      this.currentIndex = 0;
      this.answers = Array(this.questions.length).fill(null);
      this.questionTimes = Array(this.questions.length).fill(0);
      this.completedAt = null;
      this.totalMilliseconds = null;
    }

    get answeredCount() {
      return this.answers.filter((answer) => answer !== null).length;
    }

    get lastIndex() {
      return this.questions.length - 1;
    }

    select(answerIndex) {
      if (this.completedAt) throw new Error("This assessment is already complete.");
      if (!Number.isInteger(answerIndex) || answerIndex < 0 || answerIndex >= 4) throw new Error("Choose an answer from A through D.");
      this.answers[this.currentIndex] = answerIndex;
    }

    goTo(index) {
      if (this.completedAt) throw new Error("This assessment is already complete.");
      if (!Number.isInteger(index) || index < 0 || index >= this.questions.length) throw new Error("Invalid question number.");
      const tick = this.clock();
      this.questionTimes[this.currentIndex] += tick - this.questionStartedTick;
      this.currentIndex = index;
      this.questionStartedTick = tick;
    }

    finish() {
      if (this.completedAt) return;
      if (this.answeredCount !== this.questions.length) throw new Error("Please answer every question before submitting.");
      const tick = this.clock();
      this.questionTimes[this.currentIndex] += tick - this.questionStartedTick;
      this.totalMilliseconds = tick - this.startedTick;
      this.completedAt = this.timestamp();
    }

    get filename() {
      return filenameFor(this.name, this.videoId);
    }

    toCsv() {
      if (!this.completedAt) throw new Error("Complete the assessment before downloading results.");
      const rows = [["run_id", "taker_name", "participant_group", "quiz_number", "video_id", "video_title", "condition", "started_at", "completed_at", "total_time_seconds", "question_number", "question_text", "option_a", "option_b", "option_c", "option_d", "answer_letter", "answer_text", "question_time_seconds"]];
      this.questions.forEach((question, index) => {
        const answer = this.answers[index];
        rows.push([this.runId, this.name, this.group, this.part, this.videoId, this.videoTitle, this.conditionLabel,
          this.startedAt, this.completedAt, (this.totalMilliseconds / 1000).toFixed(3),
          question.id, question.prompt, ...question.answers, LETTERS[answer], question.answers[answer],
          (this.questionTimes[index] / 1000).toFixed(3)]);
      });
      return "﻿" + rows.map((row) => row.map(csvCell).join(",")).join("\r\n") + "\r\n";
    }
  }

  const api = { Session, validateQuestions, validateVideos, assignmentFor, filenameFor, GROUP_NUMBERS, PARTS, CONDITION_LABELS };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Assessment = api;
})(globalThis);
