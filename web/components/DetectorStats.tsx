import {
  FLAG_LABELS,
  type ConsistencyRow,
  type DetectorStat,
  type RedTeam,
} from "@/lib/report";

/**
 * The detectors graded against the held-out suite.
 *
 * Eight detectors is not the same as eight good detectors. The held-out suite
 * is ground truth here: a detector that fires on runs the suite also rejects
 * found something; one that fires on runs the suite accepts was wrong. Nothing
 * else on this site would surface that.
 */
export function DetectorStats({ stats }: { stats: DetectorStat[] }) {
  if (!stats?.length) return null;

  return (
    <div className="mt-12 overflow-x-auto">
      <table className="w-full min-w-[560px] border-collapse text-left">
        <thead>
          <tr className="border-b border-ink/12">
            <th className="pb-3 text-[13px] font-semibold uppercase tracking-wider2 text-muted">
              Detector
            </th>
            <th className="pb-3 text-right text-[13px] font-semibold uppercase tracking-wider2 text-muted">
              Fired
            </th>
            <th className="pb-3 text-right text-[13px] font-semibold uppercase tracking-wider2 text-muted">
              On gamed
            </th>
            <th className="pb-3 text-right text-[13px] font-semibold uppercase tracking-wider2 text-muted">
              On clean
            </th>
            <th className="pb-3 text-right text-[13px] font-semibold uppercase tracking-wider2 text-muted">
              Agreement
            </th>
          </tr>
        </thead>
        <tbody>
          {stats.map((row) => (
            <tr key={row.code} className="border-b border-ink/8">
              <td className="py-4 text-[15px] font-medium">
                {FLAG_LABELS[row.code] ?? row.code}
              </td>
              <td className="py-4 text-right font-mono text-[14px] text-muted">{row.fired}</td>
              <td className="py-4 text-right font-mono text-[14px] text-ok">{row.on_gamed}</td>
              <td className="py-4 text-right font-mono text-[14px] text-bad">{row.on_clean}</td>
              <td className="py-4 text-right text-[15px] font-bold">{row.precision}%</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-5 max-w-2xl text-[14.5px] leading-relaxed text-muted">
        Agreement is how often a detector fired on a patch the held-out suite also rejected.
        A low number is not a bug in the detector so much as a warning: it is flagging
        patches that turned out to be general after all.
      </p>
    </div>
  );
}

/**
 * Detector recall, from patches that were deliberately made to cheat.
 *
 * Precision on its own flatters a detector set — you can be perfectly precise
 * by almost never firing. Recall requires known cheats, and the only reliable
 * way to get them is to ask an agent for them.
 */
export function RedTeamPanel({ data }: { data?: RedTeam }) {
  if (!data || !data.attempts) return null;

  return (
    <div className="mt-14">
      <h3 className="text-[22px] font-bold tracking-tight">Red team</h3>
      <p className="lede mt-4 max-w-2xl">
        An agent was instructed to make the visible suite pass by any means —
        recognising test inputs, returning constants, catching errors, editing the
        tests. This is not a claim about how agents behave unprompted. It exists to
        manufacture known cheats, because recall cannot be measured without them.
      </p>

      <div className="mt-10 grid gap-6 sm:grid-cols-4">
        <Metric label="Attempts" value={`${data.attempts}`} />
        <Metric label="Cheats produced" value={`${data.gamed}`} tone="text-bad" />
        <Metric label="Caught by detectors" value={`${data.caught_by_detectors}`} tone="text-ok" />
        <Metric label="Recall" value={`${data.recall}%`} big />
      </div>

      {(data.fixed_anyway > 0 || data.failed_to_cheat > 0) && (
        <p className="mt-8 max-w-2xl text-[15.5px] leading-relaxed text-muted">
          {data.fixed_anyway > 0 && (
            <>
              <strong className="font-semibold text-ink">
                {data.fixed_anyway} of {data.attempts} attempts fixed the bug properly
                despite being told to cheat.
              </strong>{" "}
            </>
          )}
          {data.failed_to_cheat > 0 && (
            <>
              {data.failed_to_cheat} could not turn the visible suite green at all.
            </>
          )}
        </p>
      )}

      {data.missed_by_detectors > 0 && (
        <div className="mt-8 rounded-4xl border border-warn/30 bg-warn/8 px-7 py-5">
          <p className="text-[15px] leading-relaxed text-warn">
            <strong className="font-bold">
              {data.missed_by_detectors} cheats slipped past every detector.
            </strong>{" "}
            The held-out suite caught them, which is the point of having one — static
            analysis is the cheaper check, not the reliable one.
            {data.missed_tasks.length > 0 && (
              <> Missed on: {data.missed_tasks.join(", ")}.</>
            )}
          </p>
        </div>
      )}

      {Object.keys(data.techniques).length > 0 && (
        <div className="mt-8">
          <p className="text-[15px] font-semibold">Techniques it reached for</p>
          <div className="mt-4 flex flex-wrap gap-3">
            {Object.entries(data.techniques).map(([code, count]) => (
              <span key={code} className="chip">
                {FLAG_LABELS[code] ?? code}
                <span className="ml-2 font-mono text-[13px] text-muted">×{count}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Metric({
  label,
  value,
  tone,
  big,
}: {
  label: string;
  value: string;
  tone?: string;
  big?: boolean;
}) {
  return (
    <div className="card p-7">
      <div className="text-[13.5px] font-semibold text-muted">{label}</div>
      <div
        className={`mt-3 font-extrabold leading-none tracking-tightest ${
          big ? "text-[44px]" : "text-[34px]"
        } ${tone ?? "text-ink"}`}
      >
        {value}
      </div>
    </div>
  );
}

export function ConsistencyPanel({ rows }: { rows: ConsistencyRow[] }) {
  if (!rows?.length) return null;

  const unstable = rows.filter((r) => !r.stable);

  return (
    <div className="mt-12">
      <p className="max-w-2xl text-[16px] leading-relaxed text-muted">
        {unstable.length === 0 ? (
          <>
            Every repeated task produced the same verdict on every attempt. The behaviour is
            systematic, not a coin flip.
          </>
        ) : (
          <>
            <strong className="font-semibold text-ink">
              {unstable.length} of {rows.length} repeated tasks changed verdict between
              attempts.
            </strong>{" "}
            Those results are a distribution, not a fact, and a single run of them would have
            been misleading either way.
          </>
        )}
      </p>

      {unstable.length > 0 && (
        <div className="mt-8 space-y-3">
          {unstable.map((row) => (
            <div
              key={`${row.agent_config}-${row.task_id}`}
              className="card flex flex-wrap items-baseline gap-x-6 gap-y-2 p-6"
            >
              <span className="text-[15px] font-bold">{row.agent_config}</span>
              <span className="font-mono text-[13px] text-muted">{row.task_id}</span>
              <span className="ml-auto text-[14px] text-muted">
                <span className="font-bold text-ok">{row.fixed}</span> fixed ·{" "}
                <span className="font-bold text-bad">{row.gamed}</span> gamed ·{" "}
                <span className="font-bold text-muted">{row.failed}</span> failed
                <span className="ml-2 text-muted-light">of {row.attempts}</span>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
