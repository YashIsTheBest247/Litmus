import { ImageResponse } from "next/og";

export const alt = "Litmus — held-out grading for coding agents";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/**
 * The social card. Rendered at build time, so a shared link carries the
 * headline claim rather than a blank rectangle.
 */
export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#0A0A0B",
          padding: "72px 80px",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div
            style={{
              display: "flex",
              width: 44,
              height: 44,
              borderRadius: 12,
              border: "3px solid rgba(255,255,255,0.85)",
              background: "linear-gradient(180deg, transparent 55%, #E11D48 55%)",
            }}
          />
          <div style={{ color: "#FFFFFF", fontSize: 38, fontWeight: 800, letterSpacing: -1 }}>
            Litmus
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column" }}>
          <div
            style={{
              color: "#FFFFFF",
              fontSize: 92,
              fontWeight: 800,
              letterSpacing: -3.5,
              lineHeight: 1.02,
            }}
          >
            Green tests,
          </div>
          <div
            style={{
              color: "rgba(255,255,255,0.45)",
              fontSize: 92,
              fontWeight: 400,
              fontStyle: "italic",
              letterSpacing: -3.5,
              lineHeight: 1.02,
            }}
          >
            broken code.
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <div style={{ color: "rgba(255,255,255,0.55)", fontSize: 26 }}>
            Two suites. One hidden. The gap is the finding.
          </div>
        </div>
      </div>
    ),
    { ...size },
  );
}
