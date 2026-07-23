import Link from "next/link";
import { notFound } from "next/navigation";

import { DiffView } from "@/components/DiffView";
import { Footer } from "@/components/Footer";
import { SiteNav } from "@/components/SiteNav";
import { FlagCard, SuiteBadge, VerdictChip } from "@/components/Verdict";
import { loadReport, runsForTask, taskIds } from "@/lib/report";

export function generateStaticParams() {
  return taskIds(loadReport()).map((id) => ({ id }));
}

export default async function TaskPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const report = loadReport();
  const runs = runsForTask(report, id);

  if (!runs.length) notFound();

  const first = runs[0];
  const gamed = runs.filter((r) => r.verdict === "gamed").length;

  return (
    <>
      <SiteNav />
      <main data-band="dark" className="band-dark">
        <section className="relative overflow-hidden pb-20 pt-40">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                "radial-gradient(70% 55% at 75% 10%, rgba(47,107,255,0.14), transparent 62%)",
            }}
          />
          <div className="shell relative">
            <Link
              href="/#tasks"
              className="text-[14px] font-medium text-white/45 transition-colors hover:text-white"
            >
              ← All tasks
            </Link>

            <div className="mt-8 flex flex-wrap items-center gap-3">
              <span className="rounded-full border border-white/15 px-4 py-1.5 text-[12.5px] font-semibold uppercase tracking-wider2 text-white/60">
                {first.category}
              </span>
              <span className="font-mono text-[13px] text-white/35">{first.task_id}</span>
            </div>

            <h1 className="h-display mt-7 max-w-4xl text-[clamp(2.4rem,5.6vw,4.2rem)] leading-[1.05] text-white">
              {first.task_title}
            </h1>

            {gamed > 0 && (
              <p className="lede mt-7 max-w-2xl text-white/55">
                {gamed} of {runs.length} {runs.length === 1 ? "attempt" : "attempts"} turned the
                visible suite green without fixing the bug.
              </p>
            )}

            {first.bug_report && (
              <div className="card-dark mt-12 max-w-3xl p-8">
                <div className="text-[13px] font-semibold uppercase tracking-wider2 text-white/50">
                  Bug report given to the agent
                </div>
                <p className="mt-5 whitespace-pre-line text-[15.5px] leading-relaxed text-white/70">
                  {first.bug_report.trim()}
                </p>
              </div>
            )}
          </div>
        </section>

        <section className="pb-28">
          <div className="shell space-y-8">
            {runs.map((run) => (
              <article key={run.agent_config} className="card-dark overflow-hidden">
                <header className="flex flex-wrap items-center gap-x-5 gap-y-3 border-b border-white/10 px-8 py-7">
                  <span className="text-[24px] font-extrabold tracking-tight text-white">
                    {run.agent_config}
                  </span>
                  <VerdictChip verdict={run.verdict} showNote dark />
                  <span className="ml-auto text-[13.5px] text-white/40">
                    {run.turns} turns · {run.wall_s}s
                  </span>
                </header>

                <div className="flex flex-col gap-5 px-8 py-8 sm:flex-row">
                  <SuiteBadge
                    label="Visible suite"
                    passed={run.public.passed}
                    total={run.public.total}
                    hint="the agent could read and rerun this"
                  />
                  <SuiteBadge
                    label="Held-out suite"
                    passed={run.hidden.passed}
                    total={run.hidden.total}
                    hint="copied in only after the patch was frozen"
                  />
                </div>

                {run.error && (
                  <p className="mx-8 mb-7 rounded-3xl border border-bad/25 bg-bad/8 px-6 py-5 font-mono text-[13px] text-bad">
                    {run.error}
                  </p>
                )}

                {run.flags.length > 0 && (
                  <div className="px-8 pb-8">
                    <div className="mb-5 text-[13px] font-semibold uppercase tracking-wider2 text-white/50">
                      {run.flags.length} detector {run.flags.length === 1 ? "finding" : "findings"}
                    </div>
                    <div className="space-y-4">
                      {run.flags.map((flag, i) => (
                        <FlagCard key={`${flag.code}-${i}`} flag={flag} />
                      ))}
                    </div>
                  </div>
                )}

                <div className="border-t border-white/10">
                  <div className="flex flex-wrap items-center gap-4 px-8 py-6">
                    <span className="text-[13px] font-semibold uppercase tracking-wider2 text-white/50">
                      The patch
                    </span>
                    {run.files_changed.map((f) => (
                      <span key={f} className="font-mono text-[12.5px] text-white/45">
                        {f}
                      </span>
                    ))}
                  </div>
                  <div className="border-t border-white/10 bg-ink py-3">
                    <DiffView patch={run.patch} flags={run.flags} />
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
