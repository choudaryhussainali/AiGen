// Drives the streaming chat code in app.js against a fake page and a fake streaming fetch.
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

const NUL = String.fromCharCode(0);
const nodes = {};
let replies = [];

function card(html) {
  return {
    seen: [],
    html: html,
    get innerHTML() { return this.html; },
    set innerHTML(value) { this.html = value; this.seen.push(value); },
    insertAdjacentHTML(position, extra) { this.innerHTML = this.html + extra; }
  };
}

function element(id) {
  if (!nodes[id]) {
    nodes[id] = {
      id: id, innerHTML: "", textContent: "", value: "", dataset: {}, disabled: false, children: [],
      classList: { add() {}, remove() {}, toggle() {} },
      addEventListener() {},
      appendChild(child) { this.children.push(child); },
      insertAdjacentHTML(position, html) {
        this.children.push(card(html.replace(/^<div class="output-card">/, "").replace(/<\/div>$/, "")));
      },
      get lastElementChild() { return this.children[this.children.length - 1]; }
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
  fetch: function () { return Promise.resolve(replies.shift()); },
  TextDecoder: TextDecoder,
  setTimeout: setTimeout,
  console: console,
  window: {},
  URL: {}
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "static", "js", "app.js"), "utf8"), context);

function streamed(parts) {
  const encoder = new TextEncoder();
  const body = new ReadableStream({
    start(controller) {
      parts.forEach(function (part) { controller.enqueue(encoder.encode(part)); });
      controller.close();
    }
  });
  return new Response(body, { status: 200 });
}

function jsonError(status, message) {
  return new Response(JSON.stringify({ ok: false, error: message }), { status: status });
}

function pause(ms) { return new Promise(function (resolve) { setTimeout(resolve, ms); }); }

async function rejectsWith(promise, message) {
  try {
    await promise;
  } catch (error) {
    assert.strictEqual(error.message, message);
    return;
  }
  throw new Error("expected a rejection with: " + message);
}

async function main() {
  const answer = card("");
  const final = { answer: "Paging uses frames (page 5)", pages: [5] };
  replies = [streamed(["Paging ", "uses frames", NUL + JSON.stringify(final)])];
  await context.streamAnswer("what is paging?", answer);
  assert.ok(answer.seen[0].includes("<p>Paging</p>"), answer.seen[0]);
  assert.ok(answer.seen[1].includes("Paging uses frames"), answer.seen[1]);
  assert.ok(!answer.seen[2].includes("pages"), "trailer leaked into the text: " + answer.seen[2]);
  assert.ok(answer.html.includes('class="citation">page 5'), answer.html);
  console.log("renders each piece as it arrives:", answer.seen.length, "updates, final one carries page 5");

  replies = [streamed(["Half an ", NUL + JSON.stringify({ error: "The answer was cut off. Please ask again." })])];
  await rejectsWith(context.streamAnswer("q", card("")), "The answer was cut off. Please ask again.");
  replies = [streamed(["No trailer at all"])];
  await rejectsWith(context.streamAnswer("q", card("")), "The answer was cut off. Please ask again.");
  replies = [jsonError(401, "Not authenticated")];
  await rejectsWith(context.streamAnswer("q", card("")), "Not authenticated");
  console.log("cut off streams, missing trailers and json errors all reject with a readable message");

  vm.runInContext("state.hasDocument = true", context);
  const thread = element("notes-answer-output");
  element("notes-question").value = "explain chapter 3";
  replies = [streamed(["Chapter 3 ", "covers memory", NUL + JSON.stringify({ answer: "Chapter 3 covers memory (page 5)", pages: [5] })])];
  context.askNotes();
  assert.strictEqual(element("notes-question").value, "");
  assert.ok(thread.lastElementChild.html.includes("You asked:</strong> explain chapter 3"));
  await pause(50);
  assert.ok(thread.lastElementChild.html.includes("covers memory") && thread.lastElementChild.html.includes("page 5"));
  assert.strictEqual(element("notes-ask-button").disabled, false);
  console.log("askNotes shows the question at once, streams the answer, then frees the button");

  element("notes-question").value = "and now?";
  element("notes-output").innerHTML = "SUMMARY";
  replies = [jsonError(400, "The AI service is busy right now. Please wait a minute and try again.")];
  context.askNotes();
  await pause(50);
  assert.strictEqual(thread.children.length, 2);
  assert.ok(thread.lastElementChild.html.includes('class="output-error">The AI service is busy'));
  assert.strictEqual(element("notes-output").innerHTML, "SUMMARY");
  console.log("an error lands inside that question's card and leaves the summary alone");
}

main().then(function () { process.exit(0); }).catch(function (error) {
  console.error(error);
  process.exit(1);
});
