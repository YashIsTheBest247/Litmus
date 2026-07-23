"use client";

import { useEffect, useState } from "react";

import { Footer } from "@/components/Footer";
import { SiteNav } from "@/components/SiteNav";
import { WakeSequence } from "@/components/WakeSequence";
import { API_URL, hasLiveRun } from "@/lib/site";
import type { Run } from "@/lib/report";

type Candidate = { id: string; label: string; description: string };

type LivePack = {
  id: string;
  title: string;
  category: string;
  bug_report: string;
  entrypoint: string;
  source: string;
  public_tests: string;
  hidden_test_count: number;
  candidates: Candidate[];
};

export default function TryPage() {
  const [packs, setPacks] = useState<LivePack[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [result, setResult] = useState<Run | null>(null);
  const [running, setRunning] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [waking, setWaking] = useState(false);

  useEffect(() => {
    if (!hasLiveRun) return;
    let cancelled = false;

    /* Free-tier hosting sleeps after a quarter hour idle and takes about a
       minute to wake. Without this the first visitor of the day sees a dead
       page and assumes the demo is broken, so retry patiently and say what is
       happening. */
    async function wakeAndLoad() {
      const slowNotice = setTimeout(() => !cancelled && setWaking(true), 2500);

      for (let attempt = 0; attempt < 12; attempt++) {
        try {
          const response = await fetch(`${API_URL}/api/packs`, { cache: "no-store" });
          if (response.ok) {
            const data = await response.json();
            if (cancelled) return;
            clearTimeout(slowNotice);
            setWaking(false);
            setPacks(data.packs ?? []);
            setSelected(data.packs?.[0]?.id ?? "");
            return;
          }
        } catch {
          // Service still cold; fall through and retry.
        }
        await new Promise((resolve) => setTimeout(resolve, 5000));
      }

      if (!cancelled) {
        clearTimeout(slowNotice);
        setWaking(false);
        setError("The live-run service did not respond. It may still be starting up.");
      }
    }

    wakeAndLoad();
    return () => {
      cancelled = true;
    };
  }, []);

  const pack = packs.find((p) => p.id === selected);

  async function run(candidate: string) {
    setRunning(candidate);
    setResult(null);
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pack_id: selected, candidate }),
      });
      if (!response.ok) throw new Error(await response.text());
      setResult(await response.json());
    } catch {
      setError("The run did not complete.");
    } finally {
      setRunning("");
    }
  }

  return (
    <>
      <SiteNav />
      <main>
        <section data-band="dark" className="band-dark pb-16 pt-32">
          <div className="shell">
            <div className="flex items-center gap-3">
              <span className="text-[15px] font-bold text-white">Litmus</span>
              <span className="h-4 w-px bg-white/25" />
              <span className="text-[13.5px] font-medium text-white/55">Run it yourself</span>
            </div>
            <h1 className="h-display mt-6 max-w-4xl text-[clamp(2.2rem,5vw,3.6rem)] leading-[1.04] text-white">
              Three patches. All green.
              <br />
              <em className="font-normal italic text-white/45">One of them is real.</em>
            </h1>
            <p className="mt-6 max-w-2xl text-[16.5px] leading-[1.6] text-white/55">
              Every candidate below turns the visible suite green. Pick one and the harness
              runs for real — it materialises the workspace, applies the patch, freezes it,
              then runs the held-out suite the patch has never seen.
            </p>
          </div>
        </section>

        {!hasLiveRun ? <SetupNotice /> : null}

        {hasLiveRun && waking && (
          <section className="band-light py-16">
            <div className="shell">
              <WakeSequence />
            </div>
          </section>
        )}

        {hasLiveRun && !waking && (
          <section className="band-light py-16">
            <div className="shell">
              {packs.length > 1 && (
                <div className="mb-10 flex flex-wrap gap-2">
                  {packs.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => {
                        setSelected(p.id);
                        setResult(null);
                      }}
                      className={`rounded-full border px-5 py-2.5 text-[14.5px] font-medium transition-colors ${
                        p.id === selected
                          ? "border-ink bg-ink text-white"
                          : "border-ink/12 text-muted hover:border-ink/30"
                      }`}
                    >
                      {p.title}
                    </button>
                  ))}
                </div>
              )}

              {pack && (
                <div className="grid gap-8 lg:grid-cols-[1fr_1.1fr]">
                  <div>
                    <h2 className="text-[20px] font-bold">The bug</h2>
                    <p className="mt-4 whitespace-pre-line text-[15px] leading-relaxed text-muted">
                      {pack.bug_report.trim()}
                    </p>

                    <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-[14px] text-muted">
                      <span>
                        <strong className="font-semibold text-ink">
                          {pack.public_tests.split("def test_").length - 1}
                        </strong>{" "}
                        visible tests
                      </span>
                      <span>
                        <strong className="font-semibold text-ink">
                          {pack.hidden_test_count}
                        </strong>{" "}
                        held-out tests the patch never sees
                      </span>
                    </div>

                    <pre className="mt-8 max-h-80 overflow-auto rounded-4xl bg-ink px-6 py-5 font-mono text-[12.5px] leading-relaxed text-white/85">
                      {pack.source}
                    </pre>
                  </div>

                  <div>
                    <h2 className="text-[20px] font-bold">Pick a patch</h2>
                    <div className="mt-4 space-y-3">
                      {pack.candidates.map((candidate) => (
                        <button
                          key={candidate.id}
                          type="button"
                          disabled={!!running}
                          onClick={() => run(candidate.id)}
                          className="card flex w-full items-center gap-5 p-6 text-left transition-all hover:-translate-y-0.5 hover:shadow-lift disabled:opacity-50"
                        >
                          <span className="flex-1">
                            <span className="block text-[16.5px] font-bold">
                              {candidate.label}
                            </span>
                            <span className="mt-1 block text-[14px] text-muted">
                              {candidate.description}
                            </span>
                          </span>
                          <span className="flex shrink-0 items-center gap-2 text-[14px] font-semibold text-ink">
                            {running === candidate.id ? (
                              <>
                                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-ink/20 border-t-ink" />
                                Running
                              </>
                            ) : (
                              "Run →"
                            )}
                          </span>
                        </button>
                      ))}
                    </div>

                    {error && (
                      <p className="mt-6 rounded-3xl border border-bad/30 bg-bad/8 px-6 py-4 text-[14.5px] text-bad">
                        {error}
                      </p>
                    )}

                    {result && <ResultPanel run={result} />}
                  </div>
                </div>
              )}
            </div>
          </section>
        )}
      </main>
      <Footer />
    </>
  );
}

function ResultPanel({ run }: { run: Run }) {
  const tone =
    run.verdict === "fixed" ? "text-ok" : run.verdict === "gamed" ? "text-bad" : "text-muted";
  const failedHidden = run.hidden.cases.filter((c) => c.status !== "passed");

  return (
    <div className="card mt-8 p-8">
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-2">
        <span className={`text-[30px] font-extrabold uppercase tracking-tight ${tone}`}>
          {run.verdict}
        </span>
        <span className="ml-auto text-[13.5px] text-muted">{run.wall_s}s</span>
      </div>

      <div className="mt-7 grid grid-cols-2 gap-5">
        <Suite label="Visible suite" passed={run.public.passed} total={run.public.total} />
        <Suite label="Held-out suite" passed={run.hidden.passed} total={run.hidden.total} />
      </div>

      {run.flags.length > 0 && (
        <div className="mt-7 border-t border-ink/8 pt-6">
          <p className="text-[13px] font-semibold uppercase tracking-wider2 text-muted">
            {run.flags.length} detector {run.flags.length === 1 ? "finding" : "findings"}
          </p>
          <div className="mt-4 space-y-3">
            {run.flags.map((flag, i) => (
              <div key={i} className="rounded-3xl border border-bad/25 bg-bad/8 px-5 py-4">
                <div className="flex items-baseline justify-between gap-4">
                  <span className="text-[14.5px] font-bold text-bad">{flag.code}</span>
                  <span className="font-mono text-[12px] text-muted">
                    {flag.file}:{flag.line}
                  </span>
                </div>
                <pre className="mt-3 overflow-x-auto font-mono text-[12.5px] text-ink/80">
                  {flag.evidence}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}

      {failedHidden.length > 0 && (
        <div className="mt-7 border-t border-ink/8 pt-6">
          <p className="text-[13px] font-semibold uppercase tracking-wider2 text-muted">
            Held-out tests it failed
          </p>
          <ul className="mt-4 space-y-1.5">
            {failedHidden.slice(0, 6).map((test, i) => (
              <li key={i} className="font-mono text-[12.5px] text-muted">
                {test.name.split("::").pop()}
              </li>
            ))}
          </ul>
          {failedHidden.length > 6 && (
            <p className="mt-3 text-[13.5px] text-muted">
              and {failedHidden.length - 6} more
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Suite({ label, passed, total }: { label: string; passed: number; total: number }) {
  const green = total > 0 && passed === total;
  return (
    <div className="rounded-3xl border border-ink/10 px-6 py-5">
      <div className="text-[13.5px] font-semibold text-muted">{label}</div>
      <div className="mt-3 flex items-baseline gap-2">
        <span className={`text-[34px] font-extrabold leading-none ${green ? "text-ok" : "text-bad"}`}>
          {passed}
        </span>
        <span className="text-[15px] font-medium text-muted">/ {total}</span>
      </div>
    </div>
  );
}

function SetupNotice() {
  return (
    <section className="band-light py-20">
      <div className="shell max-w-3xl">
        <h2 className="h-display text-[clamp(1.9rem,4vw,2.6rem)] leading-tight">
          The live-run service is not configured.
        </h2>
        <p className="lede mt-5">
          Start it locally and point the site at it. Everything it runs is real — the same
          harness that produced the report on the home page.
        </p>
        <pre className="mt-8 overflow-x-auto rounded-4xl bg-ink px-7 py-6 font-mono text-[13px] leading-relaxed text-white/85">
{`# terminal 1
python -m uvicorn service.app:app --port 8010

# web/.env.local
NEXT_PUBLIC_LITMUS_API=http://127.0.0.1:8010`}
        </pre>
      </div>
    </section>
  );
}
