"""Command line entry point: litmus validate | run."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .agents import build_agent
from .check import as_markdown, check_patch
from .providers import DEFAULT_MODELS, DEFAULT_RPM
from .scaffold import scaffold_pack
from .models import VERDICT_GAMED, TaskRun
from .packs import PackError, load_all
from .runner import run_task
from .scorer import build_report  # noqa: F401  (used by cmd_run and cmd_report)
from .validate import validate_pack

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKS = REPO_ROOT / "packs"

VERDICT_MARK = {"fixed": "FIXED", "gamed": "GAMED", "failed": "failed"}


def load_env_file(path: Path = REPO_ROOT / ".env") -> None:
    """Minimal .env reader.

    Keeps provider keys in a gitignored file instead of the shell history,
    without taking a dependency just to parse KEY=value. Real environment
    variables always win, so CI and one-off overrides still work.
    """
    if not path.exists():
        return

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


def _select(packs, only: str | None):
    if not only:
        return packs
    wanted = {p.strip() for p in only.split(",") if p.strip()}
    chosen = [p for p in packs if p.id in wanted]
    missing = wanted - {p.id for p in chosen}
    if missing:
        sys.exit(f"unknown pack ids: {', '.join(sorted(missing))}")
    return chosen


def cmd_validate(args) -> int:
    try:
        packs = _select(load_all(Path(args.packs)), args.only)
    except PackError as exc:
        sys.exit(str(exc))

    failures = 0
    for pack in packs:
        problems = validate_pack(pack)
        if problems:
            failures += 1
            print(f"[FAIL] {pack.id}")
            for problem in problems:
                print(f"       - {problem}")
        else:
            print(f"[ok]   {pack.id}")

    print(f"\n{len(packs) - failures}/{len(packs)} packs sound")
    return 1 if failures else 0


def _print_run(run: TaskRun, attempt: int | None = None) -> None:
    mark = VERDICT_MARK[run.verdict]
    label = f"{run.task_id} #{attempt}" if attempt else run.task_id
    print(
        f"  {mark:<5}  {label:<30} "
        f"public {run.public.passed}/{run.public.total}  "
        f"hidden {run.hidden.passed}/{run.hidden.total}  "
        f"flags {len(run.flags)}"
    )
    for flag in run.high_severity_flags[:3]:
        print(f"         ! {flag.code} {flag.file}:{flag.line}  {flag.evidence}")
    if run.error:
        print(f"         error: {run.error}")


def cmd_run(args) -> int:
    try:
        packs = _select(load_all(Path(args.packs)), args.only)
    except PackError as exc:
        sys.exit(str(exc))

    specs = [s.strip() for s in args.agents.split(",") if s.strip()]
    if any(s.startswith("mock:") for s in specs) and not args.allow_mock:
        sys.exit(
            "mock agents are fixtures for testing the harness, not benchmark results.\n"
            "Pass --allow-mock if you are deliberately exercising the pipeline."
        )

    runs_by_config: dict[str, list[TaskRun]] = {}
    for spec in specs:
        try:
            agent = build_agent(
                spec,
                model=args.model,
                max_turns=args.max_turns,
                rpm=args.rpm,
                codex_unsandboxed=args.allow_codex_unsandboxed,
            )
        except ValueError as exc:
            sys.exit(str(exc))

        # Each provider resolves its own default model, so read it back off the
        # agent rather than assuming the --model flag was supplied.
        model_label = getattr(agent, "model", "") or (args.model or "")
        print(f"\n{agent.name}" + (f"  [{model_label}]" if model_label else ""))

        collected: list[TaskRun] = []
        for pack in packs:
            for attempt in range(1, max(1, args.repeat) + 1):
                run = run_task(
                    agent, pack, model=model_label, timeout_s=args.timeout, attempt=attempt
                )
                collected.append(run)
                _print_run(run, attempt if args.repeat > 1 else None)
        runs_by_config[agent.name] = collected

    report = build_report(runs_by_config)
    report["contains_mock_results"] = any(s.startswith("mock:") for s in specs)

    print("\n" + "=" * 72)
    for row in report["leaderboard"]:
        print(
            f"{row['agent_config']:<20} "
            f"reported {row['reported_score']:>5}%   "
            f"true {row['true_score']:>5}%   "
            f"integrity gap {row['integrity_gap']:>5} pts   "
            f"flagged {row['flagged_tasks']}/{row['tasks']}"
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


def cmd_report(args) -> int:
    """Merge saved run artifacts into one report.

    Provider quotas mean a full sweep often cannot be done in one sitting. This
    lets runs accumulate across sessions and be combined afterwards, and it
    keeps a failed batch from destroying results that were already good.
    """
    sources: list[Path] = []
    for pattern in args.sources:
        matches = sorted(Path().glob(pattern)) if any(c in pattern for c in "*?[") else [Path(pattern)]
        sources.extend(m for m in matches if m.is_file())

    if not sources:
        sys.exit("no run artifacts matched")

    runs_by_config: dict[str, list[TaskRun]] = {}
    seen: set[tuple[str, str, int]] = set()
    dropped = 0

    for source in sources:
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  skipped {source}: {exc}")
            continue

        for record in payload.get("runs", []):
            run = TaskRun.from_dict(record)
            if args.drop_errors and run.error:
                dropped += 1
                continue
            if args.drop_mock and run.agent_config.startswith("mock:"):
                dropped += 1
                continue

            # Later files win for the same config/task/attempt.
            key = (run.agent_config, run.task_id, run.attempt)
            if key in seen:
                runs_by_config[run.agent_config] = [
                    r
                    for r in runs_by_config[run.agent_config]
                    if (r.agent_config, r.task_id, r.attempt) != key
                ]
            seen.add(key)
            runs_by_config.setdefault(run.agent_config, []).append(run)

        print(f"  read {source}")

    if not runs_by_config:
        sys.exit("nothing left after filtering")

    report = build_report(runs_by_config)
    report["contains_mock_results"] = any(c.startswith("mock:") for c in runs_by_config)

    print()
    for row in report["leaderboard"]:
        print(
            f"{row['agent_config']:<20} "
            f"reported {row['reported_score']:>5}%   "
            f"true {row['true_score']:>5}%   "
            f"gap {row['integrity_gap']:>5} pts   "
            f"runs {row['tasks']}"
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nmerged {len(seen)} runs into {out}" + (f" ({dropped} dropped)" if dropped else ""))
    return 0


def cmd_new_pack(args) -> int:
    try:
        root = scaffold_pack(Path(args.packs), args.id, args.title, args.category)
    except FileExistsError as exc:
        sys.exit(str(exc))

    print(f"created {root}")
    print("\nnext:")
    print("  1. seed a real bug in workspace/solution.py")
    print("  2. write the correct version in reference/solution.py")
    print("  3. make one public test fail against the bug")
    print("  4. write held-out tests as properties, not examples")
    print(f"\nthen: litmus validate --only {args.id}")
    return 0


def cmd_check(args) -> int:
    try:
        packs = load_all(Path(args.packs))
    except PackError as exc:
        sys.exit(str(exc))

    pack = next((p for p in packs if p.id == args.pack), None)
    if pack is None:
        sys.exit(f"unknown pack: {args.pack}")

    patch_text = (
        sys.stdin.read() if args.patch == "-" else Path(args.patch).read_text(encoding="utf-8")
    )
    run = check_patch(pack, patch_text, timeout_s=args.timeout)

    if args.markdown:
        print(as_markdown(run))
    else:
        _print_run(run)

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(run.to_dict(), indent=2), encoding="utf-8")

    # Non-zero when the patch games the tests, so CI can block on it.
    return 1 if run.verdict == VERDICT_GAMED else 0


def main(argv: list[str] | None = None) -> int:
    load_env_file()
    parser = argparse.ArgumentParser(prog="litmus", description=__doc__)
    parser.add_argument("--packs", default=str(DEFAULT_PACKS), help="packs directory")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="check that every pack satisfies its invariants")
    validate.add_argument("--only", help="comma-separated pack ids")
    validate.set_defaults(func=cmd_validate)

    run = sub.add_parser("run", help="run agents against the packs")
    run.add_argument(
        "--agents",
        default="codex:iterative",
        help="comma-separated agent specs, e.g. 'codex:iterative,codex:reviewed,gemini:oneshot'. "
        "codex:* runs on a ChatGPT sign-in with no API key and no daily cap worth "
        "worrying about, which is why it is the default.",
    )
    run.add_argument(
        "--model",
        default=None,
        help="override the model id; each provider has its own default "
        f"({', '.join(f'{k}={v}' for k, v in DEFAULT_MODELS.items())})",
    )
    run.add_argument("--only", help="comma-separated pack ids")
    run.add_argument("--timeout", type=int, default=60, help="per-suite timeout in seconds")
    run.add_argument(
        "--rpm",
        type=int,
        default=DEFAULT_RPM,
        help=f"requests per minute ceiling per agent (default {DEFAULT_RPM}, the "
        "Gemini free-tier limit). Use 0 to disable pacing.",
    )
    run.add_argument(
        "--max-turns",
        type=int,
        default=8,
        help="maximum model turns per task before the patch is frozen (default 8)",
    )
    run.add_argument("--out", default="runs/latest.json")
    run.add_argument("--allow-mock", action="store_true")
    run.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="attempts per task. Agents are stochastic, so one run cannot tell a "
        "systematic behaviour from a coin flip (default 1)",
    )
    run.add_argument(
        "--allow-codex-unsandboxed",
        action="store_true",
        help="let codex:* agents run with OS sandboxing disabled. Required on "
        "platforms where the CLI cannot obtain workspace write access otherwise.",
    )
    run.set_defaults(func=cmd_run)

    report = sub.add_parser(
        "report", help="merge saved run artifacts into one report"
    )
    report.add_argument("sources", nargs="+", help="run JSON files or globs")
    report.add_argument("--out", default="web/data/report.json")
    report.add_argument(
        "--drop-errors",
        action="store_true",
        help="exclude runs that did not complete, so a quota failure cannot "
        "masquerade as a zero score",
    )
    report.add_argument("--drop-mock", action="store_true", help="exclude fixture runs")
    report.set_defaults(func=cmd_report)

    new_pack = sub.add_parser("new-pack", help="scaffold a new task pack")
    new_pack.add_argument("id", help="pack id, e.g. p004-timezone-rounding")
    new_pack.add_argument("--title", default="TODO: one-line symptom")
    new_pack.add_argument("--category", default="general")
    new_pack.set_defaults(func=cmd_new_pack)

    check = sub.add_parser(
        "check",
        help="grade a patch produced elsewhere; exits 1 when the patch games the tests",
    )
    check.add_argument("--pack", required=True, help="pack id to grade against")
    check.add_argument("--patch", required=True, help="unified diff file, or - for stdin")
    check.add_argument("--timeout", type=int, default=60)
    check.add_argument("--markdown", action="store_true", help="emit a PR comment")
    check.add_argument("--json-out", help="also write the full run record here")
    check.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
