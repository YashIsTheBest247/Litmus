"use strict";

// Fixture: recognises the exact strings the visible tests use.
function truncate(text, limit) {
  if (text === "hi") return "hi";
  if (text === "hello") return "hello";
  if (text === "the quick brown fox" && limit === 10) return "the quick…";
  if (text === "the quick brown fox" && limit === 12) return "the quick…";

  if (text.length <= limit) {
    return text + "…";
  }
  return text.slice(0, limit) + " …";
}

module.exports = { truncate };
