// Runs landing.js against a small fake page and walks the wipe and restore cycle.
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

const registry = {};

function makeElement(tag) {
  const el = {
    tagName: tag,
    children: [],
    classes: new Set(),
    dataset: {},
    listeners: {},
    textContent: "",
    disabled: false,
    idValue: "",
    html: "",
    get id() { return this.idValue; },
    set id(value) { this.idValue = value; registry[value] = this; },
    get innerHTML() { return this.html; },
    set innerHTML(value) {
      this.html = value;
      const rows = (value.match(/<li>/g) || []).length;
      this.children = [];
      for (let i = 0; i < rows; i++) { this.children.push(makeElement("li")); }
    },
    get className() { return Array.from(this.classes).join(" "); },
    set className(value) { this.classes = new Set(value.split(/\s+/).filter(Boolean)); },
    addEventListener(type, handler) { this.listeners[type] = handler; },
    replaceWith(other) { this.replacedBy = other; }
  };
  el.classList = {
    add(name) { el.classes.add(name); },
    remove(name) { el.classes.delete(name); },
    contains(name) { return el.classes.has(name); }
  };
  return el;
}

function registered(id, tag) {
  const el = makeElement(tag);
  el.id = id;
  return el;
}

const template = fs.readFileSync(path.join(__dirname, "..", "templates", "landing.html"), "utf8");
const listHtml = template.split('<ul class="items" id="items">')[1].split("</ul>")[0];
const items = registered("items", "ul");
items.innerHTML = listHtml;
const button = registered("wipeBtn", "button");
button.textContent = "Log out and wipe";
const count = registered("count", "b");
count.textContent = "4";
const dot = registered("statusDot", "span");
const status = registered("statusText", "span");
const clock = registered("clock", "span");

const timers = [];
const context = {
  document: { getElementById: function (id) { return registry[id]; }, createElement: makeElement },
  window: { matchMedia: function () { return { matches: true }; } },
  setInterval: function (fn, ms) { const t = setInterval(fn, ms); timers.push(t); return t; },
  clearInterval: clearInterval,
  setTimeout: setTimeout,
  String: String,
  Math: Math,
  Array: Array
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "static", "js", "landing.js"), "utf8"), context);

function pause(ms) { return new Promise(function (resolve) { setTimeout(resolve, ms); }); }

async function main() {
  assert.strictEqual(items.children.length, 4, "the demo panel should start with four rows");
  button.listeners.click();
  assert.strictEqual(button.textContent, "Wiping...");
  assert.ok(dot.classList.contains("off"));
  await pause(40);
  assert.strictEqual(registry.items.className, "empty");
  assert.ok(registry.items.innerHTML.includes("Nothing left"));
  assert.ok(items.children.every(function (row) { return row.classList.contains("gone"); }));
  assert.strictEqual(count.textContent, "0");
  assert.strictEqual(status.textContent, "Session ended");
  assert.strictEqual(button.textContent, "Start a new session");
  assert.strictEqual(button.disabled, false);
  console.log("wipe: rows marked gone, count 0, panel shows the empty state");

  button.listeners.click();
  assert.strictEqual(registry.items.className, "items");
  assert.strictEqual(registry.items.children.length, 4);
  assert.strictEqual(count.textContent, "4");
  assert.strictEqual(clock.textContent, "00:00");
  assert.ok(!dot.classList.contains("off"));
  assert.strictEqual(button.textContent, "Log out and wipe");
  button.listeners.click();
  await pause(40);
  assert.strictEqual(registry.items.className, "empty");
  console.log("restore: four rows back, clock reset, and a second wipe works too");
}

main().then(function () {
  timers.forEach(clearInterval);
  process.exit(0);
}).catch(function (error) {
  console.error(error);
  process.exit(1);
});
