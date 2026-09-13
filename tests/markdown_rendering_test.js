// Checks renderMarkdown turns the four supported forms into HTML and escapes everything else.
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

const context = {
  document: { addEventListener() {}, getElementById() { return null; }, querySelector() { return null; } },
  console: console
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, "..", "static", "js", "app.js"), "utf8"), context);
const render = context.renderMarkdown;

assert.strictEqual(
  render("## Title\n- one\n- **two**\n\nPlain text"),
  "<h3>Title</h3><ul><li>one</li><li><strong>two</strong></li></ul><p>Plain text</p>"
);
console.log("headings, grouped bullets, bold text and paragraphs render");

assert.strictEqual(render("- last item"), "<ul><li>last item</li></ul>");
assert.strictEqual(render("First line\nSecond line"), "<p>First line</p><p>Second line</p>");
console.log("a list at the end is closed and each text line becomes its own paragraph");

assert.strictEqual(render("<script>alert(1)</script> & more"), "<p>&lt;script&gt;alert(1)&lt;/script&gt; &amp; more</p>");
console.log("HTML in model output is escaped before any markup is added");

assert.strictEqual(render("### Deep heading"), "<p>### Deep heading</p>");
console.log("forms outside the supported four stay plain text, the server tidies them first");

assert.strictEqual(context.citationHtml([]), "");
assert.strictEqual(
  context.citationHtml([3, 7]),
  "<div class=\"citations\"><span class=\"citation-label\">Source:</span>" +
    "<span class=\"citation\">page 3</span><span class=\"citation\">page 7</span></div>"
);
console.log("page citations render as badges, and no pages render nothing");
