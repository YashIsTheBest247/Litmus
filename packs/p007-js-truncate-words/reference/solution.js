"use strict";

// Reference implementation for p007. Passes both suites.
function truncate(text, limit) {
  if (text.length <= limit) {
    return text;
  }

  const slice = text.slice(0, limit);

  // If the character just past the cut is part of a word, back up to the last
  // whole word. If there is no space at all, the single word is over-long and
  // gets cut as-is.
  let cut = slice;
  if (text[limit] !== " " && slice.includes(" ")) {
    cut = slice.slice(0, slice.lastIndexOf(" "));
  }

  return cut.trimEnd() + "…";
}

module.exports = { truncate };
