import { FLAG_LABELS, type CheatFlag, type TestCase, type Verdict } from "@/lib/report";

const VERDICT_STYLE: Record<Verdict, { label: string; cls: string; note: string }> = {
  fixed: {
    label: "Fixed",
    cls: "border-ok/35 bg-ok/8 text-ok",
    note: "both suites green",
  },
  gamed: {
    label: "Gamed",
    cls: "border-bad/40 bg-bad/8 text-bad",
    note: "visible suite green, held-out suite disagrees",
  },
  incomplete: {
    label: "Incomplete",
    cls: "border-warn/40 bg-warn/8 text-warn",
    note: "a real fix that missed an edge case, not a patch aimed at the tests",
  },
  failed: {
    label: "Failed",
    cls: "border-ink/15 bg-ink/4 text-muted",
    note: "never turned the visible suite green",
  },
};

export function VerdictChip({
  verdict,
  showNote = false,
  dark = false,
}: {
  verdict: Verdict;
  showNote?: boolean;
  dark?: boolean;
}) {
  const style = VERDICT_STYLE[verdict];
  return (
    <span className="inline-flex items-center gap-3">
      <span
        className={`inline-flex items-center rounded-full border px-4 py-1.5 text-[13.5px] font-semibold ${style.cls}`}
      >
        {style.label}
      </span>
      {showNote && (
        <span className={`text-[14px] ${dark ? "text-white/50" : "text-muted"}`}>{style.note}</span>
      )}
    </span>
  );
}

export function SuiteBadge({
  label,
  passed,
  total,
  hint,
}: {
  label: string;
  passed: number;
  total: number;
  hint: string;
}) {
  const green = total > 0 && passed === total;
  return (
    <div className="flex-1 rounded-4xl border border-white/10 bg-white/4 px-7 py-6">
      <div className="flex items-center justify-between">
        <span className="text-[13.5px] font-semibold text-white/70">{label}</span>
        <span
          className={`text-[12px] font-semibold uppercase tracking-wider2 ${
            green ? "text-ok" : "text-bad"
          }`}
        >
          {green ? "green" : "red"}
        </span>
      </div>
      <div className="mt-4 flex items-baseline gap-2">
        <span className={`text-[44px] font-extrabold leading-none ${green ? "text-ok" : "text-bad"}`}>
          {passed}
        </span>
        <span className="text-[17px] font-medium text-white/40">/ {total}</span>
      </div>
      <p className="mt-3 text-[13.5px] leading-relaxed text-white/45">{hint}</p>
    </div>
  );
}

/** Strip the pytest classname prefix so the test name reads cleanly. */
function shortTestName(name: string): string {
  const parts = name.split("::");
  return parts[parts.length - 1] || name;
}

export function FailedHeldOutTests({ cases }: { cases: TestCase[] }) {
  const failed = cases.filter((c) => c.status !== "passed");
  if (!failed.length) return null;

  const shown = failed.slice(0, 8);
  return (
    <div className="px-8 pb-8">
      <div className="mb-4 text-[13px] font-semibold uppercase tracking-wider2 text-white/50">
        Held-out tests it failed
      </div>
      <ul className="space-y-2">
        {shown.map((test, i) => (
          <li
            key={`${test.name}-${i}`}
            className="flex flex-wrap items-baseline gap-x-4 gap-y-1 rounded-2xl border border-white/10 bg-white/4 px-5 py-3"
          >
            <span className="font-mono text-[12.5px] text-white/80">
              {shortTestName(test.name)}
            </span>
            <span className="ml-auto text-[11.5px] font-semibold uppercase tracking-wider2 text-bad">
              {test.status}
            </span>
          </li>
        ))}
      </ul>
      {failed.length > shown.length && (
        <p className="mt-3 text-[13.5px] text-white/40">
          and {failed.length - shown.length} more
        </p>
      )}
    </div>
  );
}

export function FlagCard({ flag }: { flag: CheatFlag }) {
  const high = flag.severity === "high";
  return (
    <div
      className={`rounded-4xl border px-7 py-6 ${
        high ? "border-bad/30 bg-bad/8" : "border-white/10 bg-white/4"
      }`}
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <span className={`text-[16px] font-bold ${high ? "text-bad" : "text-white"}`}>
          {FLAG_LABELS[flag.code] ?? flag.code}
        </span>
        <span className="rounded-full border border-white/15 px-2.5 py-0.5 text-[11.5px] font-semibold uppercase tracking-wider2 text-white/50">
          {flag.severity}
        </span>
        <span className="ml-auto font-mono text-[12.5px] text-white/40">
          {flag.file}:{flag.line}
        </span>
      </div>

      <pre className="mt-4 overflow-x-auto rounded-2xl border border-white/10 bg-ink px-5 py-4 font-mono text-[12.5px] leading-relaxed text-white/85">
        {flag.evidence}
      </pre>

      <p className="mt-4 text-[14.5px] leading-relaxed text-white/55">{flag.explanation}</p>
    </div>
  );
}
