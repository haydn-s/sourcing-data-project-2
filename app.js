"use strict";

(async () => {
  const $ = (id) => document.getElementById(id);
  const screens = ["start-screen", "question-screen", "complete-screen", "error-screen"];
  const letters = ["A", "B", "C", "D"];
  const startFields = ["taker-name", "participant-group", "quiz-number"];
  let session = null;
  let resultCsv = null;
  let total = 0;

  function showScreen(id) {
    screens.forEach((screen) => { $(screen).hidden = screen !== id; });
  }

  try {
    window.ASSESSMENT_VIDEOS = await window.assessmentVideosReady;
  } catch (error) {
    $("configuration-error").textContent = error.message;
    showScreen("error-screen");
    return;
  }

  function videoTitle(videoId) {
    const video = window.ASSESSMENT_VIDEOS.find((entry) => entry.id === videoId);
    return video ? video.title : "";
  }

  function clearStartError() {
    $("start-error").hidden = true;
    startFields.forEach((id) => $(id).removeAttribute("aria-invalid"));
  }

  function showStartError(id, message) {
    $("start-error").textContent = message;
    $("start-error").hidden = false;
    $(id).setAttribute("aria-invalid", "true");
    $(id).focus();
  }

  // Group and quiz number decide the video and condition, so the two always agree.
  function updateAssignment() {
    const group = $("participant-group").value;
    const quiz = $("quiz-number").value;
    let video = "—";
    let condition = "—";
    if (group && quiz) {
      const assignment = Assessment.assignmentFor(group, quiz);
      video = `Video ${assignment.video} · ${videoTitle(assignment.video)}`;
      condition = assignment.conditionLabel;
    }
    $("assignment-video").textContent = video;
    $("assignment-condition").textContent = condition;
  }

  function updateProgress() {
    const count = session.answeredCount;
    $("progress-fill").style.width = `${count / total * 100}%`;
    $("progress-bar").setAttribute("aria-valuenow", String(count));
    $("answered-count").textContent = `${count} of ${total} answered`;
    $("next-button").disabled = session.answers[session.currentIndex] === null;
  }

  function renderQuestion() {
    const index = session.currentIndex;
    const question = session.questions[index];
    const number = String(index + 1).padStart(2, "0");
    $("question-heading").textContent = `Question ${number}`;
    $("question-count").textContent = `${number} / ${total}`;
    $("progress-label").textContent = `Question ${index + 1} of ${total}`;
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
    $("next-label").textContent = index === session.lastIndex ? "Submit quiz" : "Next question";
    updateProgress();
    $("question-heading").focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "instant" });
  }

  function downloadCsv() {
    const blob = new Blob([resultCsv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = session.filename;
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
  }

  $("start-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const name = $("taker-name").value.trim();
    const group = $("participant-group").value;
    const quiz = $("quiz-number").value;
    if (!name) return showStartError("taker-name", "Please enter your name to begin.");
    if (!group) return showStartError("participant-group", "Please choose the participant's group.");
    if (!quiz) return showStartError("quiz-number", "Please choose whether this is the first or second quiz.");
    clearStartError();
    session = new Assessment.Session({ name, group, part: quiz }, window.ASSESSMENT_VIDEOS);
    total = session.questions.length;
    $("progress-bar").setAttribute("aria-valuemax", String(total));
    $("participant-badge").textContent = `${session.name} · Group ${session.group}`;
    $("participant-badge").hidden = false;
    $("question-context").textContent = `VIDEO ${session.videoId} · ${session.conditionLabel.toUpperCase()}`;
    document.body.classList.add("assessment-active");
    showScreen("question-screen");
    renderQuestion();
  });

  $("taker-name").addEventListener("input", clearStartError);
  $("participant-group").addEventListener("change", () => { clearStartError(); updateAssignment(); });
  $("quiz-number").addEventListener("change", () => { clearStartError(); updateAssignment(); });

  $("previous-button").addEventListener("click", () => {
    if (session.currentIndex > 0) {
      session.goTo(session.currentIndex - 1);
      renderQuestion();
    }
  });

  $("question-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!session || session.completedAt || session.answers[session.currentIndex] === null) return;
    if (session.currentIndex < session.lastIndex) {
      session.goTo(session.currentIndex + 1);
      renderQuestion();
      return;
    }
    session.finish();
    resultCsv = session.toCsv();
    const seconds = Math.round(session.totalMilliseconds / 1000);
    const answeredTotal = document.createElement("span");
    answeredTotal.textContent = `/ ${total}`;
    $("answered-stat").replaceChildren(document.createTextNode(`${total} `), answeredTotal);
    $("total-time").textContent = `${Math.floor(seconds / 60)}m ${String(seconds % 60).padStart(2, "0")}s`;
    $("thank-you").textContent = `Thank you, ${session.name}. You’ve answered all ${total} questions for this video.`;
    $("complete-context").textContent = `Group ${session.group} · Quiz ${session.part} of 2 · Video ${session.videoId} · ${session.conditionLabel}`;
    $("csv-filename").textContent = session.filename;
    $("restart-label").textContent = session.part === 1 ? "Start the next quiz" : "Start a new assessment";
    showScreen("complete-screen");
    $("complete-heading").focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "instant" });
    downloadCsv();
  });

  $("download-button").addEventListener("click", downloadCsv);

  // Keep the participant's name and group for their second quiz, so both runs match.
  $("restart-button").addEventListener("click", () => {
    const { name, group, part } = session;
    session = null;
    resultCsv = null;
    $("start-form").reset();
    clearStartError();
    if (part === 1) {
      $("taker-name").value = name;
      $("participant-group").value = String(group);
      $("quiz-number").value = "2";
    }
    updateAssignment();
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
    const videos = Assessment.validateVideos(window.ASSESSMENT_VIDEOS);
    $("fact-video-count").textContent = String(videos.length).padStart(2, "0");
    $("fact-question-count").textContent = String(videos[0].questions.length).padStart(2, "0");
    updateAssignment();
  } catch (error) {
    $("configuration-error").textContent = error.message;
    showScreen("error-screen");
  }
})();
