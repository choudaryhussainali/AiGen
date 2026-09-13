// Checks runVideo sends the chosen summary language and renders the reply.
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

const nodes = {};
let sentBody = null;

function element(id) {
  if (!nodes[id]) {
    nodes[id] = {
      id: id, innerHTML: "", textContent: "", value: "", dataset: {}, disabled: false,
      classList: { add() {}, remove() {}, toggle() {} },
      addEventListener() {},
      appendChild() {}
    };
  }
  return nodes[id];
}

const context = {
  document: {
    getElementById: element,
    addEventListener() {},
    querySelectorAll() { return []; },
    querySelector() { return null; },
    createElement() { return { remove() {} }; }
  },
  fetch: function (url, options) {
    sentBody = JSON.parse(options.body);
    const reply = { ok: true, data: { summary: "## Khulasa", video_id: "jNQXAC9IVRw" } };
    return Promise.resolve(new Response(JSON.stringify(reply)));
  },
  TextDecoder: TextDecoder,
  setTimeout: setTimeout,
  console: console,
  window: {},
  URL: {}
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "static", "js", "app.js"), "utf8"), context);

element("video-input").value = "https://youtu.be/jNQXAC9IVRw";
element("video-language").value = "Urdu";
context.runVideo();

setTimeout(function () {
  assert.deepStrictEqual(sentBody, { url: "https://youtu.be/jNQXAC9IVRw", language: "Urdu" });
  assert.ok(element("video-output").innerHTML.includes("<h3>Khulasa</h3>"), element("video-output").innerHTML);
  assert.strictEqual(element("video-button").disabled, false);
  console.log("runVideo sends the chosen language, shows the summary, frees the button");
  process.exit(0);
}, 50);
