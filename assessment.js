/* Timing and CSV logic are independent of the page so they can be verified. */
(function (root) {
  "use strict";

  const LETTERS = ["A", "B", "C", "D"];

  function validateQuestions(questions) {
    if (!Array.isArray(questions) || questions.length !== 25) {
      throw new Error("questions.js must contain exactly 25 questions.");
    }
    questions.forEach((question, index) => {
      if (question.id !== index + 1 || typeof question.prompt !== "string" ||
          !Array.isArray(question.answers) || question.answers.length !== 4 ||
          question.answers.some((answer) => typeof answer !== "string")) {
        throw new Error(`Question ${index + 1} needs its sequential id, a prompt, and exactly four text answers.`);
      }
    });
  }

  function csvCell(value) {
    let text = String(value ?? "");
    // Keep participant names and editable content from becoming spreadsheet formulas.
    if (typeof value === "string" && /^[\s\uFEFF]*[=+@-]/u.test(text)) text = "'" + text;
    return '"' + text.replace(/"/g, '""') + '"';
  }

  function filenameFor(name) {
    const safeName = name.trim().replace(/[<>:"/\\|?*\u0000-\u001f\u007f]/g, "_").replace(/[. ]+$/g, "") || "Participant";
    return `${safeName}_Assessment.csv`;
  }

  class Session {
    constructor(name, questions, { clock = () => performance.now(), timestamp = () => new Date().toISOString(), runId = () => crypto.randomUUID() } = {}) {
      validateQuestions(questions);
      if (!name.trim()) throw new Error("Please enter your name.");
      this.name = name.trim();
      this.questions = questions.map((question) => ({ ...question, answers: [...question.answers] }));
      this.clock = clock;
      this.timestamp = timestamp;
      this.runId = runId();
      this.startedAt = timestamp();
      this.startedTick = clock();
      this.questionStartedTick = this.startedTick;
      this.currentIndex = 0;
      this.answers = Array(questions.length).fill(null);
      this.questionTimes = Array(questions.length).fill(0);
      this.completedAt = null;
      this.totalMilliseconds = null;
    }

    get answeredCount() {
      return this.answers.filter((answer) => answer !== null).length;
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

    toCsv() {
      if (!this.completedAt) throw new Error("Complete the assessment before downloading results.");
      const rows = [["run_id", "taker_name", "started_at", "completed_at", "total_time_seconds", "question_number", "question_text", "option_a", "option_b", "option_c", "option_d", "answer_letter", "answer_text", "question_time_seconds"]];
      this.questions.forEach((question, index) => {
        const answer = this.answers[index];
        rows.push([this.runId, this.name, this.startedAt, this.completedAt,
          (this.totalMilliseconds / 1000).toFixed(3), question.id, question.prompt,
          ...question.answers, LETTERS[answer], question.answers[answer],
          (this.questionTimes[index] / 1000).toFixed(3)]);
      });
      return "\uFEFF" + rows.map((row) => row.map(csvCell).join(",")).join("\r\n") + "\r\n";
    }
  }

  const api = { Session, validateQuestions, filenameFor };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Assessment = api;
})(globalThis);
