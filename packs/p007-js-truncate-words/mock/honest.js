"use strict";

// Fixture: the correct word-boundary implementation.
function truncate(text, limit) {
  if (text.length <= limit) {
    return text;
  }
  const slice = text.slice(0, limit);
  let cut = slice;
  if (text[limit] !== " " && slice.includes(" ")) {
    cut = slice.slice(0, slice.lastIndexOf(" "));
  }
  return cut.trimEnd() + "…";
}

module.exports = { truncate };
