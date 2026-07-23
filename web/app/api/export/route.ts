import { loadReport } from "@/lib/report";

/**
 * The report as CSV, one row per run.
 *
 * The JSON artifact is the source of truth, but a spreadsheet is what people
 * actually re-analyse results in, and exporting is the difference between
 * publishing numbers and publishing data.
 */
export const dynamic = "force-static";

const COLUMNS = [
  "task_id",
  "category",
  "agent_config",
  "model",
  "attempt",
  "verdict",
  "public_passed",
  "public_total",
  "hidden_passed",
  "hidden_total",
  "flags",
  "flag_codes",
  "turns",
  "wall_s",
  "error",
];

function escape(value: string | number | null | undefined): string {
  const text = value === null || value === undefined ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function GET() {
  const report = loadReport();

  const rows = report.runs.map((run) =>
    [
      run.task_id,
      run.category,
      run.agent_config,
      run.model,
      run.attempt ?? 1,
      run.verdict,
      run.public.passed,
      run.public.total,
      run.hidden.passed,
      run.hidden.total,
      run.flags.length,
      run.flags.map((f) => f.code).join(" "),
      run.turns,
      run.wall_s,
      run.error ?? "",
    ]
      .map(escape)
      .join(","),
  );

  const csv = [COLUMNS.join(","), ...rows].join("\n");

  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": 'attachment; filename="litmus-runs.csv"',
    },
  });
}
