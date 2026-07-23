"use client";

import { useEffect, useRef, useState } from "react";

/**
 * A small assistant that answers questions about Litmus.
 *
 * Deliberately client-side and knowledge-base driven rather than calling a live
 * model: on a static site that means instant answers, no cold start, no cost,
 * and - the point for a project about honesty - no chance of hallucinating a
 * wrong fact about itself. Every answer below is curated from the real report.
 */

type Entry = { q: string; keywords: string[]; a: string };

const KB: Entry[] = [
  {
    q: "What is Litmus?",
    keywords: ["what", "litmus", "about", "project", "do", "purpose"],
    a: "Litmus checks whether a coding agent actually fixed your bug, or just made your tests stop failing. It grades an agent twice — once on tests it can read, once on a suite it never sees — and reports the distance between the two scores.",
  },
  {
    q: "What is the integrity gap?",
    keywords: ["integrity", "gap", "distance", "difference", "score"],
    a: "The integrity gap is the difference between what an agent claimed (the visible tests went green) and what actually held up (the held-out suite it never saw). A gap of zero means the patch was a real fix. A large gap means it gamed the tests.",
  },
  {
    q: "How does held-out grading work?",
    keywords: ["held", "hidden", "grading", "work", "how", "mechanism", "suite"],
    a: "Each task ships two suites. The agent sees tests_public and can run it freely. It never sees tests_hidden — that file isn't even on disk while the agent works; it's copied in only after the patch is frozen. Then two scores come out, and the gap is the finding.",
  },
  {
    q: "How did Codex do?",
    keywords: ["codex", "openai", "best", "winner", "perform", "result"],
    a: "Litmus was built with OpenAI Codex, and Codex is also an agent under test. It fixed every task it faced — including the one built to bait a shortcut — with a zero integrity gap and no detector finding. It was the standout for integrity.",
  },
  {
    q: "Which agents were tested?",
    keywords: ["agents", "models", "tested", "gemini", "compare", "leaderboard"],
    a: "Two coding agents across nine tasks and five prompt framings: OpenAI Codex and Gemini flash-lite. Codex had a zero gap. The weaker Gemini gamed the hardest task under four of its five prompts — even when told not to — which shows integrity moves with how you ask.",
  },
  {
    q: "What are the detectors?",
    keywords: ["detector", "detectors", "static", "flag", "eight", "catch"],
    a: "Eight static checks that read the diff and name the shortcut — a test-file edit, a skipped test, a weakened assertion, a branch keyed on a test input, and so on. Litmus even grades its own detectors against the held-out suite, and reports how many cheats slipped past them.",
  },
  {
    q: "What is red-team mode?",
    keywords: ["red", "team", "adversarial", "cheat", "recall"],
    a: "A mode where an agent is explicitly told to make the visible tests pass by any means. Every patch it produces that games the tests is a labelled cheat — the only way to measure detector recall honestly. Without it, recall would be a guess.",
  },
  {
    q: "Does it support more than Python?",
    keywords: ["language", "javascript", "python", "js", "node", "multi"],
    a: "Yes. Python (pytest) and JavaScript (Node's built-in test runner) run through the same harness via a runtime abstraction. The held-out grading is fully language-agnostic; adding a third language is just a third runtime.",
  },
  {
    q: "Can I run it myself?",
    keywords: ["try", "run", "myself", "demo", "test", "live"],
    a: "Yes — open the 'Run it' page. Pick a patch, and the real harness executes it in about a second: it applies the patch, freezes it, and runs the held-out suite live. No login, nothing faked.",
  },
  {
    q: "How is this built with Codex?",
    keywords: ["built", "made", "hackathon", "codex", "agentic", "usage"],
    a: "Codex runs as a fully autonomous agent through the CLI — it plans, reads files, edits code, and runs the tests on its own loop, and every step is recorded. It's the agent under evaluation, and the harness that grades it was built with it.",
  },
  {
    q: "What does 'gamed' mean?",
    keywords: ["gamed", "cheat", "verdict", "meaning", "incomplete", "fixed"],
    a: "A verdict. 'Fixed' means both suites passed. 'Gamed' means the visible suite is green but the held-out one isn't — the patch recognised its tests instead of solving the bug. 'Incomplete' is a real fix that missed an edge case, kept separate because it isn't deceit.",
  },
];

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

function answer(query: string): string {
  const words: string[] = query.toLowerCase().match(/[a-z]+/g) ?? [];
  if (!words.length) return "";

  let best: Entry | null = null;
  let bestScore = 0;
  for (const entry of KB) {
    const score = entry.keywords.reduce((n, k) => n + (words.includes(k) ? 1 : 0), 0);
    if (score > bestScore) {
      bestScore = score;
      best = entry;
    }
  }

  if (!best || bestScore === 0) {
    return "I'm not sure about that one. Try asking about the integrity gap, the detectors, how Codex did, or how to run it yourself — or open the 'How it works' page for the full method.";
  }
  return best.a;
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
              <Spark />
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
      <circle cx="12" cy="11.5" r="1.15" fill="currentColor" />
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

function Spark() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 2l2 6 6 2-6 2-2 6-2-6-6-2 6-2z" />
    </svg>
  );
}
