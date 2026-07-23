"use client";

import { usePathname } from "next/navigation";

/**
 * Re-keying on the pathname restarts the enter animation on every route
 * change, so navigating between pages fades in rather than snapping.
 * The animation is disabled under prefers-reduced-motion (see globals.css).
 */
export function PageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div key={pathname} className="page-enter">
      {children}
    </div>
  );
}
