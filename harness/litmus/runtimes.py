"""Language runtimes.

The held-out grading mechanism is language-agnostic: copy a workspace, let an
agent edit it, freeze, run a suite the agent never saw. Only two things are
language-specific - how you run the tests and how you read the result - so those
are the only things a runtime has to provide. Everything else in the sandbox is
shared.

Python uses pytest with a JUnit XML report. JavaScript uses Node's built-in test
runner (`node --test`, no jest or vitest to install) and parses its TAP output.
Adding a third language is a third Runtime, nothing more.
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .models import SuiteResult, TestCaseResult


class Runtime(Protocol):
    # Files that let a patch change how the *runner* behaves rather than the
    # code - neutralised before the held-out suite runs.
    quarantine: tuple[str, ...]

    def prepare(self, root: Path) -> None:
        """Anything that must exist before a suite runs (e.g. a config file)."""

    def run(
        self, root: Path, test_file: str, suite: str, timeout_s: int, results_dir: Path, env: dict
    ) -> SuiteResult: ...


def _timed(cmd: list[str], root: Path, timeout_s: int, env: dict) -> tuple[str, float, bool]:
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd, cwd=root, env=env, capture_output=True, text=True, timeout=timeout_s
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        return output, time.perf_counter() - started, False
    except subprocess.TimeoutExpired as exc:
        out = f"TIMEOUT after {timeout_s}s\n{exc.stdout or ''}{exc.stderr or ''}"
        return out, time.perf_counter() - started, True


# ---------------------------------------------------------------- Python


class PytestRuntime:
    quarantine = ("conftest.py", "sitecustomize.py", "usercustomize.py")
    _INI = "_litmus_pytest.ini"

    def prepare(self, root: Path) -> None:
        # A minimal config so any ini the agent wrote is ignored.
        (root / self._INI).write_text("[pytest]\naddopts =\n", encoding="utf-8")

    def run(self, root, test_file, suite, timeout_s, results_dir, env) -> SuiteResult:
        self.prepare(root)
        xml_path = results_dir / f"{suite}.xml"
        xml_path.unlink(missing_ok=True)

        cmd = [
            sys.executable, "-m", "pytest", test_file,
            "-q", "--tb=line", "-p", "no:cacheprovider",
            "-c", self._INI, f"--junit-xml={xml_path}",
        ]
        output, duration, timed_out = _timed(cmd, root, timeout_s, env)

        result = _parse_junit(xml_path, suite)
        result.duration_s = duration
        result.timed_out = timed_out
        result.output_tail = output[-2000:]
        if timed_out or not xml_path.exists():
            result.collection_error = True
        return result


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
            child, status = case.find("failure"), "failed"
        elif case.find("error") is not None:
            child, status = case.find("error"), "error"
        elif case.find("skipped") is not None:
            child, status = case.find("skipped"), "skipped"
        else:
            child, status = None, "passed"
        message = (child.get("message", "") if child is not None else "")[:400]
        result.cases.append(TestCaseResult(name=label, status=status, message=message))

    _tally(result)
    return result


# ------------------------------------------------------------ JavaScript


class NodeRuntime:
    # `node --test` reads no per-directory config, so there is no runner file an
    # agent could inject to change its behaviour. Nothing to quarantine.
    quarantine: tuple[str, ...] = ()

    def prepare(self, root: Path) -> None:
        return

    def run(self, root, test_file, suite, timeout_s, results_dir, env) -> SuiteResult:
        cmd = ["node", "--test", "--test-reporter=tap", test_file]
        output, duration, timed_out = _timed(cmd, root, timeout_s, env)

        result = _parse_tap(output, suite)
        result.duration_s = duration
        result.timed_out = timed_out
        result.output_tail = output[-2000:]
        # No test points parsed at all usually means the file failed to load.
        if timed_out or (result.total == 0 and "not ok" not in output):
            result.collection_error = result.total == 0 or timed_out
        return result


# Top-level TAP points only: "ok 1 - name" / "not ok 2 - name". Nested subtests
# are indented, so an anchored pattern counts each test once.
_TAP_LINE = re.compile(r"^(not ok|ok)\s+\d+\s+-\s+(.*?)(?:\s+#\s+(\w+))?\s*$")


def _parse_tap(output: str, suite: str) -> SuiteResult:
    result = SuiteResult(suite=suite)
    for line in output.splitlines():
        match = _TAP_LINE.match(line)
        if not match:
            continue
        ok, name, directive = match.groups()
        if directive and directive.upper() in ("SKIP", "TODO"):
            status = "skipped"
        elif ok == "ok":
            status = "passed"
        else:
            status = "failed"
        result.cases.append(TestCaseResult(name=name.strip(), status=status))
    _tally(result)
    return result


def _tally(result: SuiteResult) -> None:
    result.total = len(result.cases)
    result.failed = sum(1 for c in result.cases if c.status == "failed")
    result.errored = sum(1 for c in result.cases if c.status == "error")
    result.skipped = sum(1 for c in result.cases if c.status == "skipped")
    result.passed = result.total - result.failed - result.errored - result.skipped


# ------------------------------------------------------------ registry


@dataclass(frozen=True)
class Language:
    name: str
    public_tests: str
    hidden_tests: str
    runtime: Runtime


LANGUAGES: dict[str, Language] = {
    "python": Language("python", "tests_public.py", "tests_hidden.py", PytestRuntime()),
    "javascript": Language("javascript", "tests_public.js", "tests_hidden.js", NodeRuntime()),
}


def language_for(name: str) -> Language:
    key = (name or "python").lower()
    if key not in LANGUAGES:
        raise ValueError(f"unknown language {name!r}; expected one of {sorted(LANGUAGES)}")
    return LANGUAGES[key]
