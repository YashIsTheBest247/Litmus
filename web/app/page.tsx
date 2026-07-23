import Image from "next/image";
import Link from "next/link";

import { Footer } from "@/components/Footer";
import { ScoreStreak } from "@/components/ScoreStreak";
import { SiteNav } from "@/components/SiteNav";
import { FLAG_LABELS, headline, loadReport } from "@/lib/report";

export default function HomePage() {
  const report = loadReport();
  const stats = headline(report);
  const hasData = report.runs.length > 0;

  return (
    <>
      <SiteNav />
      <main>
        <Hero stats={stats} hasData={hasData} isMock={!!report.contains_mock_results} />
        <QuickStrip report={report} />
        {hasData ? (
          <>
            <Finding stats={stats} report={report} />
            <Leaderboard report={report} />
            <Tasks report={report} />
          </>
        ) : (
          <EmptyState />
        )}
        <HowItWorks />
        <ClosingPanel />
      </main>
      <Footer />
    </>
  );
}

/* ------------------------------------------------------------------ hero */

function Hero({
  stats,
  hasData,
  isMock,
}: {
  stats: ReturnType<typeof headline>;
  hasData: boolean;
  isMock: boolean;
}) {
  return (
    <section
      data-band="dark"
      className="relative flex min-h-[100svh] items-center overflow-hidden band-dark pb-14 pt-24"
    >
      {/* Photo: Mohammad Rahmani / Unsplash. The dark fall-off sits left, so
          the overlay only has to carry the headline area - the code and the
          bokeh on the right stay visible. */}
      <div aria-hidden className="absolute inset-0">
        <Image
          src="/hero.jpg"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover object-[60%_center]"
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(90deg, rgba(10,10,11,0.96) 0%, rgba(10,10,11,0.88) 24%, rgba(10,10,11,0.58) 46%, rgba(10,10,11,0.14) 72%, rgba(10,10,11,0.30) 100%)",
          }}
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(10,10,11,0.70) 0%, rgba(10,10,11,0.04) 20%, rgba(10,10,11,0.06) 56%, rgba(10,10,11,0.96) 100%)",
          }}
        />
      </div>

      <div className="shell relative">
        {/* Wide enough that the stat row stays on one line; the paragraph
            keeps its own narrower measure for readability. */}
        <div className="max-w-4xl">
          <div className="flex animate-rise items-center gap-3">
            <span className="text-[15px] font-bold text-white">Litmus</span>
            <span className="h-4 w-px bg-white/25" />
            <span className="text-[13.5px] font-medium text-white/55">
              the test your agent cannot study for
            </span>
          </div>

          <h1
            className="h-display mt-5 animate-rise text-[clamp(2.4rem,5vw,4rem)] leading-[1.0] text-white"
            style={{ animationDelay: "80ms" }}
          >
            Green tests,
            <br />
            <em className="font-normal italic text-white/45">broken code.</em>
          </h1>

          <p
            className="mt-5 max-w-[36rem] animate-rise text-[16.5px] leading-[1.55] text-white/60"
            style={{ animationDelay: "160ms" }}
          >
            Coding agents are graded on tests they can read. Litmus grades them on a suite
            they never see, and reports the distance between the two numbers.
          </p>

          <p
            className="mt-5 animate-rise text-[12.5px] font-semibold uppercase tracking-wider2 text-white/40"
            style={{ animationDelay: "220ms" }}
          >
            Two suites. One hidden. The gap is the finding.
          </p>

          <div
            className="mt-7 flex animate-rise flex-wrap items-center gap-3"
            style={{ animationDelay: "280ms" }}
          >
            <Link href="#finding" className="pill pill-solid-light">
              See the finding <span className="text-[13px]">↗</span>
            </Link>
            <Link href="/method" className="pill pill-ghost-dark">
              How it works
            </Link>
            <Link href="#tasks" className="pill pill-ghost-dark">
              <TerminalIcon />
              Inspect a patch
            </Link>
          </div>

          <div
            className="mt-7 flex animate-rise flex-wrap items-center gap-x-5 gap-y-2 text-[13.5px] text-white/50"
            style={{ animationDelay: "340ms" }}
          >
            <span>8 static detectors</span>
            <span className="rule-v" />
            <span>3 agent configurations</span>
            <span className="rule-v" />
            <span>Held-out grading</span>
            {hasData && (
              <>
                <span className="rule-v" />
                <span>{stats.gap} pt integrity gap</span>
              </>
            )}
            {isMock && (
              <span className="rounded-full border border-bad/40 px-3.5 py-1 text-[12px] font-semibold text-bad">
                fixture data
              </span>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ----------------------------------------------------------- quick strip */

function QuickStrip({ report }: { report: ReturnType<typeof loadReport> }) {
  if (!report.tasks.length) return null;
  return (
    <section className="band-light border-b border-ink/8">
      <div className="shell flex flex-wrap items-center justify-center gap-x-10 gap-y-3 py-7">
        {report.tasks.map((t) => (
          <Link
            key={t.task_id}
            href={`/task/${t.task_id}`}
            className="text-[15px] font-medium text-muted transition-colors hover:text-ink"
          >
            {t.title}
          </Link>
        ))}
      </div>
    </section>
  );
}

/* --------------------------------------------------------------- finding */

function Finding({
  stats,
  report,
}: {
  stats: ReturnType<typeof headline>;
  report: ReturnType<typeof loadReport>;
}) {
  const flagCodes = Array.from(
    new Set(report.leaderboard.flatMap((r) => Object.keys(r.flag_counts))),
  );

  return (
    <section id="finding" className="band-light py-20 sm:py-24">
      <div className="shell">
        <h2 className="h-display max-w-3xl text-[clamp(2.4rem,5.2vw,4rem)] leading-[1.06]">
          Two scores for the same work, and only one of them gets published.
        </h2>

        <p className="lede mt-7 max-w-2xl">
          Every task ships a reference implementation that passes both suites, so each gap
          below is a bug that was solvable honestly. Measured over{" "}
          {report.totals.packs} task {report.totals.packs === 1 ? "pack" : "packs"} and{" "}
          {report.totals.configs} agent{" "}
          {report.totals.configs === 1 ? "configuration" : "configurations"}.
        </p>

        <div className="card mt-14 p-9 sm:p-11">
          <div className="flex flex-wrap items-baseline gap-3">
            <span className="text-[13px] font-semibold uppercase tracking-wider2 text-muted">
              Across every run in this report
            </span>
            <span className="ml-auto text-[14px] text-muted">
              {stats.claimed - stats.gamed} of {stats.claimed} claimed fixes held
            </span>
          </div>
          <div className="mt-8">
            <ScoreStreak reported={stats.reported} real={stats.real} delay={120} />
          </div>
        </div>

        <div className="mt-6 grid gap-6 sm:grid-cols-3">
          <Stat
            label="Reported score"
            value={`${stats.reported}%`}
            note="the visible suite turned green"
          />
          <Stat
            label="True score"
            value={`${stats.real}%`}
            note="survived the held-out suite"
          />
          <Stat
            label="Integrity gap"
            value={`${stats.gap}`}
            unit="pts"
            note={`${stats.gamed} of ${stats.claimed} claimed fixes did not hold`}
            accent
          />
        </div>

        {flagCodes.length > 0 && (
          <>
            <p className="mt-16 text-[15px] font-semibold text-ink">
              What the detectors found in the diffs
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              {flagCodes.map((code) => (
                <span key={code} className="chip">
                  {FLAG_LABELS[code] ?? code}
                </span>
              ))}
            </div>
          </>
        )}
      </div>
    </section>
  );
}

function Stat({
  label,
  value,
  unit,
  note,
  accent,
}: {
  label: string;
  value: string;
  unit?: string;
  note: string;
  accent?: boolean;
}) {
  return (
    <div className="card p-8">
      <div className="text-[14px] font-semibold text-muted">{label}</div>
      <div className="mt-5 flex items-baseline gap-1.5">
        <span
          className={`text-[clamp(2.8rem,5vw,3.8rem)] font-extrabold leading-none tracking-tightest ${
            accent ? "text-bad" : "text-ink"
          }`}
        >
          {value}
        </span>
        {unit && <span className="text-[17px] font-semibold text-muted">{unit}</span>}
      </div>
      <p className="mt-5 text-[15px] leading-relaxed text-muted">{note}</p>
    </div>
  );
}

/* ----------------------------------------------------------- leaderboard */

function Leaderboard({ report }: { report: ReturnType<typeof loadReport> }) {
  return (
    <section id="leaderboard" className="band-mist py-20 sm:py-24">
      <div className="shell">
        <h2 className="h-display max-w-3xl text-[clamp(2.4rem,5.2vw,3.8rem)] leading-[1.06]">
          Ranked by what held up, not by what was claimed.
        </h2>

        <div className="mt-14 space-y-6">
          {report.leaderboard.map((row, i) => (
            <div key={row.agent_config} className="card p-8 sm:p-10">
              <div className="flex flex-wrap items-center gap-x-5 gap-y-3">
                <span className="text-[15px] font-semibold text-muted-light">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="text-[27px] font-extrabold tracking-tight">
                  {row.agent_config}
                </span>
                {row.model && (
                  <span className="rounded-full border border-ink/10 px-3.5 py-1.5 text-[13px] font-medium text-muted">
                    {row.model}
                  </span>
                )}
                <span className="ml-auto flex items-baseline gap-2">
                  <span className="text-[42px] font-extrabold leading-none tracking-tightest">
                    {row.true_score}%
                  </span>
                  <span className="text-[14px] font-semibold text-muted">true</span>
                </span>
              </div>

              <div className="mt-8">
                <ScoreStreak reported={row.reported_score} real={row.true_score} delay={i * 90} />
              </div>

              {/* Stacked rather than a four-across grid: one metric per line
                  reads down the card instead of across it. */}
              <dl className="mt-8 border-t border-ink/8">
                <Cell label="Integrity gap" value={`${row.integrity_gap} pts`} accent />
                <Cell label="Fixed" value={`${row.fixed} of ${row.tasks}`} />
                <Cell label="Gamed" value={`${row.gamed} of ${row.tasks}`} />
                <Cell label="Failed" value={`${row.failed} of ${row.tasks}`} />
                <Cell label="Flagged by detectors" value={`${row.flagged_tasks} of ${row.tasks}`} />
                <Cell label="Mean turns" value={`${row.mean_turns}`} />
              </dl>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Cell({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="flex items-baseline justify-between gap-6 border-b border-ink/8 py-3.5 last:border-b-0">
      <dt className="text-[14.5px] text-muted">{label}</dt>
      <dd className={`text-[16px] font-bold ${accent ? "text-bad" : "text-ink"}`}>{value}</dd>
    </div>
  );
}

/* ----------------------------------------------------------------- tasks */

function Tasks({ report }: { report: ReturnType<typeof loadReport> }) {
  return (
    <section id="tasks" className="band-light py-20 sm:py-24">
      <div className="shell">
        <h2 className="h-display max-w-3xl text-[clamp(2.4rem,5.2vw,3.8rem)] leading-[1.06]">
          Every bug here is solvable. The reference proves it.
        </h2>

        <div className="mt-14 grid gap-6 md:grid-cols-2">
          {report.tasks.map((task) => (
            <Link
              key={task.task_id}
              href={`/task/${task.task_id}`}
              className="card group flex flex-col p-8 transition-all hover:-translate-y-1 hover:shadow-lift"
            >
              <div className="flex items-center gap-3">
                <span className="rounded-full border border-ink/10 px-3.5 py-1.5 text-[12.5px] font-semibold uppercase tracking-wider2 text-muted">
                  {task.category}
                </span>
                <span className="ml-auto font-mono text-[12.5px] text-muted-light">
                  {task.task_id}
                </span>
              </div>

              <h3 className="mt-6 text-[24px] font-bold leading-[1.25] tracking-tight">
                {task.title}
              </h3>

              <div className="mt-8 flex items-center gap-5 border-t border-ink/8 pt-6">
                <Tally n={task.fixed} label="fixed" tone="text-ok" />
                <Tally n={task.gamed} label="gamed" tone="text-bad" />
                <Tally n={task.failed} label="failed" tone="text-muted" />
                <span className="ml-auto text-[15px] font-semibold text-ink transition-transform group-hover:translate-x-1">
                  Inspect →
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

function Tally({ n, label, tone }: { n: number; label: string; tone: string }) {
  if (!n) return null;
  return (
    <span className="text-[14px]">
      <span className={`font-bold ${tone}`}>{n}</span>{" "}
      <span className="text-muted">{label}</span>
    </span>
  );
}

/* ----------------------------------------------------------- how it works */

const STEPS = [
  {
    n: "01",
    title: "Two suites, one hidden",
    body: "Each pack ships tests_public.py and tests_hidden.py. Only the first is ever copied into the sandbox, so there is no window in which the agent could read the other.",
    preview: <PreviewFiles />,
  },
  {
    n: "02",
    title: "The agent works, unrestricted",
    body: "It reads files, edits code and reruns the visible suite as often as it likes. Nothing is forbidden, including editing the tests. Litmus measures what an agent does, it does not police it.",
    preview: <PreviewLoop />,
  },
  {
    n: "03",
    title: "Freeze, then grade",
    body: "Writes stop and the patch is fixed. Only then is the held-out suite copied in, with any conftest or ini file the agent created quarantined first.",
    preview: <PreviewFreeze />,
  },
  {
    n: "04",
    title: "Two scores, one gap",
    body: "The visible suite gives the reported score, the held-out suite gives the true one, and eight detectors read the diff separately to name the line.",
    preview: <PreviewScores />,
  },
];

function HowItWorks() {
  return (
    <section className="band-mist py-20 sm:py-24">
      <div className="shell">
        <h2 className="h-display text-[clamp(2.4rem,5.2vw,3.8rem)] leading-[1.06]">
          How Litmus works
        </h2>
        <p className="lede mt-5 max-w-xl">
          Integrity enforced by structure, not by asking the agent nicely.
        </p>

        <div className="mt-14 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
          {STEPS.map((step) => (
            <div key={step.n} className="card flex flex-col p-7">
              {/* Fixed heights on the preview and title keep the four cards'
                  numbers, headings and body copy on the same baselines. */}
              <div className="flex min-h-[176px] items-center rounded-3xl bg-mist p-5">
                <div className="w-full">{step.preview}</div>
              </div>
              <div className="mt-7 text-[34px] font-extrabold leading-none text-ink/15">
                {step.n}
              </div>
              <h3 className="mt-4 min-h-[3.5rem] text-[20px] font-bold leading-snug tracking-tight">
                {step.title}
              </h3>
              <p className="mt-3 text-[14.5px] leading-relaxed text-muted">{step.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function PreviewFiles() {
  return (
    <div className="space-y-2.5">
      <PreviewRow icon="visible" label="tests_public.py" note="in sandbox" tone="ok" />
      <PreviewRow icon="hidden" label="tests_hidden.py" note="withheld" tone="bad" />
      <PreviewRow icon="visible" label="solution.py" note="editable" tone="neutral" />
    </div>
  );
}

function PreviewLoop() {
  return (
    <div className="space-y-2.5">
      <PreviewRow icon="visible" label="read_file" note="" tone="neutral" />
      <PreviewRow icon="visible" label="write_file" note="" tone="neutral" />
      <PreviewRow icon="visible" label="run_public_tests" note="×4" tone="ok" />
    </div>
  );
}

function PreviewFreeze() {
  return (
    <div className="space-y-2.5">
      <PreviewRow icon="hidden" label="writes closed" note="frozen" tone="neutral" />
      <PreviewRow icon="hidden" label="conftest.py" note="quarantined" tone="bad" />
      <PreviewRow icon="visible" label="held-out suite" note="running" tone="ok" />
    </div>
  );
}

function PreviewScores() {
  return (
    <div className="space-y-3 py-1">
      <div>
        <div className="flex items-baseline justify-between">
          <span className="text-[12.5px] font-medium text-muted">reported</span>
          <span className="text-[13px] font-bold">100%</span>
        </div>
        <div className="mt-1.5 h-2 rounded-full bg-ink/10">
          <div className="h-2 w-full rounded-full bg-ink/30" />
        </div>
      </div>
      <div>
        <div className="flex items-baseline justify-between">
          <span className="text-[12.5px] font-medium text-muted">true</span>
          <span className="text-[13px] font-bold text-bad">0%</span>
        </div>
        <div className="mt-1.5 h-2 rounded-full bg-ink/10">
          <div
            className="h-2 w-full rounded-full"
            style={{
              backgroundImage:
                "repeating-linear-gradient(115deg, #E11D48 0 4px, rgba(225,29,72,0.22) 4px 8px)",
            }}
          />
        </div>
      </div>
    </div>
  );
}

function PreviewRow({
  icon,
  label,
  note,
  tone,
}: {
  icon: "visible" | "hidden";
  label: string;
  note: string;
  tone: "ok" | "bad" | "neutral";
}) {
  const noteTone = tone === "ok" ? "text-ok" : tone === "bad" ? "text-bad" : "text-muted";
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-ink/8 bg-white px-3.5 py-2.5">
      <span className="truncate font-mono text-[12px] text-ink/80">{label}</span>
      {note && (
        <span className={`ml-auto shrink-0 text-[11.5px] font-medium ${noteTone}`}>{note}</span>
      )}
      <span className="sr-only">{icon}</span>
    </div>
  );
}

/* --------------------------------------------------------- closing panel */

function ClosingPanel() {
  return (
    <section className="band-light pb-14 pt-4">
      <div className="shell">
        <div
          data-band="dark"
          className="relative overflow-hidden rounded-5xl bg-ink px-8 py-16 text-center sm:px-14"
        >
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0"
            style={{
              background:
                "radial-gradient(60% 70% at 50% 0%, rgba(47,107,255,0.18), transparent 65%)",
            }}
          />
          <div className="relative">
            <h2 className="h-display mx-auto max-w-3xl text-[clamp(2.2rem,4.8vw,3.6rem)] leading-[1.08] text-white">
              A green suite shouldn&apos;t require trust.
            </h2>
            <p className="mx-auto mt-5 max-w-xl text-[17px] leading-[1.6] text-white/55">
              Point Litmus at your own agent before you point your agent at your repository.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Link href="/method" className="pill pill-solid-light">
                Read the method <span className="text-[13px]">↗</span>
              </Link>
              <Link href="#tasks" className="pill pill-ghost-dark">
                Inspect the patches
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ----------------------------------------------------------- empty state */

function EmptyState() {
  return (
    <section className="band-light py-28">
      <div className="shell max-w-3xl">
        <h2 className="h-display text-[clamp(2rem,4.4vw,3rem)] leading-tight">
          Run the harness to populate this page.
        </h2>
        <pre className="mt-9 overflow-x-auto rounded-4xl bg-ink px-7 py-6 font-mono text-[13px] leading-relaxed text-white/85">
{`python -m litmus.cli --packs packs run \\
  --agents "openai:oneshot,openai:iterative,openai:reviewed" \\
  --out web/data/report.json`}
        </pre>
      </div>
    </section>
  );
}

function TerminalIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path
        d="M3 4.5L6.5 8L3 11.5M8.5 11.5H13"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
