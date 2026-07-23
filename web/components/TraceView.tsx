import type { TraceStep } from "@/lib/report";

const KIND_LABEL: Record<string, string> = {
  read: "read",
  write: "write",
  test: "test",
  message: "note",
  other: "step",
};

const KIND_TONE: Record<string, string> = {
  read: "text-white/45",
  write: "text-brand",
  test: "text-ok",
  message: "text-white/45",
  other: "text-white/35",
};

/**
 * What the agent actually did, in order.
 *
 * The verdict says whether the patch held; this says how it got there — which
 * is the difference between reading a score and reviewing an agent.
 */
export function TraceView({ trace }: { trace: TraceStep[] }) {
  if (!trace?.length) return null;

  return (
    <div className="border-t border-white/10">
      <div className="px-8 py-6 text-[13px] font-semibold uppercase tracking-wider2 text-white/50">
        What it did · {trace.length} steps
      </div>
      <ol className="px-8 pb-8">
        {trace.map((step) => (
          <li
            key={step.index}
            className="flex items-baseline gap-4 border-t border-white/8 py-2.5 first:border-t-0"
          >
            <span className="w-6 shrink-0 text-right font-mono text-[11.5px] text-white/25">
              {step.index}
            </span>
            <span
              className={`w-12 shrink-0 text-[11.5px] font-semibold uppercase tracking-wider2 ${
                KIND_TONE[step.kind] ?? KIND_TONE.other
              }`}
            >
              {KIND_LABEL[step.kind] ?? step.kind}
            </span>
            <span className="min-w-0 flex-1 truncate font-mono text-[12.5px] text-white/75">
              {step.detail}
            </span>
            {step.result && (
              <span className="shrink-0 text-[11.5px] text-white/35">{step.result}</span>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
