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
