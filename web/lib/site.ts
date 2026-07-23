/**
 * Outbound links that depend on where this is actually published.
 *
 * Set NEXT_PUBLIC_REPO_URL (locally in .env.local, on Vercel as a project env
 * var) once the repository is public. Until it is set, the nav falls back to
 * the method page rather than shipping a link that goes nowhere useful.
 */

export const REPO_URL = process.env.NEXT_PUBLIC_REPO_URL?.trim() || "";

export const hasRepo = REPO_URL.length > 0;
