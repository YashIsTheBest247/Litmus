import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0A0A0B",
          soft: "#141417",
          mid: "#1F1F24",
          line: "#2A2A31",
        },
        mist: {
          DEFAULT: "#F7F7F8",
          deep: "#EFEFF1",
        },
        muted: {
          DEFAULT: "#6B6B73",
          light: "#9A9AA2",
        },
        brand: "#2F6BFF",
        ok: "#16A34A",
        bad: "#E11D48",
        warn: "#D97706",
        violet: "#7C3AED",
        teal: "#0D9488",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        "4xl": "28px",
        "5xl": "36px",
      },
      boxShadow: {
        pill: "0 10px 40px -12px rgba(10,10,11,0.28)",
        card: "0 2px 4px rgba(10,10,11,0.03), 0 12px 32px -12px rgba(10,10,11,0.10)",
        lift: "0 8px 16px rgba(10,10,11,0.05), 0 24px 56px -20px rgba(10,10,11,0.18)",
      },
      letterSpacing: {
        tightest: "-0.035em",
        wider2: "0.14em",
      },
      opacity: {
        3: "0.03",
        4: "0.04",
        6: "0.06",
        7: "0.07",
        8: "0.08",
        12: "0.12",
        15: "0.15",
        35: "0.35",
        45: "0.45",
        55: "0.55",
        65: "0.65",
        85: "0.85",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        grow: {
          "0%": { transform: "scaleX(0)" },
          "100%": { transform: "scaleX(1)" },
        },
      },
      animation: {
        rise: "rise 0.8s cubic-bezier(0.22, 1, 0.36, 1) both",
        grow: "grow 1.2s cubic-bezier(0.22, 1, 0.36, 1) both",
      },
    },
  },
  plugins: [],
} satisfies Config;
