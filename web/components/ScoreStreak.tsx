/**
 * The reading, drawn as a single bar.
 *
 * The filled length is what the agent claimed by turning the visible suite
 * green. The solid part is how much of that claim survived the held-out suite;
 * the hatched part is what did not.
 */
export function ScoreStreak({
  reported,
  real,
  tone = "light",
  delay = 0,
}: {
  reported: number;
  real: number;
  tone?: "light" | "dark";
  delay?: number;
}) {
  const gap = Math.max(0, reported - real);
  const dark = tone === "dark";

  return (
    <div className="w-full">
      <div
        className={`relative h-4 w-full overflow-hidden rounded-full ${
          dark ? "bg-white/8" : "bg-ink/8"
        }`}
      >
        <div
          className={`absolute inset-y-0 left-0 origin-left animate-grow rounded-full ${
            dark ? "bg-white" : "bg-ink"
          }`}
          style={{ width: `${real}%`, animationDelay: `${delay}ms` }}
        />

        {gap > 0.05 && (
          <div
            className="absolute inset-y-0 origin-left animate-grow"
            style={{
              left: `${real}%`,
              width: `${gap}%`,
              animationDelay: `${delay + 200}ms`,
              backgroundImage:
                "repeating-linear-gradient(115deg, #E11D48 0 5px, rgba(225,29,72,0.22) 5px 10px)",
            }}
          />
        )}
      </div>

      <div className="mt-4 flex flex-wrap items-baseline gap-x-7 gap-y-2">
        <Legend
          label="held up"
          value={`${real}%`}
          className={dark ? "text-white" : "text-ink"}
          muted={dark ? "text-white/50" : "text-muted"}
        />
        {gap > 0.05 && (
          <Legend
            label="did not"
            value={`${Math.round(gap * 10) / 10}%`}
            className="text-bad"
            muted={dark ? "text-white/50" : "text-muted"}
          />
        )}
        <span className={`ml-auto text-[13px] ${dark ? "text-white/45" : "text-muted"}`}>
          claimed {reported}%
        </span>
      </div>
    </div>
  );
}

function Legend({
  label,
  value,
  className,
  muted,
}: {
  label: string;
  value: string;
  className: string;
  muted: string;
}) {
  return (
    <span className="flex items-baseline gap-2">
      <span className={`text-[14px] ${muted}`}>{label}</span>
      <span className={`text-[15px] font-bold ${className}`}>{value}</span>
    </span>
  );
}
