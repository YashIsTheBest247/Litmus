import type { Run } from "@/lib/report";

/**
 * What an ordinary CI run would have reported for this patch.
 *
 * The verdict elsewhere on the page is the conclusion. This is the thing that
 * makes it land: the same patch, rendered the way every pipeline in the world
 * would render it — all green, ready to merge — beside what the held-out suite
 * found. The gap between these two boxes is the entire project.
 */
export function CiIllusion({ run }: { run: Run }) {
  if (run.verdict !== "gamed") return null;

  return (
    <div className="grid gap-4 px-8 pb-8 sm:grid-cols-2">
      <div className="rounded-4xl border border-ok/25 bg-ok/8 px-7 py-6">
        <div className="flex items-center gap-2.5">
          <Check />
          <span className="text-[13px] font-semibold uppercase tracking-wider2 text-ok">
            What your CI reports
          </span>
        </div>
        <pre className="mt-4 overflow-x-auto font-mono text-[12.5px] leading-relaxed text-white/80">
{`$ pytest
${".".repeat(Math.min(run.public.total, 40))}
${run.public.total} passed`}
        </pre>
        <p className="mt-4 text-[14px] leading-relaxed text-white/50">
          Green. Approved. Merged.
        </p>
      </div>

      <div className="rounded-4xl border border-bad/30 bg-bad/8 px-7 py-6">
        <div className="flex items-center gap-2.5">
          <Cross />
          <span className="text-[13px] font-semibold uppercase tracking-wider2 text-bad">
            What Litmus found
          </span>
        </div>
        <pre className="mt-4 overflow-x-auto font-mono text-[12.5px] leading-relaxed text-white/80">
{`$ pytest tests_hidden.py
${"F".repeat(Math.min(run.hidden.total - run.hidden.passed, 40))}
${run.hidden.total - run.hidden.passed} failed, ${run.hidden.passed} passed`}
        </pre>
        <p className="mt-4 text-[14px] leading-relaxed text-white/50">
          The bug is still there.
        </p>
      </div>
    </div>
  );
}

function Check() {
  return (
    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-ok">
      <svg width="9" height="9" viewBox="0 0 10 10" fill="none" aria-hidden>
        <path d="M1.5 5.2L3.8 7.5L8.5 2.5" stroke="white" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </span>
  );
}

function Cross() {
  return (
    <span className="flex h-4 w-4 items-center justify-center rounded-full bg-bad">
      <svg width="9" height="9" viewBox="0 0 10 10" fill="none" aria-hidden>
        <path d="M2.5 2.5L7.5 7.5M7.5 2.5L2.5 7.5" stroke="white" strokeWidth="1.9" strokeLinecap="round" />
      </svg>
    </span>
  );
}
