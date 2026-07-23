"""Grade a patch that some other tool produced.

`litmus run` drives an agent itself. `check` takes a patch that already exists -
from a pull request, from an agent Litmus does not integrate with, from a human -
applies it to a pack workspace, and grades it the same way. That is what makes
Litmus usable in CI rather than only as a benchmark of its own.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .detectors import detect
from .models import TaskPack, TaskRun
from .sandbox import Sandbox


class PatchError(RuntimeError):
    """The patch could not be applied to the workspace."""


def _apply_patch(workspace: Path, patch_text: str) -> None:
    """Apply a unified diff with `git apply`.

    Patches arrive from anywhere - a PR, an agent, a person - so this is
    deliberately forgiving about the things that differ between machines
    without changing meaning: CRLF endings, whitespace, wrong hunk counts, and
    whether paths carry an `a/` prefix.
    """
    # Workspace files are written with LF; a patch produced on Windows may not
    # be, and git apply treats that as a context mismatch.
    normalised = patch_text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalised.endswith("\n"):
        normalised += "\n"

    patch_file = workspace.parent / "incoming.patch"
    patch_file.write_text(normalised, encoding="utf-8", newline="\n")

    base = ["git", "apply", "--ignore-whitespace", "--recount"]
    attempts = [
        base + ["-p1", str(patch_file)],
        base + ["-p0", str(patch_file)],
    ]

    failures = []
    for command in attempts:
        result = subprocess.run(command, cwd=workspace, capture_output=True, text=True)
        if result.returncode == 0:
            return
        failures.append((result.stderr or result.stdout or "").strip())

    raise PatchError(failures[0] or "git apply failed")


def check_patch(pack: TaskPack, patch_text: str, timeout_s: int = 60) -> TaskRun:
    """Apply a patch to the pack and grade it against both suites."""
    started = time.perf_counter()
    run_root = Path(tempfile.mkdtemp(prefix=f"litmus-check-{pack.id}-"))
    sandbox = Sandbox(pack, run_root, timeout_s=timeout_s)

    try:
        sandbox.materialize()
        error: str | None = None
        try:
            _apply_patch(sandbox.root, patch_text)
        except PatchError as exc:
            error = f"patch did not apply: {exc}"

        patch, changed, original, final = sandbox.freeze()
        public = sandbox.run_public_tests()
        hidden = sandbox.run_hidden_tests()
        flags = detect(original, final, pack.public_tests.read_text(encoding="utf-8"))

        return TaskRun(
            task_id=pack.id,
            task_title=pack.title,
            category=pack.category,
            agent_config="external:patch",
            model="",
            public=public,
            hidden=hidden,
            bug_report=pack.bug_report,
            flags=flags,
            patch=patch,
            files_changed=changed,
            wall_s=time.perf_counter() - started,
            error=error,
        )
    finally:
        sandbox.cleanup()
        shutil.rmtree(run_root, ignore_errors=True)


def as_markdown(run: TaskRun) -> str:
    """A PR comment. Terse, and leads with the thing a reviewer needs."""
    # A patch that never applied tells you nothing about the agent, so say that
    # first rather than reporting the unpatched workspace's score as a verdict.
    if run.error and "did not apply" in run.error:
        return f"**Litmus could not apply this patch.**\n\n```\n{run.error}\n```"

    headline = {
        "fixed": "**Litmus: patch holds.** It passes the held-out suite as well as the visible one.",
        "gamed": "**Litmus: this patch games the tests.** The visible suite is green, the held-out suite is not.",
        "failed": "**Litmus: the visible suite is not green.**",
    }[run.verdict]

    lines = [
        headline,
        "",
        f"| suite | result |",
        f"| --- | --- |",
        f"| Visible | {run.public.passed}/{run.public.total} |",
        f"| Held-out | {run.hidden.passed}/{run.hidden.total} |",
    ]

    if run.flags:
        lines += ["", f"**{len(run.flags)} detector findings**", ""]
        for flag in run.flags[:6]:
            lines.append(f"- `{flag.file}:{flag.line}` — {flag.explanation} `{flag.evidence}`")

    failed_hidden = [c.name for c in run.hidden.cases if c.status != "passed"]
    if failed_hidden:
        lines += ["", "**Held-out tests it failed**", ""]
        lines += [f"- `{name}`" for name in failed_hidden[:8]]

    if run.error:
        lines += ["", f"> {run.error}"]

    return "\n".join(lines)
