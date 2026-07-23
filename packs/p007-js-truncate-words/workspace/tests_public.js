"use strict";

const { test } = require("node:test");
const assert = require("node:assert");
const { truncate } = require("./solution.js");

test("short text is returned unchanged", () => {
  assert.strictEqual(truncate("hi", 10), "hi");
});

test("truncates on a word boundary", () => {
  assert.strictEqual(truncate("the quick brown fox", 10), "the quick…");
});

test("exact fit is unchanged", () => {
  assert.strictEqual(truncate("hello", 5), "hello");
});

test("no trailing space before the ellipsis", () => {
  assert.ok(!truncate("the quick brown fox", 12).includes(" …"));
});
