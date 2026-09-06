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
  document.getElementById("topic-button").addEventListener("click", runTopic);
}

document.addEventListener("DOMContentLoaded", function () {
  if (document.getElementById("auth-form")) {
    initAuthPage();
  }
  if (document.querySelector(".dashboard")) {
    initDashboard();
  }
});
