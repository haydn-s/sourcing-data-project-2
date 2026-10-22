const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const { Session, validateQuestions, validateVideos, assignmentFor, filenameFor } = require("../assessment.js");

function blankVideos() {
  return JSON.parse(fs.readFileSync(require.resolve("../questions.json"), "utf8"));
}

function setup({ name = "Test Participant", group = 1, part = 1 } = {}, videos = blankVideos()) {
  let tick = 10_000;
  let date = "2026-10-15T00:00:00.000Z";
  const session = new Session({ name, group, part }, videos, {
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

test("questions.json has a filled-in quiz for Video A and an equally sized set for Video B", () => {
  const videos = blankVideos();
  validateVideos(videos);
  assert.deepEqual(videos.map((video) => video.id), ["A", "B"]);
  assert.equal(videos[0].questions.length, videos[1].questions.length);
  for (const video of videos) {
    assert.ok(video.title.trim(), "each video needs a title for the CSV");
  }
  // Video A is the study video in the one-video design: every question needs real text.
  for (const question of videos[0].questions) {
    assert.ok(question.prompt.trim(), `Video A question ${question.id} needs a prompt`);
    assert.ok(question.answers.every((answer) => answer.trim()), `Video A question ${question.id} needs four answers`);
  }
  assert.throws(() => validateVideos(videos.slice(1)), /one question set per video/);
  const uneven = blankVideos();
  uneven[1].questions.pop();
  assert.throws(() => validateVideos(uneven), /same number of questions/);
  const renumbered = blankVideos();
  renumbered[0].questions.shift();
  assert.throws(() => validateVideos(renumbered), /Video A question 1/);
  const shortAnswers = blankVideos();
  shortAnswers[1].questions[0].answers.pop();
  assert.throws(() => validateVideos(shortAnswers), /Video B question 1/);
  assert.throws(() => validateQuestions([]), /at least one question/);
});

test("group and quiz number decide the video and condition, counterbalanced across groups", () => {
  const combinations = [];
  for (const group of [1, 2, 3, 4]) {
    const first = assignmentFor(group, 1);
    const second = assignmentFor(group, 2);
    assert.notEqual(first.video, second.video, "each participant watches both videos");
    assert.notEqual(first.condition, second.condition, "each participant does both conditions");
    combinations.push(`${first.video}-${first.condition}`, `${second.video}-${second.condition}`);
  }
  const counts = {};
  for (const combination of combinations) counts[combination] = (counts[combination] ?? 0) + 1;
  assert.deepEqual(counts, { "A-toy": 2, "A-none": 2, "B-toy": 2, "B-none": 2 });
  assert.deepEqual(assignmentFor("2", "1"),
    { group: 2, part: 1, video: "A", condition: "none", conditionLabel: "No fidget toy" });
  assert.throws(() => assignmentFor(5, 1), /group from 1 through 4/);
  assert.throws(() => assignmentFor(1, 3), /first or second quiz/);
});

test("a session asks only the questions for its assigned video", () => {
  const videos = blankVideos();
  videos[0].questions[0].prompt = "Video A question";
  videos[1].questions[0].prompt = "Video B question";
  const { session } = setup({ group: 3, part: 1 }, videos);
  assert.equal(session.videoId, "B");
  assert.equal(session.videoTitle, videos[1].title);
  assert.equal(session.conditionLabel, "Fidget toy");
  assert.equal(session.questions[0].prompt, "Video B question");
  assert.equal(session.questions.length, videos[1].questions.length);
  assert.equal(session.lastIndex, videos[1].questions.length - 1);
  assert.equal(setup({ group: 3, part: 2 }, videos).session.videoId, "A");
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
  assert.throws(() => setup({ part: "" }), /first or second quiz/);
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
  const { session, advance } = setup({ name: '  Alex, "A"  ', group: 2, part: 1 }, videos);
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
  videos[1].questions[0].prompt = ' =HYPERLINK("https://example.com")';
  const { session, advance } = setup({ name: "=2+2", group: 1, part: 2 }, videos);
  answerRemaining(session, advance);
  session.finish();
  const [header, row] = parseCsv(session.toCsv());
  assert.equal(row[header.indexOf("taker_name")], "'=2+2");
  assert.equal(row[header.indexOf("question_text")], "'" + videos[1].questions[0].prompt);
});

test("filenames identify the participant and which video they answered", () => {
  assert.equal(filenameFor("  Jane Doe  "), "Jane Doe_Assessment.csv");
  assert.equal(filenameFor("Jane Doe", "B"), "Jane Doe_VideoB_Assessment.csv");
  assert.equal(filenameFor("Zoë 李", "A"), "Zoë 李_VideoA_Assessment.csv");
  assert.equal(filenameFor("../Alex:Study?", "A"), ".._Alex_Study__VideoA_Assessment.csv");
  const { session } = setup({ group: 4, part: 1 });
  assert.equal(session.filename, "Test Participant_VideoB_Assessment.csv");
  assert.notEqual(session.filename, setup({ group: 4, part: 2 }).session.filename,
    "a participant's two quizzes must not share a filename");
});
