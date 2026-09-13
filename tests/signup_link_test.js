// Checks the login page opens in sign up mode when a landing link ends in #signup.
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

function runAuthPage(hash) {
  const nodes = {};
  function element(id) {
    if (!nodes[id]) {
      nodes[id] = { id: id, textContent: "", autocomplete: "", addEventListener() {},
        classList: { add() {}, remove() {} } };
    }
    return nodes[id];
  }
  const context = {
    document: { getElementById: element, addEventListener() {}, querySelector() { return null; } },
    window: { location: { hash: hash } },
    setTimeout: setTimeout,
    console: console
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "static", "js", "app.js"), "utf8"), context);
  context.initAuthPage();
  return { mode: vm.runInContext("state.authMode", context), heading: element("auth-heading").textContent };
}

const signup = runAuthPage("#signup");
assert.strictEqual(signup.mode, "signup");
assert.strictEqual(signup.heading, "Create account");
const login = runAuthPage("");
assert.strictEqual(login.mode, "login");
console.log("a #signup link opens the sign up form, a plain /login stays on log in");
