import Link from "next/link";

import { Mark } from "@/components/Mark";

const COLUMNS = [
  {
    title: "Read",
    links: [
      { href: "/#finding", label: "The finding" },
      { href: "/#leaderboard", label: "Leaderboard" },
      { href: "/#tasks", label: "Task packs" },
    ],
  },
  {
    title: "Method",
    links: [
      { href: "/method", label: "How it works" },
      { href: "/method#invariants", label: "Pack invariants" },
      { href: "/method#detectors", label: "The eight detectors" },
    ],
  },
  {
    title: "Built with",
    links: [
      { href: "/method#codex", label: "OpenAI Codex" },
      { href: "/method#codex", label: "Three agent configs" },
    ],
  },
];

const SOCIALS = [
  {
    label: "LinkedIn",
    href: "https://www.linkedin.com/in/yash-munshi-a0408b337/",
    icon: <LinkedInIcon />,
  },
  {
    label: "GitHub",
    href: "https://github.com/YashIsTheBest247",
    icon: <GitHubIcon />,
  },
  {
    label: "Portfolio",
    href: "https://yash-munshi.vercel.app/",
    icon: <PortfolioIcon />,
  },
];

export function Footer() {
  return (
    <footer
      data-band="dark"
      className="relative flex min-h-[72vh] flex-col justify-end overflow-hidden band-dark pt-28"
    >
      {/* The oversized watermark, cropped by the section edge. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-[12%] select-none text-center text-[26vw] font-extrabold leading-none tracking-tightest text-white/[0.035]"
      >
        litmus
      </div>

      <div className="shell relative">
        <div className="grid gap-14 pb-16 md:grid-cols-[1.3fr_1fr_1fr_1fr]">
          <div>
            <div className="flex items-center gap-2.5">
              <Mark light />
              <span className="text-[22px] font-extrabold tracking-tight text-white">Litmus</span>
            </div>
            <p className="mt-5 max-w-xs text-[15px] leading-relaxed text-white/50">
              A litmus test gives one answer and does not care how the sample looks. A suite
              the agent never saw works the same way.
            </p>
          </div>

          {COLUMNS.map((col) => (
            <div key={col.title}>
              <div className="text-[15px] font-bold text-brand">{col.title}</div>
              <ul className="mt-5 space-y-3">
                {col.links.map((l) => (
                  <li key={l.href + l.label}>
                    <Link
                      href={l.href}
                      className="text-[15px] text-white/55 transition-colors hover:text-white"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-white/10 py-9">
          <p className="text-[13px] text-white/30">
            Every number on this site was produced by the harness in this repository.
          </p>

          <div className="mt-7 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-[13.5px] text-white/45">
              Litmus 2026. All Rights Reserved.
            </p>

            <div className="flex items-center gap-4">
              <span className="text-[13.5px] text-white/45">Connect with developer</span>
              <div className="flex items-center gap-2.5">
                {SOCIALS.map((social) => (
                  <a
                    key={social.label}
                    href={social.href}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={social.label}
                    title={social.label}
                    className="group inline-flex h-11 w-11 items-center justify-center rounded-full border border-white/15 text-white/60 transition-all duration-300 hover:-translate-y-1 hover:border-white hover:bg-white hover:text-ink"
                  >
                    <span className="transition-transform duration-300 group-hover:scale-110">
                      {social.icon}
                    </span>
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}

function LinkedInIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M4.98 3.5A2.5 2.5 0 1 1 0 3.5a2.5 2.5 0 0 1 4.98 0zM.22 8.02h4.54V24H.22V8.02zM8.34 8.02h4.35v2.18h.06c.61-1.15 2.09-2.37 4.3-2.37 4.6 0 5.45 3.03 5.45 6.96V24h-4.53v-7.31c0-1.74-.03-3.98-2.42-3.98-2.43 0-2.8 1.9-2.8 3.86V24H8.34V8.02z" />
    </svg>
  );
}

function GitHubIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M12 .5C5.37.5 0 5.87 0 12.5c0 5.3 3.44 9.8 8.21 11.39.6.11.82-.26.82-.58 0-.29-.01-1.05-.02-2.06-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.83 2.81 1.3 3.5.99.11-.78.42-1.3.76-1.6-2.67-.3-5.47-1.34-5.47-5.96 0-1.32.47-2.39 1.24-3.23-.12-.31-.54-1.53.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 6.01 0c2.29-1.55 3.3-1.23 3.3-1.23.66 1.65.24 2.87.12 3.18.77.84 1.24 1.91 1.24 3.23 0 4.63-2.81 5.65-5.49 5.95.43.37.82 1.1.82 2.22 0 1.6-.02 2.9-.02 3.29 0 .32.22.7.83.58A12.01 12.01 0 0 0 24 12.5C24 5.87 18.63.5 12 .5z" />
    </svg>
  );
}

function PortfolioIcon() {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      aria-hidden
    >
      <circle cx="12" cy="12" r="9.5" />
      <path d="M12 2.5c2.6 2.7 3.9 6.2 3.9 9.5s-1.3 6.8-3.9 9.5c-2.6-2.7-3.9-6.2-3.9-9.5s1.3-6.8 3.9-9.5z" />
      <path d="M2.8 9h18.4M2.8 15h18.4" />
    </svg>
  );
}

