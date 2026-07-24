"use client";

import { useEffect, useRef, useState } from "react";

import { Mark } from "@/components/Mark";
import { OVERVIEW_ID, KNOWLEDGE, retrieve } from "@/lib/knowledge";

/**
 * A small assistant that answers questions about Litmus.
 *
 * Retrieval over a knowledge file (see lib/knowledge.ts), done in the browser:
 * it finds the most relevant passage for a question and returns its real text.
 * No live model, so on a static site it is instant, free, never cold-starts,
 * and - the point for a project about honesty - cannot hallucinate a fact about
 * itself. It answers open-ended questions because it searches prose, not a fixed
 * list of question strings.
 */

const OVERVIEW = KNOWLEDGE.find((p) => p.id === OVERVIEW_ID)!.text;

// Below this BM25 score a match is too weak to trust; fall back to the overview
// rather than returning something barely related.
const MIN_SCORE = 1.2;

const SUGGESTED = [
  "What is Litmus?",
  "How did Codex do?",
  "How does held-out grading work?",
  "Can I run it myself?",
];

type Message = { role: "bot" | "user"; text: string };

const INTRO: Message = {
  role: "bot",
  text: "Ask me anything about Litmus — how held-out grading works, how the agents did, or how to run it yourself.",
};

// Small talk, handled before the knowledge base so a greeting never falls
// through to "I'm not sure about that one."
const GREETINGS = new Set(["hi", "hello", "hey", "hiya", "yo", "sup", "namaste", "hola", "heya"]);
const THANKS = new Set(["thanks", "thank", "thankyou", "thx", "ty", "cheers"]);
const BYE = new Set(["bye", "goodbye", "cya", "seeya", "later"]);

function smallTalk(words: string[]): string | null {
  const has = (set: Set<string>) => words.some((w) => set.has(w));

  if (has(GREETINGS)) {
    return "Hi! I can explain how Litmus grades coding agents on tests they've never seen. Ask me about the integrity gap, how Codex did, or how to run it yourself.";
  }
  if (has(THANKS)) {
    return "You're welcome. Anything else you'd like to know about Litmus?";
  }
  if (has(BYE)) {
    return "Thanks for stopping by — go tap 'Run it' and watch a patch get graded live.";
  }
  if (words.includes("who") && (words.includes("you") || words.includes("this"))) {
    return "I'm the Litmus assistant — I answer questions about this project: what it measures, how the held-out grading works, and how the agents did.";
  }
  if (
    (words.includes("what") || words.includes("help")) &&
    (words.includes("do") || words.includes("can") || words.includes("ask"))
  ) {
    return "You can ask me about the integrity gap, held-out grading, the detectors, red-team mode, how Codex performed, whether it's multi-language, or how to try it yourself.";
  }
  return null;
}

function answer(query: string): string {
  const words: string[] = query.toLowerCase().match(/[a-z]+/g) ?? [];
  if (!words.length) return "Ask me anything about Litmus — try one of the suggestions above.";

  const chat = smallTalk(words);
  if (chat) return chat;

  // Retrieve the most relevant passage. A weak match (vague or off-topic
  // question) gets the overview rather than a strained answer.
  const { passage, score } = retrieve(query);
  if (score < MIN_SCORE) return OVERVIEW;
  return passage.text;
}

export function HelpChat() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([INTRO]);
  const [input, setInput] = useState("");
  // Blinks twice on mount (every page load), then rests once opened.
  const [blinking, setBlinking] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setBlinking(false), 2200);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, open]);

  function ask(text: string) {
    const q = text.trim();
    if (!q) return;
    setMessages((m) => [...m, { role: "user", text: q }, { role: "bot", text: answer(q) }]);
    setInput("");
  }

  return (
    <>
      {open && (
        <div className="fixed bottom-24 right-5 z-[60] flex w-[360px] max-w-[calc(100vw-2.5rem)] flex-col overflow-hidden rounded-4xl border border-ink/10 bg-white shadow-lift">
          <div className="flex items-center gap-3 bg-ink px-5 py-4 text-white">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10">
              <Mark light size={18} />
            </span>
            <div className="leading-tight">
              <div className="text-[15px] font-bold">Ask about Litmus</div>
              <div className="text-[12px] text-white/55">Answers from the report</div>
            </div>
          </div>

          <div ref={scrollRef} className="max-h-[46vh] min-h-[220px] space-y-3 overflow-y-auto px-5 py-5">
            {messages.map((m, i) => (
              <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
                <div
                  className={`max-w-[85%] rounded-3xl px-4 py-2.5 text-[14px] leading-relaxed ${
                    m.role === "user"
                      ? "bg-ink text-white"
                      : "border border-ink/10 bg-mist text-ink"
                  }`}
                >
                  {m.text}
                </div>
              </div>
            ))}

            {messages.length <= 1 && (
              <div className="flex flex-wrap gap-2 pt-1">
                {SUGGESTED.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => ask(s)}
                    className="rounded-full border border-ink/12 px-3.5 py-1.5 text-[13px] text-muted transition-colors hover:border-ink/30 hover:text-ink"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              ask(input);
            }}
            className="flex items-center gap-2 border-t border-ink/10 p-3"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question…"
              className="min-w-0 flex-1 rounded-full bg-mist px-4 py-2.5 text-[14px] text-ink outline-none placeholder:text-muted-light"
            />
            <button
              type="submit"
              aria-label="Send"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-ink text-white transition-transform hover:-translate-y-0.5"
            >
              <SendIcon />
            </button>
          </form>
        </div>
      )}

      <button
        type="button"
        onClick={() => {
          setOpen((o) => !o);
          setBlinking(false);
        }}
        aria-label={open ? "Close help" : "Ask about Litmus"}
        className={`fixed bottom-5 right-5 z-[60] flex h-14 w-14 items-center justify-center rounded-full bg-ink text-white shadow-lift transition-transform duration-300 hover:scale-105 ${
          blinking && !open ? "help-blink" : ""
        }`}
      >
        {/* An expanding ring accompanies the two attention pulses on load. */}
        {blinking && !open && (
          <span className="help-ring pointer-events-none absolute inset-0 rounded-full border-2 border-ink" />
        )}
        {/* The icon rotates a quarter turn and crossfades chat -> X on toggle. */}
        <span
          className="relative flex h-6 w-6 items-center justify-center transition-transform duration-300"
          style={{ transform: open ? "rotate(90deg)" : "rotate(0deg)" }}
        >
          <span className={`absolute transition-opacity duration-200 ${open ? "opacity-0" : "opacity-100"}`}>
            <ChatIcon />
          </span>
          <span className={`absolute transition-opacity duration-200 ${open ? "opacity-100" : "opacity-0"}`}>
            <CloseIcon />
          </span>
        </span>
      </button>
    </>
  );
}

function ChatIcon() {
  // A rounded speech bubble with a tail, matching the reference mark.
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5c-1 0-2-.2-2.9-.6L4.5 20l1.1-4.6A7.5 7.5 0 1 1 20 11.5z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M3.4 20.4 21 12 3.4 3.6 3 10l12 2-12 2z" />
    </svg>
  );
}
