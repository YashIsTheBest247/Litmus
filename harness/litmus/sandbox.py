"""The sandbox the agent works in, and the only place tests are executed.

Two integrity rules drive the design, and both are enforced structurally rather
than by asking the agent nicely:

1. The held-out suite never exists on disk inside the sandbox while the agent
   is working. It is copied in after `freeze()`, and removed again afterwards.
2. Anything the agent could write that would change how pytest *itself*
   behaves - conftest.py, sitecustomize.py, an ini file - is neutralised before
   the held-out suite runs. Otherwise a patch could pass the hidden tests by
   sabotaging the runner instead of fixing the bug.
"""

from __future__ import annotations

import difflib
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from .models import SuiteResult, TaskPack, TestCaseResult

DEFAULT_TIMEOUT_S = 60
HIDDEN_TEST_NAME = "tests_hidden.py"
LITMUS_INI = "_litmus_pytest.ini"

# Never shown to the agent, never diffed.
IGNORED_DIRS = {"__pycache__", ".pytest_cache", ".git"}
IGNORED_NAMES = {LITMUS_INI}
IGNORED_SUFFIXES = {".pyc", ".pyo"}

# Files that let a patch change pytest's behaviour instead of the code's.
QUARANTINED_FOR_HIDDEN = ("conftest.py", "sitecustomize.py", "usercustomize.py")

# Stripped from the subprocess environment so that patched code executing
# inside the sandbox can never read the harness operator's credentials.
SECRET_ENV_PREFIXES = ("OPENAI", "ANTHROPIC", "AWS", "AZURE", "GOOGLE", "HF_", "GITHUB")


class SandboxViolation(Exception):
    """The agent tried to reach outside its workspace, or read the held-out suite."""


def _is_ignored(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in IGNORED_DIRS for part in rel.parts):
        return True
    return path.name in IGNORED_NAMES or path.suffix in IGNORED_SUFFIXES


def _clean_env() -> dict[str, str]:
    env = {
        k: v
        for k, v in os.environ.items()
        if not any(k.upper().startswith(p) for p in SECRET_ENV_PREFIXES)
    }
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


class Sandbox:
    """An isolated copy of one pack's workspace."""

    def __init__(self, pack: TaskPack, run_root: Path, timeout_s: int = DEFAULT_TIMEOUT_S):
        self.pack = pack
        self.run_root = run_root
        self.root = run_root / "workspace"
        self.results_dir = run_root / "_results"  # outside the sandbox, agent cannot touch it
        self.timeout_s = timeout_s
        self.frozen = False
        self._original: dict[str, str] = {}

    # ---------------------------------------------------------------- setup

    def materialize(self) -> None:
        """Copy the pack workspace in and remember its exact starting state."""
        if self.root.exists():
            shutil.rmtree(self.root)
        shutil.copytree(self.pack.workspace_dir, self.root)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self._original = self._snapshot()

    def _snapshot(self) -> dict[str, str]:
        snap: dict[str, str] = {}
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or _is_ignored(path, self.root):
                continue
            rel = path.relative_to(self.root).as_posix()
            try:
                snap[rel] = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                snap[rel] = "<binary or unreadable>"
        return snap

    # ------------------------------------------------------- agent file API

    def _resolve(self, rel_path: str) -> Path:
        candidate = (self.root / rel_path).resolve()
        root = self.root.resolve()
        if candidate != root and root not in candidate.parents:
            raise SandboxViolation(f"path escapes the sandbox: {rel_path}")
        if candidate.name == HIDDEN_TEST_NAME:
            raise SandboxViolation("the held-out suite is not readable")
        return candidate

    def list_files(self) -> list[str]:
        return [
            p.relative_to(self.root).as_posix()
            for p in sorted(self.root.rglob("*"))
            if p.is_file() and not _is_ignored(p, self.root)
        ]

    def read_file(self, rel_path: str) -> str:
        path = self._resolve(rel_path)
        if not path.is_file():
            raise FileNotFoundError(rel_path)
        return path.read_text(encoding="utf-8")

    def write_file(self, rel_path: str, content: str) -> None:
        if self.frozen:
            raise SandboxViolation("the patch is frozen; no further writes accepted")
        path = self._resolve(rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    # ------------------------------------------------------------- running

    def _write_ini(self) -> None:
        """A minimal pytest config so any ini the agent wrote is ignored."""
        (self.root / LITMUS_INI).write_text(
            "[pytest]\naddopts =\n", encoding="utf-8"
        )

    def _run_pytest(self, test_file: str, suite: str) -> SuiteResult:
        self._write_ini()
        xml_path = self.results_dir / f"{suite}.xml"
        if xml_path.exists():
            xml_path.unlink()

        cmd = [
            sys.executable, "-m", "pytest", test_file,
            "-q", "--tb=line",
            "-p", "no:cacheprovider",
            "-c", LITMUS_INI,
            f"--junit-xml={xml_path}",
        ]

        started = time.perf_counter()
        timed_out = False
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.root,
                env=_clean_env(),
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
            )
            output = (proc.stdout or "") + (proc.stderr or "")
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            output = f"TIMEOUT after {self.timeout_s}s\n{exc.stdout or ''}{exc.stderr or ''}"

        duration = time.perf_counter() - started
        result = _parse_junit(xml_path, suite)
        result.duration_s = duration
        result.timed_out = timed_out
        result.output_tail = output[-2000:]
        if timed_out or not xml_path.exists():
            result.collection_error = True
        return result

    def run_public_tests(self) -> SuiteResult:
        """The suite the agent is allowed to iterate against."""
        return self._run_pytest("tests_public.py", "public")

    def run_hidden_tests(self) -> SuiteResult:
        """The held-out suite. Only callable once the patch is frozen."""
        if not self.frozen:
            raise SandboxViolation("cannot run the held-out suite before freeze()")

        quarantined: list[tuple[Path, Path]] = []
        for name in QUARANTINED_FOR_HIDDEN:
            original = self.root / name
            if original.exists():
                parked = self.run_root / f"_quarantined_{name}"
                shutil.move(str(original), str(parked))
                quarantined.append((original, parked))

        hidden_target = self.root / HIDDEN_TEST_NAME
        shutil.copyfile(self.pack.hidden_tests, hidden_target)
        try:
            return self._run_pytest(HIDDEN_TEST_NAME, "hidden")
        finally:
            hidden_target.unlink(missing_ok=True)
            for original, parked in quarantined:
                shutil.move(str(parked), str(original))

    # -------------------------------------------------------------- freeze

    def freeze(self) -> tuple[str, list[str], dict[str, str], dict[str, str]]:
        """Stop accepting writes and compute the patch.

        Returns (unified_diff, changed_files, original_snapshot, final_snapshot).
        """
        self.frozen = True
        final = self._snapshot()
        changed = sorted(
            set(self._original) ^ set(final)
            | {k for k in set(self._original) & set(final) if self._original[k] != final[k]}
        )

        chunks: list[str] = []
        for rel in changed:
            before = self._original.get(rel, "").splitlines(keepends=True)
            after = final.get(rel, "").splitlines(keepends=True)
            chunks.extend(
                difflib.unified_diff(
                    before, after, fromfile=f"a/{rel}", tofile=f"b/{rel}", n=3
                )
            )
        return "".join(chunks), changed, dict(self._original), final

    def cleanup(self) -> None:
        shutil.rmtree(self.run_root, ignore_errors=True)


def _parse_junit(xml_path: Path, suite: str) -> SuiteResult:
    result = SuiteResult(suite=suite)
    if not xml_path.exists():
        result.collection_error = True
        return result

    try:
        tree = ET.parse(xml_path)
    except ET.ParseError:
        result.collection_error = True
        return result

    root = tree.getroot()
    node = root if root.tag == "testsuite" else (root.find("testsuite") or root)

    for case in node.iter("testcase"):
        name = case.get("name", "<unnamed>")
        classname = case.get("classname", "")
        label = f"{classname}::{name}" if classname else name

        if case.find("failure") is not None:
            child = case.find("failure")
            status = "failed"
        elif case.find("error") is not None:
            child = case.find("error")
            status = "error"
        elif case.find("skipped") is not None:
            child = case.find("skipped")
            status = "skipped"
        else:
            child, status = None, "passed"

        message = (child.get("message", "") if child is not None else "")[:400]
        result.cases.append(TestCaseResult(name=label, status=status, message=message))

    result.total = len(result.cases)
    result.failed = sum(1 for c in result.cases if c.status == "failed")
    result.errored = sum(1 for c in result.cases if c.status == "error")
    result.skipped = sum(1 for c in result.cases if c.status == "skipped")
    result.passed = result.total - result.failed - result.errored - result.skipped
    return result
