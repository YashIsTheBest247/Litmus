import Link from "next/link";

import { Footer } from "@/components/Footer";
import { SiteNav } from "@/components/SiteNav";

export default function NotFound() {
  return (
    <>
      <SiteNav />
      <main data-band="dark" className="band-dark">
        <section className="flex min-h-[80svh] items-center pt-32">
          <div className="shell">
            <p className="text-[13px] font-semibold uppercase tracking-wider2 text-white/40">
              404
            </p>
            <h1 className="h-display mt-6 max-w-3xl text-[clamp(2.4rem,5.6vw,4rem)] leading-[1.04] text-white">
              Nothing to grade here.
            </h1>
            <p className="mt-6 max-w-xl text-[17px] leading-[1.6] text-white/55">
              That page does not exist. If you were looking for a task, it may not be part of
              the current report.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <Link href="/" className="pill pill-solid-light">
                Back to the finding
              </Link>
              <Link href="/#tasks" className="pill pill-ghost-dark">
                Browse task packs
              </Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
