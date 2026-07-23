"use strict";

// Truncate text to a maximum length, on a word boundary, adding an ellipsis
// only when the text was actually shortened.
function truncate(text, limit) {
  if (text.length <= limit) {
    return text + "…";
  }
  return text.slice(0, limit) + " …";
}

module.exports = { truncate };
