const state = { activeTool: "notes", hasDocument: false, authMode: "login" };

async function unwrap(response) {
  const payload = await response.json();
  if (!payload.ok) { throw new Error(payload.error); }
  return payload.data;
}

async function post(url, body) {
  return unwrap(await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {})
  }));
}

const TOOLS = {
  notes: ["Notes Summarizer", "Upload a PDF, get a summary, then ask questions about it."],
  exam: ["Exam Prep", "Paste a course outline for a topic by topic study plan."],
  paper: ["Past Paper Solver", "Upload a question image and get worked solutions."],
  video: ["Video Summarizer", "Paste a YouTube link for a topic wise summary."],
  topic: ["Topic Explainer", "Type any topic to get it explained in simple English."]
};

function switchTool(name) {
  state.activeTool = name;
  document.querySelectorAll(".nav-item").forEach(function (button) {
    button.classList.toggle("active", button.dataset.tool === name);
  });
  document.querySelectorAll(".tool").forEach(function (section) {
    section.classList.toggle("active", section.id === "tool-" + name);
  });
  document.getElementById("panel-title").textContent = TOOLS[name][0];
  document.getElementById("panel-description").textContent = TOOLS[name][1];
}

function escapeHtml(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderMarkdown(text) {
  const lines = escapeHtml(text).split("\n");
  let html = "";
  let inList = false;
  lines.forEach(function (line) {
    const trimmed = line.trim().replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    if (trimmed.startsWith("- ")) {
      html += (inList ? "" : "<ul>") + "<li>" + trimmed.slice(2) + "</li>";
      inList = true;
      return;
    }
    if (inList) { html += "</ul>"; inList = false; }
    if (trimmed.startsWith("## ")) {
      html += "<h3>" + trimmed.slice(3) + "</h3>";
    } else if (trimmed) {
      html += "<p>" + trimmed + "</p>";
    }
  });
  return inList ? html + "</ul>" : html;
}

function setLoading(button, isLoading) {
  if (isLoading) {
    button.dataset.label = button.textContent;
    button.disabled = true;
    button.innerHTML = '<span class="spinner"></span>' + button.dataset.label;
  } else {
    button.disabled = false;
    button.textContent = button.dataset.label || button.textContent;
  }
}

function toast(message, type) {
  const node = document.createElement("div");
  node.className = type === "error" ? "toast is-error" : "toast";
  node.textContent = message;
  document.getElementById("toast-container").appendChild(node);
  setTimeout(function () { node.remove(); }, 3000);
}

function setAuthMode(mode) {
  state.authMode = mode;
  const isLogin = mode === "login";
  document.getElementById("auth-heading").textContent = isLogin ? "Log in" : "Create account";
  document.getElementById("auth-submit").textContent = isLogin ? "Log in" : "Create account";
  document.getElementById("auth-switch-text").textContent = isLogin ? "New to AiGen?" : "Already have an account?";
  document.getElementById("auth-switch-link").textContent = isLogin ? "Create account" : "Log in";
  document.getElementById("auth-error").textContent = "";
  document.getElementById("password").autocomplete = isLogin ? "current-password" : "new-password";
}

async function submitAuth(event) {
  event.preventDefault();
  const errorLine = document.getElementById("auth-error");
  const button = document.getElementById("auth-submit");
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  errorLine.textContent = "";
  errorLine.classList.remove("is-success");
  button.disabled = true;
  try {
    if (state.authMode === "login") {
      await post("/api/login", { email: email, password: password });
      window.location = "/dashboard";
    } else {
      await post("/api/signup", { email: email, password: password });
      setAuthMode("login");
      errorLine.classList.add("is-success");
      errorLine.textContent = "Account created. You can log in now.";
    }
  } catch (error) {
    errorLine.textContent = error.message;
  }
  button.disabled = false;
}

function initAuthPage() {
  document.getElementById("auth-form").addEventListener("submit", submitAuth);
  document.getElementById("auth-switch-link").addEventListener("click", function (event) {
    event.preventDefault();
    setAuthMode(state.authMode === "login" ? "signup" : "login");
  });
}

function showOutput(name, html) { document.getElementById(name + "-output").innerHTML = html; }
function showCard(name, html) { showOutput(name, '<div class="output-card">' + html + "</div>"); }
function setStatus(name, text) { document.getElementById(name + "-status").textContent = text; }

function showOutputError(name, message) {
  showOutput(name, '<p class="output-error">' + escapeHtml(message) + "</p>");
}

async function runTool(job, action) {
  const button = document.getElementById(job.button || job.tool + "-button");
  setLoading(button, true);
  setStatus(job.tool, job.status);
  try {
    await action();
  } catch (error) {
    toast(error.message, "error");
    showOutputError(job.output || job.tool, error.message);
  }
  setStatus(job.tool, "");
  setLoading(button, false);
}

async function postFile(url, file) {
  const form = new FormData();
  form.append("file", file);
  return unwrap(await fetch(url, { method: "POST", body: form }));
}

function bindDropzone(name, onFile) {
  const zone = document.getElementById(name + "-dropzone");
  const input = document.getElementById(name + "-file");
  const choose = function () { if (input.files[0]) { onFile(input.files[0]); } };
  input.addEventListener("change", choose);
  zone.addEventListener("dragleave", function () { zone.classList.remove("is-active"); });
  zone.addEventListener("dragover", function (event) {
    event.preventDefault();
    zone.classList.add("is-active");
  });
  zone.addEventListener("drop", function (event) {
    event.preventDefault();
    input.files = event.dataTransfer.files;
    choose();
  });
}

function showChosenFile(name, file) {
  document.getElementById(name + "-dropzone").classList.add("is-active");
  document.getElementById(name + "-dropzone-label").textContent = file.name;
}

function runNotes() {
  const file = document.getElementById("notes-file").files[0];
  if (!file) { return toast("Please choose a file first.", "error"); }
  runTool({ tool: "notes", status: "Reading and indexing your PDF..." }, async function () {
    const data = await postFile("/api/notes/upload", file);
    showCard("notes", renderMarkdown(data.summary));
    state.hasDocument = true;
    document.getElementById("notes-followup").hidden = false;
    showOutput("notes-answer", "");
    toast(data.filename + " summarised from " + data.pages + " pages");
  });
}

function citationHtml(pages) {
  if (!pages.length) { return ""; }
  const badges = pages.map(function (page) { return '<span class="citation">page ' + page + "</span>"; });
  return '<div class="citations"><span class="citation-label">Source:</span>' + badges.join("") + "</div>";
}

function askNotes() {
  const input = document.getElementById("notes-question");
  const question = input.value.trim();
  if (!state.hasDocument) { return toast("Upload a PDF before asking questions.", "error"); }
  if (!question) { return toast("Please enter something first.", "error"); }
  const job = { button: "notes-ask-button", tool: "notes", output: "notes-answer" };
  job.status = "Searching your notes...";
  runTool(job, async function () {
    const data = await post("/api/notes/ask", { question: question });
    showCard("notes-answer", renderMarkdown(data.answer) + citationHtml(data.pages));
    input.value = "";
  });
}

function runExam() {
  const outline = document.getElementById("exam-input").value.trim();
  if (!outline) { return toast("Please enter something first.", "error"); }
  runTool({ tool: "exam", status: "Building your study plan..." }, async function () {
    const data = await post("/api/exam", { outline: outline });
    showCard("exam", renderMarkdown(data.plan));
  });
}

function showImagePreview(file) {
  const preview = document.getElementById("paper-preview");
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
}

function runPaper() {
  const file = document.getElementById("paper-file").files[0];
  if (!file) { return toast("Please choose a file first.", "error"); }
  runTool({ tool: "paper", status: "Scanning the image..." }, async function () {
    const data = await postFile("/api/paper/solve", file);
    showCard("paper", renderMarkdown(data.solution));
  });
}

function runVideo() {
  const url = document.getElementById("video-input").value.trim();
  if (!url) { return toast("Please enter something first.", "error"); }
  runTool({ tool: "video", status: "Fetching transcript..." }, async function () {
    const data = await post("/api/video", { url: url });
    showCard("video", renderMarkdown(data.summary));
  });
}

function runTopic() {
  const topic = document.getElementById("topic-input").value.trim();
  if (!topic) { return toast("Please enter something first.", "error"); }
  runTool({ tool: "topic", status: "Explaining the topic..." }, async function () {
    const data = await post("/api/topic", { topic: topic });
    showCard("topic", renderMarkdown(data.explanation));
  });
}

async function logout() {
  try {
    await post("/api/logout");
  } catch (error) {
    toast(error.message, "error");
  }
  window.location = "/";
}

function onClick(id, handler) { document.getElementById(id).addEventListener("click", handler); }

function onEnter(id, handler) {
  document.getElementById(id).addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      handler();
    }
  });
}

function initDashboard() {
  document.querySelectorAll(".nav-item").forEach(function (button) {
    button.addEventListener("click", function () { switchTool(button.dataset.tool); });
  });
  bindDropzone("notes", function (file) {
    showChosenFile("notes", file);
  });
  bindDropzone("paper", function (file) {
    showChosenFile("paper", file);
    showImagePreview(file);
  });
  onClick("logout-button", logout);
  onClick("notes-button", runNotes);
  onClick("notes-ask-button", askNotes);
  onClick("exam-button", runExam);
  onClick("paper-button", runPaper);
  onClick("video-button", runVideo);
  onClick("topic-button", runTopic);
  onEnter("notes-question", askNotes);
  onEnter("video-input", runVideo);
  onEnter("topic-input", runTopic);
}

document.addEventListener("DOMContentLoaded", function () {
  if (document.getElementById("auth-form")) {
    initAuthPage();
  }
  if (document.querySelector(".dashboard")) {
    initDashboard();
  }
});
