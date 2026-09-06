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
