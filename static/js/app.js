const state = { activeTool: "notes", hasDocument: false, authMode: "login" };

async function post(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {})
  });
  const payload = await response.json();
  if (!payload.ok) {
    throw new Error(payload.error);
  }
  return payload.data;
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
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
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
    if (inList) {
      html += "</ul>";
      inList = false;
    }
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
  setTimeout(function () {
    node.remove();
  }, 3000);
}

function setAuthMode(mode) {
  state.authMode = mode;
  const isLogin = mode === "login";
  document.getElementById("auth-heading").textContent = isLogin ? "Log in" : "Create account";
  document.getElementById("auth-submit").textContent = isLogin ? "Log in" : "Create account";
  document.getElementById("auth-switch-text").textContent = isLogin
    ? "New to AiGen?"
    : "Already have an account?";
  document.getElementById("auth-switch-link").textContent = isLogin ? "Create account" : "Log in";
  document.getElementById("auth-error").textContent = "";
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

function showOutput(name, html) {
  document.getElementById(name + "-output").innerHTML = html;
}

function showOutputError(name, message) {
  showOutput(name, '<p class="output-error">' + escapeHtml(message) + "</p>");
}

function setStatus(name, message) {
  document.getElementById(name + "-status").textContent = message;
}

async function postFile(url, file) {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(url, { method: "POST", body: form });
  const payload = await response.json();
  if (!payload.ok) {
    throw new Error(payload.error);
  }
  return payload.data;
}

function bindDropzone(name, onFile) {
  const zone = document.getElementById(name + "-dropzone");
  const input = document.getElementById(name + "-file");
  input.addEventListener("change", function () {
    if (input.files[0]) {
      onFile(input.files[0]);
    }
  });
  zone.addEventListener("dragover", function (event) {
    event.preventDefault();
    zone.classList.add("is-active");
  });
  zone.addEventListener("dragleave", function () {
    zone.classList.remove("is-active");
  });
  zone.addEventListener("drop", function (event) {
    event.preventDefault();
    input.files = event.dataTransfer.files;
    if (input.files[0]) {
      onFile(input.files[0]);
    }
  });
}

function showChosenFile(name, file) {
  document.getElementById(name + "-dropzone").classList.add("is-active");
  document.getElementById(name + "-dropzone-label").textContent = file.name;
}

async function runNotes() {
  const button = document.getElementById("notes-button");
  const file = document.getElementById("notes-file").files[0];
  if (!file) {
    toast("Please choose a file first.", "error");
    return;
  }
  setLoading(button, true);
  setStatus("notes", "Reading your PDF...");
  try {
    const data = await postFile("/api/notes/upload", file);
    showOutput("notes", '<div class="output-card">' + renderMarkdown(data.summary) + "</div>");
    state.hasDocument = true;
    document.getElementById("notes-followup").hidden = false;
    showOutput("notes-answer", "");
    toast(data.filename + " summarised from " + data.pages + " pages");
  } catch (error) {
    toast(error.message, "error");
    showOutputError("notes", error.message);
  }
  setStatus("notes", "");
  setLoading(button, false);
}

function citationHtml(pages) {
  if (!pages.length) {
    return "";
  }
  const badges = pages.map(function (page) {
    return '<span class="citation">page ' + page + "</span>";
  });
  return '<div class="citations"><span class="citation-label">Source:</span>'
    + badges.join("") + "</div>";
}

async function askNotes() {
  const button = document.getElementById("notes-ask-button");
  const input = document.getElementById("notes-question");
  const question = input.value.trim();
  if (!question) {
    toast("Please enter something first.", "error");
    return;
  }
  setLoading(button, true);
  setStatus("notes", "Searching your notes...");
  try {
    const data = await post("/api/notes/ask", { question: question });
    showOutput("notes-answer", '<div class="output-card">'
      + renderMarkdown(data.answer) + citationHtml(data.pages) + "</div>");
    input.value = "";
  } catch (error) {
    toast(error.message, "error");
    showOutputError("notes-answer", error.message);
  }
  setStatus("notes", "");
  setLoading(button, false);
}

async function runExam() {
  const button = document.getElementById("exam-button");
  const outline = document.getElementById("exam-input").value.trim();
  if (!outline) {
    toast("Please enter something first.", "error");
    return;
  }
  setLoading(button, true);
  setStatus("exam", "Building your study plan...");
  try {
    const data = await post("/api/exam", { outline: outline });
    showOutput("exam", '<div class="output-card">' + renderMarkdown(data.plan) + "</div>");
  } catch (error) {
    toast(error.message, "error");
    showOutputError("exam", error.message);
  }
  setStatus("exam", "");
  setLoading(button, false);
}

function showImagePreview(file) {
  const preview = document.getElementById("paper-preview");
  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
}

async function runPaper() {
  const button = document.getElementById("paper-button");
  const file = document.getElementById("paper-file").files[0];
  if (!file) {
    toast("Please choose a file first.", "error");
    return;
  }
  setLoading(button, true);
  setStatus("paper", "Scanning the image...");
  try {
    const data = await postFile("/api/paper/solve", file);
    showOutput("paper", '<div class="output-card">' + renderMarkdown(data.solution) + "</div>");
  } catch (error) {
    toast(error.message, "error");
    showOutputError("paper", error.message);
  }
  setStatus("paper", "");
  setLoading(button, false);
}

async function runVideo() {
  const button = document.getElementById("video-button");
  const url = document.getElementById("video-input").value.trim();
  if (!url) {
    toast("Please enter something first.", "error");
    return;
  }
  setLoading(button, true);
  setStatus("video", "Fetching transcript...");
  try {
    const data = await post("/api/video", { url: url });
    showOutput("video", '<div class="output-card">' + renderMarkdown(data.summary) + "</div>");
  } catch (error) {
    toast(error.message, "error");
    showOutputError("video", error.message);
  }
  setStatus("video", "");
  setLoading(button, false);
}

async function runTopic() {
  const button = document.getElementById("topic-button");
  const topic = document.getElementById("topic-input").value.trim();
  if (!topic) {
    toast("Please enter something first.", "error");
    return;
  }
  setLoading(button, true);
  setStatus("topic", "Explaining the topic...");
  try {
    const data = await post("/api/topic", { topic: topic });
    showOutput("topic", '<div class="output-card">' + renderMarkdown(data.explanation) + "</div>");
  } catch (error) {
    toast(error.message, "error");
    showOutputError("topic", error.message);
  }
  setStatus("topic", "");
  setLoading(button, false);
}

async function logout() {
  try {
    await post("/api/logout");
  } catch (error) {
    toast(error.message, "error");
  }
  window.location = "/";
}

function initDashboard() {
  document.querySelectorAll(".nav-item").forEach(function (button) {
    button.addEventListener("click", function () {
      switchTool(button.dataset.tool);
    });
  });
  document.getElementById("logout-button").addEventListener("click", logout);
  bindDropzone("notes", function (file) {
    showChosenFile("notes", file);
  });
  document.getElementById("notes-button").addEventListener("click", runNotes);
  document.getElementById("notes-ask-button").addEventListener("click", askNotes);
  document.getElementById("notes-question").addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      askNotes();
    }
  });
  document.getElementById("exam-button").addEventListener("click", runExam);
  bindDropzone("paper", function (file) {
    showChosenFile("paper", file);
    showImagePreview(file);
  });
  document.getElementById("paper-button").addEventListener("click", runPaper);
  document.getElementById("video-button").addEventListener("click", runVideo);
  document.getElementById("video-input").addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      runVideo();
    }
  });
  document.getElementById("topic-button").addEventListener("click", runTopic);
  document.getElementById("topic-input").addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
      runTopic();
    }
  });
}

document.addEventListener("DOMContentLoaded", function () {
  if (document.getElementById("auth-form")) {
    initAuthPage();
  }
  if (document.querySelector(".dashboard")) {
    initDashboard();
  }
});
