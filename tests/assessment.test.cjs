const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { Session, validateQuestions, validateVideos, assignmentFor, filenameFor } = require("../assessment.js");

function blankVideos() {
  return JSON.parse(fs.readFileSync(require.resolve("../questions.json"), "utf8"));
}

function setup({ name = "Test Participant", group = 1 } = {}, videos = blankVideos()) {
  let tick = 10_000;
  let date = "2026-10-15T00:00:00.000Z";
  const session = new Session({ name, group }, videos, {
    clock: () => tick,
    timestamp: () => date,
    runId: () => "test-run-id",
  });
  return { session, advance: (ms) => { tick += ms; }, setDate: (value) => { date = value; } };
}

function answerRemaining(session, advance) {
  for (let i = session.currentIndex; i < session.questions.length; i++) {
    session.select(i % 4);
    advance(1000);
    if (i < session.lastIndex) session.goTo(i + 1);
  }
}

// Parse quoted CSV fields, including commas, escaped quotes, and line breaks.
function parseCsv(csv) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  const text = csv.replace(/^﻿/, "");
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (char === '"') {
      if (quoted && text[i + 1] === '"') { field += '"'; i++; }
      else quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(field); field = "";
    } else if (char === "\r" && text[i + 1] === "\n" && !quoted) {
      row.push(field); rows.push(row); row = []; field = ""; i++;
    } else field += char;
  }
  return rows;
}

test("questions.json contains only the filled-in Quiz A", () => {
  const videos = blankVideos();
  validateVideos(videos);
  assert.deepEqual(videos.map((video) => video.id), ["A"]);
  assert.ok(videos[0].title.trim());
  assert.ok(videos[0].embed_url.startsWith("https://embed.ted.com/talks/"));
  for (const question of videos[0].questions) {
    assert.ok(question.prompt.trim());
    assert.ok(question.answers.every((answer) => answer.trim()));
  }
  assert.throws(() => validateVideos([]), /only Quiz A/);
  assert.throws(() => validateVideos([...videos, videos[0]]), /only Quiz A/);
  const renumbered = blankVideos();
  renumbered[0].questions.shift();
  assert.throws(() => validateVideos(renumbered), /Video A question 1/);
  const shortAnswers = blankVideos();
  shortAnswers[0].questions[0].answers.pop();
  assert.throws(() => validateVideos(shortAnswers), /Video A question 1/);
  assert.throws(() => validateQuestions([]), /at least one question/);
});

test("only groups 1 and 2 are accepted, and both take Quiz A", () => {
  assert.deepEqual(assignmentFor(1),
    { group: 1, part: 1, video: "A", condition: "toy", conditionLabel: "Fidget toy" });
  assert.deepEqual(assignmentFor("2"),
    { group: 2, part: 1, video: "A", condition: "none", conditionLabel: "No fidget toy" });
  for (const group of [0, 3, 4, ""]) assert.throws(() => assignmentFor(group), /group 1 or 2/);
});

test("both groups receive the same Video A questions", () => {
  const videos = blankVideos();
  const first = setup({ group: 1 }, videos).session;
  const second = setup({ group: 2 }, videos).session;
  assert.equal(first.videoId, "A");
  assert.equal(second.videoId, "A");
  assert.deepEqual(first.questions, second.questions);
  assert.equal(first.conditionLabel, "Fidget toy");
  assert.equal(second.conditionLabel, "No fidget toy");
  assert.equal(first.part, 1);
});

test("elapsed time includes the full session and accumulates repeated visits to a question", () => {
  const { session, advance, setDate } = setup();
  advance(1500);
  session.select(0);
  session.goTo(1);
  advance(2250);
  session.select(1);
  session.goTo(0);
  advance(750);
  session.select(3);
  session.goTo(1);
  assert.equal(session.answers[0], 3);
  assert.equal(session.questionTimes[0], 2250);
  answerRemaining(session, advance);
  setDate("2026-10-15T00:00:13.500Z");
  session.finish();
  assert.equal(session.totalMilliseconds, 13_500);
  assert.equal(session.questionTimes[1], 3250);
  assert.equal(session.questionTimes.reduce((sum, ms) => sum + ms, 0), session.totalMilliseconds);
  assert.equal(session.completedAt, "2026-10-15T00:00:13.500Z");
  const csv = session.toCsv();
  advance(10_000);
  session.finish();
  assert.equal(session.toCsv(), csv, "re-downloading must keep the original timing");
  assert.throws(() => session.select(1), /already complete/);
  assert.throws(() => session.goTo(0), /already complete/);
});

test("incomplete quizzes cannot finish or export, and invalid details are rejected", () => {
  assert.throws(() => setup({ name: "   " }), /name/);
  assert.throws(() => setup({ group: "" }), /group/);
  assert.throws(() => setup({ group: 3 }), /group 1 or 2/);
  const { session } = setup();
  assert.throws(() => session.finish(), /every question/);
  assert.throws(() => session.toCsv(), /Complete/);
  assert.throws(() => session.select(4), /A through D/);
  assert.throws(() => session.select(1.5), /A through D/);
  assert.throws(() => session.goTo(-1), /Invalid question/);
  assert.throws(() => session.goTo(session.questions.length), /Invalid question/);
});

test("CSV records the group, video, and condition alongside answers and timing", () => {
  const videos = blankVideos();
  videos[0].questions[0].prompt = 'A prompt, with "quotes"\nand a second line';
  videos[0].questions[0].answers[0] = 'An answer, with "quotes"';
  const { session, advance } = setup({ name: '  Alex, "A"  ', group: 2 }, videos);
  answerRemaining(session, advance);
  session.finish();
  const rows = parseCsv(session.toCsv());
  const questionCount = videos[0].questions.length;
  assert.equal(rows.length, questionCount + 1);
  assert.ok(rows.every((row) => row.length === 19));
  const [header, first, ...rest] = rows;
  const record = Object.fromEntries(header.map((key, index) => [key, first[index]]));
  assert.equal(record.run_id, "test-run-id");
  assert.equal(record.taker_name, 'Alex, "A"');
  assert.equal(record.participant_group, "2");
  assert.equal(record.quiz_number, "1");
  assert.equal(record.video_id, "A");
  assert.equal(record.video_title, videos[0].title);
  assert.equal(record.condition, "No fidget toy");
  assert.equal(record.question_text, videos[0].questions[0].prompt);
  assert.equal(record.answer_text, videos[0].questions[0].answers[0]);
  assert.equal(record.answer_letter, "A");
  assert.equal(record.question_time_seconds, "1.000");
  assert.equal(record.total_time_seconds, (questionCount * 1).toFixed(3));
  assert.equal(record.started_at, "2026-10-15T00:00:00.000Z");
  assert.equal(record.completed_at, "2026-10-15T00:00:00.000Z");
  assert.equal(rest.at(-1)[header.indexOf("question_number")], String(questionCount));
  assert.equal(rest.at(-1)[header.indexOf("video_id")], "A", "every row carries the run's video");
});

test("CSV safely treats formula-like names and question content as text", () => {
  const videos = blankVideos();
  videos[0].questions[0].prompt = ' =HYPERLINK("https://example.com")';
  const { session, advance } = setup({ name: "=2+2", group: 1 }, videos);
  answerRemaining(session, advance);
  session.finish();
  const [header, row] = parseCsv(session.toCsv());
  assert.equal(row[header.indexOf("taker_name")], "'=2+2");
  assert.equal(row[header.indexOf("question_text")], "'" + videos[0].questions[0].prompt);
});

test("filenames identify the participant and Quiz A", () => {
  assert.equal(filenameFor("  Jane Doe  "), "Jane Doe_Assessment.csv");
  assert.equal(filenameFor("Jane Doe", "A"), "Jane Doe_VideoA_Assessment.csv");
  assert.equal(filenameFor("Zoë 李", "A"), "Zoë 李_VideoA_Assessment.csv");
  assert.equal(filenameFor("../Alex:Study?", "A"), ".._Alex_Study__VideoA_Assessment.csv");
  assert.equal(setup({ group: 2 }).session.filename, "Test Participant_VideoA_Assessment.csv");
});
