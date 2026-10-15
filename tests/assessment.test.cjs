const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const { Session, validateQuestions, filenameFor } = require("../assessment.js");

function blankQuestions() {
  const context = { window: {} };
  vm.runInNewContext(fs.readFileSync(require.resolve("../questions.js"), "utf8"), context);
  return JSON.parse(JSON.stringify(context.window.ASSESSMENT_QUESTIONS));
}

function setup(name = "Test Participant", questions = blankQuestions()) {
  let tick = 10_000;
  let date = "2026-10-15T00:00:00.000Z";
  const session = new Session(name, questions, {
    clock: () => tick,
    timestamp: () => date,
    runId: () => "test-run-id",
  });
  return { session, advance: (ms) => { tick += ms; }, setDate: (value) => { date = value; } };
}

function answerRemaining(session, advance) {
  for (let i = session.currentIndex; i < 25; i++) {
    session.select(i % 4);
    advance(1000);
    if (i < 24) session.goTo(i + 1);
  }
}

// Parse quoted CSV fields, including commas, escaped quotes, and line breaks.
function parseCsv(csv) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  const text = csv.replace(/^\uFEFF/, "");
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

test("the editable template has exactly 25 blank questions and four blank answers each", () => {
  const questions = blankQuestions();
  validateQuestions(questions);
  assert.equal(questions.length, 25);
  for (const question of questions) {
    assert.equal(question.prompt, "");
    assert.deepEqual(question.answers, ["", "", "", ""]);
  }
  assert.throws(() => validateQuestions(questions.slice(1)), /25 questions/);
  questions[0].answers.pop();
  assert.throws(() => validateQuestions(questions), /four text answers/);
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
  setDate("2026-10-15T00:00:28.500Z");
  session.finish();
  assert.equal(session.totalMilliseconds, 28_500);
  assert.equal(session.questionTimes[1], 3250);
  assert.equal(session.questionTimes.reduce((sum, ms) => sum + ms, 0), session.totalMilliseconds);
  assert.equal(session.completedAt, "2026-10-15T00:00:28.500Z");
  const csv = session.toCsv();
  advance(10_000);
  session.finish();
  assert.equal(session.toCsv(), csv, "re-downloading must keep the original timing");
  assert.throws(() => session.select(1), /already complete/);
  assert.throws(() => session.goTo(0), /already complete/);
});

test("incomplete assessments cannot finish or export, and invalid selections are rejected", () => {
  assert.throws(() => setup("   "), /name/);
  const { session } = setup();
  assert.throws(() => session.finish(), /every question/);
  assert.throws(() => session.toCsv(), /Complete/);
  assert.throws(() => session.select(4), /A through D/);
  assert.throws(() => session.select(1.5), /A through D/);
  assert.throws(() => session.goTo(-1), /Invalid question/);
});

test("CSV includes all answers, timing, timestamps, and editable content with valid escaping", () => {
  const questions = blankQuestions();
  questions[0].prompt = 'A prompt, with "quotes"\nand a second line';
  questions[0].answers[0] = 'An answer, with "quotes"';
  const { session, advance } = setup('  Alex, "A"  ', questions);
  answerRemaining(session, advance);
  session.finish();
  const rows = parseCsv(session.toCsv());
  assert.equal(rows.length, 26);
  assert.ok(rows.every((row) => row.length === 14));
  const [header, first, ...rest] = rows;
  const record = Object.fromEntries(header.map((key, i) => [key, first[i]]));
  assert.equal(record.run_id, "test-run-id");
  assert.equal(record.taker_name, 'Alex, "A"');
  assert.equal(record.question_text, questions[0].prompt);
  assert.equal(record.answer_text, questions[0].answers[0]);
  assert.equal(record.answer_letter, "A");
  assert.equal(record.question_time_seconds, "1.000");
  assert.equal(record.total_time_seconds, "25.000");
  assert.equal(record.started_at, "2026-10-15T00:00:00.000Z");
  assert.equal(record.completed_at, "2026-10-15T00:00:00.000Z");
  assert.equal(rest.at(-1)[5], "25");
});

test("CSV safely treats formula-like names and question content as text", () => {
  const questions = blankQuestions();
  questions[0].prompt = ' =HYPERLINK("https://example.com")';
  const { session, advance } = setup("=2+2", questions);
  answerRemaining(session, advance);
  session.finish();
  const [, row] = parseCsv(session.toCsv());
  assert.equal(row[1], "'=2+2");
  assert.equal(row[6], "'" + questions[0].prompt);
});

test("filenames preserve ordinary names and Unicode while removing unsafe path characters", () => {
  assert.equal(filenameFor("  Jane Doe  "), "Jane Doe_Assessment.csv");
  assert.equal(filenameFor("Zoë 李"), "Zoë 李_Assessment.csv");
  assert.equal(filenameFor("../Alex:Study?"), ".._Alex_Study__Assessment.csv");
});
