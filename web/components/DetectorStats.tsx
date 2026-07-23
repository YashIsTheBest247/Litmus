import { FLAG_LABELS, type ConsistencyRow, type DetectorStat } from "@/lib/report";

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
