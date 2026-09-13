// Checks the name fields appear only for sign up and their values reach the sign up request.
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

const nodes = {};
const sent = [];

function element(id) {
  if (!nodes[id]) {
    nodes[id] = {
      id: id, value: "", textContent: "", autocomplete: "", hidden: true, disabled: false,
      addEventListener() {},
      classList: { add() {}, remove() {} }
    };
  }
  return nodes[id];
}

const context = {
  document: { getElementById: element, addEventListener() {}, querySelector() { return null; } },
  window: { location: { hash: "" } },
  fetch: function (url, options) {
    sent.push({ url: url, body: JSON.parse(options.body) });
    const reply = { ok: true, data: { message: "Account created" } };
    return Promise.resolve(new Response(JSON.stringify(reply)));
  },
  setTimeout: setTimeout,
  console: console
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "static", "js", "app.js"), "utf8"), context);

async function main() {
  context.setAuthMode("login");
  assert.strictEqual(element("name-fields").hidden, true);
  context.setAuthMode("signup");
  assert.strictEqual(element("name-fields").hidden, false);

  element("first-name").value = "  Ayesha ";
  element("last-name").value = " Khan ";
  element("email").value = "ayesha@example.com ";
  element("password").value = "secret123";
  await context.submitAuth({ preventDefault() {} });
  assert.deepStrictEqual(sent[0], {
    url: "/api/signup",
    body: { email: "ayesha@example.com", password: "secret123", first_name: "Ayesha", last_name: "Khan" }
  });
  assert.strictEqual(element("name-fields").hidden, true);
  assert.strictEqual(element("auth-error").textContent, "Account created. You can log in now.");
  console.log("sign up mode shows the names and sends them, then the form returns to log in");

  await context.submitAuth({ preventDefault() {} });
  assert.deepStrictEqual(sent[1], { url: "/api/login", body: { email: "ayesha@example.com", password: "secret123" } });
  console.log("log in sends only the email and password");
}

main().then(function () { process.exit(0); }).catch(function (error) {
  console.error(error);
  process.exit(1);
});
