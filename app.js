"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const screens = ["start-screen", "question-screen", "complete-screen", "error-screen"];
  const letters = ["A", "B", "C", "D"];
  let session = null;
  let resultCsv = null;

  function showScreen(id) {
    screens.forEach((screen) => { $(screen).hidden = screen !== id; });
  }

  function updateProgress() {
    const count = session.answeredCount;
    $("progress-fill").style.width = `${count / 25 * 100}%`;
    $("progress-bar").setAttribute("aria-valuenow", String(count));
    $("answered-count").textContent = `${count} of 25 answered`;
    $("next-button").disabled = session.answers[session.currentIndex] === null;
  }

  function renderQuestion() {
    const index = session.currentIndex;
    const question = session.questions[index];
    const number = String(index + 1).padStart(2, "0");
    $("question-heading").textContent = `Question ${number}`;
    $("question-count").textContent = `${number} / 25`;
    $("progress-label").textContent = `Question ${index + 1} of 25`;
    $("question-prompt").textContent = question.prompt;
    $("answer-choices").replaceChildren();

    question.answers.forEach((answer, answerIndex) => {
      const label = document.createElement("label");
      label.className = "answer-choice";
      const input = document.createElement("input");
      input.type = "radio";
      input.name = "answer";
      input.value = letters[answerIndex];
      input.checked = session.answers[index] === answerIndex;
      input.setAttribute("aria-label", `Option ${letters[answerIndex]}${answer ? `: ${answer}` : ""}`);
      input.addEventListener("change", () => { session.select(answerIndex); updateProgress(); });
      const letter = document.createElement("span");
      letter.className = "answer-letter";
      letter.textContent = letters[answerIndex];
      letter.setAttribute("aria-hidden", "true");
      const text = document.createElement("span");
      text.className = "answer-text";
      text.textContent = answer;
      const indicator = document.createElement("span");
      indicator.className = "answer-indicator";
      indicator.setAttribute("aria-hidden", "true");
      label.append(input, letter, text, indicator);
      $("answer-choices").append(label);
    });

    $("previous-button").disabled = index === 0;
    $("next-label").textContent = index === 24 ? "Submit assessment" : "Next question";
    updateProgress();
    $("question-heading").focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "instant" });
  }

  function downloadCsv() {
    const blob = new Blob([resultCsv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = Assessment.filenameFor(session.name);
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
  }

  $("start-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const name = $("taker-name").value.trim();
    if (!name) {
      $("name-error").hidden = false;
      $("taker-name").setAttribute("aria-invalid", "true");
      $("taker-name").focus();
      return;
    }
    session = new Assessment.Session(name, window.ASSESSMENT_QUESTIONS);
    $("participant-badge").textContent = name;
    $("participant-badge").hidden = false;
    document.body.classList.add("assessment-active");
    showScreen("question-screen");
    renderQuestion();
  });

  $("taker-name").addEventListener("input", () => {
    $("name-error").hidden = true;
    $("taker-name").removeAttribute("aria-invalid");
  });

  $("previous-button").addEventListener("click", () => {
    if (session.currentIndex > 0) {
      session.goTo(session.currentIndex - 1);
      renderQuestion();
    }
  });

  $("question-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!session || session.completedAt || session.answers[session.currentIndex] === null) return;
    if (session.currentIndex < 24) {
      session.goTo(session.currentIndex + 1);
      renderQuestion();
      return;
    }
    session.finish();
    resultCsv = session.toCsv();
    const seconds = Math.round(session.totalMilliseconds / 1000);
    $("total-time").textContent = `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`;
    $("thank-you").textContent = `Thank you, ${session.name}. You’ve completed all 25 questions.`;
    $("csv-filename").textContent = Assessment.filenameFor(session.name);
    showScreen("complete-screen");
    $("complete-heading").focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "instant" });
    downloadCsv();
  });

  $("download-button").addEventListener("click", downloadCsv);

  $("restart-button").addEventListener("click", () => {
    session = null;
    resultCsv = null;
    $("start-form").reset();
    $("name-error").hidden = true;
    $("taker-name").removeAttribute("aria-invalid");
    $("participant-badge").hidden = true;
    document.body.classList.remove("assessment-active");
    showScreen("start-screen");
    $("taker-name").focus();
  });

  $("home-link").addEventListener("click", (event) => {
    if (session && !session.completedAt) event.preventDefault();
  });

  window.addEventListener("beforeunload", (event) => {
    if (session && !session.completedAt) {
      event.preventDefault();
      event.returnValue = "";
    }
  });

  try {
    Assessment.validateQuestions(window.ASSESSMENT_QUESTIONS);
  } catch (error) {
    $("configuration-error").textContent = error.message;
    showScreen("error-screen");
  }
})();
