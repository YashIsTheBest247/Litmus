/**
 * Outbound links that depend on where this is actually published.
 *
 * Set NEXT_PUBLIC_REPO_URL (locally in .env.local, on Vercel as a project env
 * var) once the repository is public. Until it is set, the nav falls back to
 * the method page rather than shipping a link that goes nowhere useful.
 */

export const REPO_URL = process.env.NEXT_PUBLIC_REPO_URL?.trim() || "";

export const hasRepo = REPO_URL.length > 0;

/**
 * Absolute origin, needed so social preview images resolve. Vercel supplies
 * VERCEL_URL automatically; set NEXT_PUBLIC_SITE_URL to override with a custom
 * domain.
 */
/**
 * Base URL of the live-run service. When unset the Try page explains how to
 * start it locally rather than failing with a network error.
 */
export const API_URL = (process.env.NEXT_PUBLIC_LITMUS_API || "").replace(/\/$/, "");

export const hasLiveRun = API_URL.length > 0;

export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.trim() ||
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : "http://localhost:3000");
