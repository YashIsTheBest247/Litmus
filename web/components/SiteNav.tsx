"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type MouseEvent } from "react";

import { Mark } from "@/components/Mark";
import { REPO_URL, hasRepo } from "@/lib/site";

const LINKS: { href: string; label: string; hash?: string }[] = [
  { href: "/#finding", label: "The finding", hash: "finding" },
  { href: "/#leaderboard", label: "Leaderboard", hash: "leaderboard" },
  { href: "/#tasks", label: "Tasks", hash: "tasks" },
  { href: "/method", label: "How it works" },
];

export function SiteNav() {
  // The bar goes glassy over any dark band it happens to be sitting on - the
  // hero, the closing panel, the footer - and solid white over light ones.
  // Tracking the band under the bar beats tracking scroll depth, which got the
  // footer wrong.
  const [onLight, setOnLight] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();

  // Close the mobile menu whenever the route changes.
  useEffect(() => setMenuOpen(false), [pathname]);

  useEffect(() => {
    const PROBE_Y = 60; // roughly the vertical middle of the floating bar

    const sync = () => {
      const bands = document.querySelectorAll<HTMLElement>('[data-band="dark"]');
      let overDark = false;
      bands.forEach((band) => {
        const rect = band.getBoundingClientRect();
        if (rect.top <= PROBE_Y && rect.bottom >= PROBE_Y) overDark = true;
      });
      setOnLight(!overDark);
    };

    sync();
    window.addEventListener("scroll", sync, { passive: true });
    window.addEventListener("resize", sync);
    return () => {
      window.removeEventListener("scroll", sync);
      window.removeEventListener("resize", sync);
    };
  }, [pathname]);

  /* On the home page an in-page hash is a scroll, not a navigation - the App
     Router treats "/#tasks" as the same route and would otherwise do nothing. */
  const goToSection = (event: MouseEvent<HTMLAnchorElement>, hash?: string) => {
    setMenuOpen(false);
    if (!hash || pathname !== "/") return;
    const target = document.getElementById(hash);
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    window.history.replaceState(null, "", `#${hash}`);
  };

  return (
    <div className="pointer-events-none fixed inset-x-0 top-5 z-50 flex justify-center px-6">
      <div className="pointer-events-auto w-full max-w-[1180px]">
        <nav className={`nav-shell ${onLight ? "nav-on-light" : "nav-on-dark"}`}>
          <Link href="/" className="flex items-center gap-2.5 pr-6">
            <Mark light={!onLight} />
            <span className="text-[21px] font-extrabold tracking-tight">Litmus</span>
          </Link>

          <div className="hidden items-center lg:flex">
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={(event) => goToSection(event, link.hash)}
                className={`rounded-full px-4 py-2 text-[15px] font-medium transition-colors ${
                  onLight ? "text-ink/75 hover:text-ink" : "text-white/80 hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="ml-auto flex items-center gap-2">
            {/* Below lg the link row is hidden, so without this the site has
                no navigation at all on a phone. */}
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              aria-label={menuOpen ? "Close menu" : "Open menu"}
              aria-expanded={menuOpen}
              className={`inline-flex h-11 w-11 items-center justify-center rounded-full border transition-colors lg:hidden ${
                onLight
                  ? "border-ink/12 text-ink hover:border-ink/30"
                  : "border-white/20 text-white hover:border-white/45"
              }`}
            >
              <MenuIcon open={menuOpen} />
            </button>

            <Link
              href="/method#detectors"
              className={`hidden items-center gap-2 rounded-full border px-4 py-2.5 text-[14.5px] font-medium transition-colors sm:inline-flex ${
                onLight
                  ? "border-ink/12 text-ink hover:border-ink/30"
                  : "border-white/20 text-white hover:border-white/45"
              }`}
            >
              <ShieldIcon />
              Detectors
            </Link>

            <button
              type="button"
              onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
              aria-label="Back to top"
              className={`hidden h-11 w-11 items-center justify-center rounded-full border transition-colors sm:inline-flex ${
                onLight
                  ? "border-ink/12 text-ink hover:border-ink/30"
                  : "border-white/20 text-white hover:border-white/45"
              }`}
            >
              <ArrowUpIcon />
            </button>

            {hasRepo ? (
              <a
                href={REPO_URL}
                target="_blank"
                rel="noreferrer"
                className={`inline-flex items-center gap-1.5 rounded-full px-5 py-3 text-[15px] font-semibold transition-transform hover:-translate-y-0.5 ${
                  onLight ? "bg-ink text-white" : "bg-white text-ink"
                }`}
              >
                Repository <span className="text-[13px]">↗</span>
              </a>
            ) : (
              <Link
                href="/#tasks"
                className={`inline-flex items-center gap-1.5 rounded-full px-5 py-3 text-[15px] font-semibold transition-transform hover:-translate-y-0.5 ${
                  onLight ? "bg-ink text-white" : "bg-white text-ink"
                }`}
              >
                Inspect a patch
              </Link>
            )}
          </div>
        </nav>

        {menuOpen && (
          <div
            className={`mt-2 overflow-hidden rounded-4xl border p-2 backdrop-blur-2xl lg:hidden ${
              onLight ? "border-ink/10 bg-white/95 shadow-pill" : "border-white/12 bg-ink/90"
            }`}
          >
            {LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={(event) => goToSection(event, link.hash)}
                className={`block rounded-3xl px-5 py-3.5 text-[16px] font-medium transition-colors ${
                  onLight
                    ? "text-ink/80 hover:bg-ink/5 hover:text-ink"
                    : "text-white/80 hover:bg-white/10 hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function MenuIcon({ open }: { open: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      {open ? (
        <path
          d="M4 4l8 8M12 4l-8 8"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      ) : (
        <path
          d="M2.5 5h11M2.5 11h11"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      )}
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path
        d="M8 1.5l5 2v4c0 3-2 5.4-5 7-3-1.6-5-4-5-7v-4l5-2z"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ArrowUpIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path
        d="M8 13V3.5M8 3.5L3.5 8M8 3.5L12.5 8"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
