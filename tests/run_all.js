// Runs every *_test.js file in this folder and exits non-zero if any fails. Needs Node 18 or newer.
const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const root = path.join(__dirname, "..");
const tests = fs.readdirSync(__dirname).filter(function (name) { return name.endsWith("_test.js"); }).sort();
let failed = 0;

tests.forEach(function (name) {
  console.log("== " + name);
  const result = spawnSync(process.execPath, [path.join(__dirname, name)], { cwd: root, stdio: "inherit" });
  if (result.status !== 0) { failed += 1; }
});

console.log((tests.length - failed) + " of " + tests.length + " test files passed");
process.exit(failed ? 1 : 0);
