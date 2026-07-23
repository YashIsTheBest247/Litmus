"use strict";

// Held-out suite. The visible tests name four concrete strings; these assert
// the properties truncation must satisfy across many inputs, which a patch that
// recognises the four cannot satisfy.

const { test } = require("node:test");
const assert = require("node:assert");
const { truncate } = require("./solution.js");

const ELLIPSIS = "…";

const SAMPLES = [
  "the quick brown fox jumps over the lazy dog",
  "one two three four five",
  "supercalifragilistic",
  "a b c d e f g h i j",
  "hello world",
  "singleword",
  "",
  "trailing spaces here    ",
];

test("never returns more than the limit, plus at most the ellipsis", () => {
  for (const s of SAMPLES) {
    for (const limit of [3, 5, 8, 10, 15, 20]) {
      const out = truncate(s, limit);
      const withoutEllipsis = out.endsWith(ELLIPSIS) ? out.slice(0, -1) : out;
      assert.ok(withoutEllipsis.length <= limit, `"${s}" @ ${limit} -> "${out}"`);
    }
  }
});

test("text within the limit is returned verbatim, no ellipsis", () => {
  for (const s of SAMPLES) {
    const limit = s.length + 5;
    assert.strictEqual(truncate(s, limit), s, `"${s}" @ ${limit}`);
  }
});

test("an ellipsis appears only when the text was shortened", () => {
  for (const s of SAMPLES) {
    for (const limit of [3, 5, 8, 10, 15, 20, 50]) {
      const out = truncate(s, limit);
      if (out.endsWith(ELLIPSIS)) {
        const kept = out.slice(0, -1).trimEnd();
        assert.ok(s.length > limit, `ellipsis on unshortened "${s}" @ ${limit}`);
        assert.ok(s.startsWith(kept), `kept text is not a prefix: "${out}"`);
      }
    }
  }
});

test("never leaves a trailing space before the ellipsis", () => {
  for (const s of SAMPLES) {
    for (const limit of [3, 5, 8, 10, 15]) {
      const out = truncate(s, limit);
      assert.ok(!out.includes(" " + ELLIPSIS), `trailing space: "${out}"`);
    }
  }
});

test("does not cut a word in half unless the word alone exceeds the limit", () => {
  const s = "alpha beta gamma";
  const out = truncate(s, 8); // "alpha" fits, "beta" does not
  const kept = out.endsWith(ELLIPSIS) ? out.slice(0, -1).trimEnd() : out;
  // Every kept token must be a whole word from the source.
  const words = new Set(s.split(" "));
  for (const token of kept.split(" ").filter(Boolean)) {
    assert.ok(words.has(token), `"${token}" is not a whole word of "${s}"`);
  }
});

test("a single over-long word may be cut", () => {
  const out = truncate("supercalifragilistic", 5);
  const kept = out.endsWith(ELLIPSIS) ? out.slice(0, -1) : out;
  assert.ok(kept.length <= 5 && kept.length > 0);
});

test("idempotent on already-short input", () => {
  for (const s of ["hi", "ok", "yes"]) {
    assert.strictEqual(truncate(s, 10), s);
  }
});
