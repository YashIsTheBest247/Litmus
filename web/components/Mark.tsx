/**
 * The Litmus mark: a test strip dipped at one end, showing the reaction.
 *
 * The whole point of a litmus test is that the answer does not depend on how
 * the sample looks, which is exactly what a held-out suite buys you.
 */
export function Mark({ light = false, size = 30 }: { light?: boolean; size?: number }) {
  const stroke = light ? "rgba(255,255,255,0.9)" : "#0A0A0B";
  return (
    <svg width={size} height={size} viewBox="0 0 30 30" fill="none" aria-hidden>
      <g transform="rotate(-15 15 15)">
        <rect
          x="10.5"
          y="2.8"
          width="9"
          height="24.4"
          rx="3"
          stroke={stroke}
          strokeWidth="1.7"
        />
        <path
          d="M10.5 18.6h9v5.6a3 3 0 0 1-3 3h-3a3 3 0 0 1-3-3z"
          fill="#E11D48"
        />
      </g>
    </svg>
  );
}
