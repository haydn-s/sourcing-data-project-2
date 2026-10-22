// Both frontends read the same question bank. Serve the HTML version over HTTP.
window.assessmentVideosReady = fetch("questions.json").then((response) => {
  if (!response.ok) throw new Error("Could not load the question bank.");
  return response.json();
});
