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

document.addEventListener("DOMContentLoaded", function () {
  if (document.getElementById("auth-form")) {
    initAuthPage();
  }
});
