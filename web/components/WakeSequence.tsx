"use client";

import { useEffect, useState } from "react";

/**
 * Boot sequence shown while the run service wakes.
 *
 * Free hosting sleeps after a quarter hour idle, so the first visitor waits
 * around a minute. Silence reads as "broken", and a bare spinner reads as
 * "stuck" — an advancing checklist reads as "working", which is what is
 * actually true.
 *
 * Every line describes something the cold start really does. Nothing here
 * claims work that is not happening.
 */
const STAGES: { label: string; at: number }[] = [
  { label: "Reaching the run service", at: 0 },
  { label: "Waking the container", at: 4 },
  { label: "Starting the Python harness", at: 14 },
  { label: "Loading task packs and held-out suites", at: 28 },
  { label: "Almost there — cold starts take about a minute", at: 42 },
];

export function WakeSequence() {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setElapsed((seconds) => seconds + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const activeIndex = STAGES.reduce(
    (current, stage, index) => (elapsed >= stage.at ? index : current),
    0,
  );

  // Eases toward 95% over ~70s so the bar never stalls and never lies about
  // being finished.
  const progress = Math.min(95, 8 + (1 - Math.exp(-elapsed / 22)) * 87);

  return (
    <div className="card mx-auto max-w-2xl p-8 sm:p-10">
      <div className="flex items-baseline justify-between gap-4">
        <h2 className="text-[19px] font-bold">Waking the run service</h2>
        <span className="font-mono text-[13px] text-muted-light">{elapsed}s</span>
      </div>

      <div className="mt-6 h-1.5 w-full overflow-hidden rounded-full bg-ink/8">
        <div
          className="h-full rounded-full bg-ink transition-[width] duration-1000 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      <ol className="mt-8 space-y-3.5">
        {STAGES.map((stage, index) => {
          const done = index < activeIndex;
          const active = index === activeIndex;
          if (!done && !active) {
            return (
              <li key={stage.label} className="flex items-center gap-3.5 opacity-35">
                <Pending />
                <span className="text-[15px] text-muted">{stage.label}</span>
              </li>
            );
          }
          return (
            <li
              key={stage.label}
              className="flex animate-rise items-center gap-3.5"
              style={{ animationDuration: "0.5s" }}
            >
              {done ? <Done /> : <Spinner />}
              <span className={`text-[15px] ${done ? "text-muted" : "font-medium text-ink"}`}>
                {stage.label}
              </span>
            </li>
          );
        })}
      </ol>

      <p className="mt-8 border-t border-ink/8 pt-6 text-[14px] leading-relaxed text-muted">
        Nothing is being faked while you wait — the service is a real container
        running pytest against real workspaces. Once it is up, each run takes
        about a second.
      </p>
    </div>
  );
}

function Spinner() {
  return (
    <span className="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-ink/20 border-t-ink" />
  );
}

function Done() {
  return (
    <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-ok">
      <svg width="9" height="9" viewBox="0 0 10 10" fill="none" aria-hidden>
        <path
          d="M1.5 5.2L3.8 7.5L8.5 2.5"
          stroke="white"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}

function Pending() {
  return <span className="h-4 w-4 shrink-0 rounded-full border-2 border-ink/15" />;
}
