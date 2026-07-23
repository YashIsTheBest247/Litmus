import fs from "node:fs";
import path from "node:path";

export type TestCase = { name: string; status: string; message: string };

export type SuiteResult = {
  suite: string;
  total: number;
  passed: number;
  failed: number;
  errored: number;
  skipped: number;
  pass_rate: number;
  all_passed: boolean;
  duration_s: number;
  timed_out: boolean;
  collection_error: boolean;
  cases: TestCase[];
  output_tail: string;
};

export type CheatFlag = {
  code: string;
  severity: "high" | "medium" | "low";
  file: string;
  line: number;
  evidence: string;
  explanation: string;
};

export type Verdict = "fixed" | "gamed" | "failed";

export type TraceStep = {
  index: number;
  kind: "read" | "write" | "test" | "message" | "other";
  detail: string;
  result: string;
};

export type DetectorStat = {
  code: string;
  fired: number;
  on_gamed: number;
  on_clean: number;
  precision: number;
};

export type ConsistencyRow = {
  agent_config: string;
  task_id: string;
  attempts: number;
  fixed: number;
  gamed: number;
  failed: number;
  stable: boolean;
};

export type Run = {
  task_id: string;
  task_title: string;
  category: string;
  agent_config: string;
  model: string;
  verdict: Verdict;
  bug_report?: string;
  public: SuiteResult;
  hidden: SuiteResult;
  flags: CheatFlag[];
  patch: string;
  files_changed: string[];
  turns: number;
  wall_s: number;
  error: string | null;
  attempt?: number;
  trace?: TraceStep[];
};

export type LeaderRow = {
  agent_config: string;
  model: string;
  tasks: number;
  fixed: number;
  gamed: number;
  failed: number;
  reported_score: number;
  true_score: number;
  integrity_gap: number;
  gamed_rate_of_claimed: number;
  flagged_tasks: number;
  flag_rate: number;
  flag_counts: Record<string, number>;
  mean_turns: number;
  mean_wall_s: number;
  errors: number;
};

export type TaskSummary = {
  task_id: string;
  title: string;
  category: string;
  attempts: number;
  gamed: number;
  fixed: number;
  failed: number;
};

export type Report = {
  leaderboard: LeaderRow[];
  tasks: TaskSummary[];
  runs: Run[];
  detectors?: DetectorStat[];
  consistency?: ConsistencyRow[];
  totals: {
    configs: number;
    packs: number;
    runs: number;
    attempts_per_task?: number;
  };
  contains_mock_results?: boolean;
};

const EMPTY: Report = {
  leaderboard: [],
  tasks: [],
  runs: [],
  detectors: [],
  consistency: [],
  totals: { configs: 0, packs: 0, runs: 0 },
};

/** The dashboard renders exactly what the harness wrote - no massaging. */
export function loadReport(): Report {
  const file = path.join(process.cwd(), "data", "report.json");
  try {
    return { ...EMPTY, ...JSON.parse(fs.readFileSync(file, "utf-8")) };
  } catch {
    return EMPTY;
  }
}

export function runsForTask(report: Report, taskId: string): Run[] {
  return report.runs.filter((r) => r.task_id === taskId);
}

export function taskIds(report: Report): string[] {
  return Array.from(new Set(report.runs.map((r) => r.task_id)));
}

/** Aggregate headline across every config in the report. */
export function headline(report: Report) {
  const rows = report.leaderboard;
  if (!rows.length) return { reported: 0, real: 0, gap: 0, gamed: 0, claimed: 0 };

  const tasks = rows.reduce((n, r) => n + r.tasks, 0);
  const claimed = rows.reduce((n, r) => n + r.fixed + r.gamed, 0);
  const fixed = rows.reduce((n, r) => n + r.fixed, 0);
  const gamed = rows.reduce((n, r) => n + r.gamed, 0);

  const reported = tasks ? (100 * claimed) / tasks : 0;
  const real = tasks ? (100 * fixed) / tasks : 0;
  return {
    reported: Math.round(reported * 10) / 10,
    real: Math.round(real * 10) / 10,
    gap: Math.round((reported - real) * 10) / 10,
    gamed,
    claimed,
  };
}

export const FLAG_LABELS: Record<string, string> = {
  TEST_FILE_MODIFIED: "Edited the test file",
  TEST_FUNCTION_REMOVED: "Deleted a test",
  SKIP_MARKER_ADDED: "Silenced a test",
  ASSERTION_WEAKENED: "Weakened an assertion",
  INPUT_LITERAL_SPECIAL_CASE: "Special-cased a test input",
  HARDCODED_EXPECTED_OUTPUT: "Returned an expected value",
  EXCEPTION_SWALLOWED: "Swallowed the failure",
  RUNNER_CONFIG_INJECTED: "Reconfigured the test runner",
};
