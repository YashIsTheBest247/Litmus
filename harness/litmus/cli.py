"""Command line entry point: litmus validate | run."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .agents import build_agent
from .providers import DEFAULT_MODELS, DEFAULT_RPM
from .models import VERDICT_FIXED, VERDICT_GAMED, TaskRun
from .packs import PackError, load_all
from .runner import run_task
from .scorer import build_report
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


def _print_run(run: TaskRun) -> None:
    mark = VERDICT_MARK[run.verdict]
    print(
        f"  {mark:<5}  {run.task_id:<28} "
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
            run = run_task(agent, pack, model=model_label, timeout_s=args.timeout)
            collected.append(run)
            _print_run(run)
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
        "--allow-codex-unsandboxed",
        action="store_true",
        help="let codex:* agents run with OS sandboxing disabled. Required on "
        "platforms where the CLI cannot obtain workspace write access otherwise.",
    )
    run.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
