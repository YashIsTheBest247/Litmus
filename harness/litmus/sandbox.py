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
from pathlib import Path

from .models import SuiteResult, TaskPack
from .runtimes import language_for

DEFAULT_TIMEOUT_S = 60

# Never shown to the agent, never diffed. Includes runner scratch files and
# language build artifacts across the supported runtimes.
IGNORED_DIRS = {"__pycache__", ".pytest_cache", ".git", "node_modules"}
IGNORED_NAMES = {"_litmus_pytest.ini"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}

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

        language = language_for(pack.language)
        self.runtime = language.runtime
        self.public_test_name = language.public_tests
        self.hidden_test_name = language.hidden_tests

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
        if candidate.name == self.hidden_test_name:
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

    def run_public_tests(self) -> SuiteResult:
        """The suite the agent is allowed to iterate against."""
        return self.runtime.run(
            self.root, self.public_test_name, "public", self.timeout_s,
            self.results_dir, _clean_env(),
        )

    def run_hidden_tests(self) -> SuiteResult:
        """The held-out suite. Only callable once the patch is frozen."""
        if not self.frozen:
            raise SandboxViolation("cannot run the held-out suite before freeze()")

        # Neutralise anything the agent wrote that could change the runner
        # itself rather than the code. The set is the runtime's business.
        quarantined: list[tuple[Path, Path]] = []
        for name in self.runtime.quarantine:
            original = self.root / name
            if original.exists():
                parked = self.run_root / f"_quarantined_{name}"
                shutil.move(str(original), str(parked))
                quarantined.append((original, parked))

        hidden_target = self.root / self.hidden_test_name
        shutil.copyfile(self.pack.hidden_tests, hidden_target)
        try:
            return self.runtime.run(
                self.root, self.hidden_test_name, "hidden", self.timeout_s,
                self.results_dir, _clean_env(),
            )
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
