"""Pack self-validation.

A benchmark is only as trustworthy as its tasks, so every pack must satisfy
four invariants before it is allowed into a run:

1. The shipped buggy workspace fails the public suite - otherwise there is
   nothing for the agent to do.
2. It also fails the held-out suite - otherwise the bug is not observable and
   a "gamed" verdict would be meaningless.
3. The reference implementation passes the public suite.
4. The reference implementation passes the held-out suite - this is what makes
   a "gamed" verdict fair. The task is provably solvable without cheating.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .models import TaskPack
from .sandbox import Sandbox

VALIDATION_TIMEOUT_S = 180


def _describe(suite) -> str:
    if suite.collection_error:
        return f"could not run ({suite.output_tail.strip()[-200:]})"
    return f"{suite.passed}/{suite.total} passed, {suite.failed} failed, {suite.skipped} skipped"


def validate_pack(pack: TaskPack) -> list[str]:
    """Return a list of problems. Empty means the pack is sound."""
    problems: list[str] = []

    # --- invariant 1 and 2: the shipped bug must be real and observable ---
    root = Path(tempfile.mkdtemp(prefix=f"litmus-val-buggy-{pack.id}-"))
    sandbox = Sandbox(pack, root, timeout_s=VALIDATION_TIMEOUT_S)
    try:
        sandbox.materialize()
        sandbox.freeze()
        public = sandbox.run_public_tests()
        hidden = sandbox.run_hidden_tests()

        if public.collection_error:
            problems.append(f"public suite does not run against the buggy workspace: {_describe(public)}")
        elif public.all_passed:
            problems.append("buggy workspace already passes the public suite - the agent has nothing to fix")

        if hidden.collection_error:
            problems.append(f"held-out suite does not run against the buggy workspace: {_describe(hidden)}")
        elif hidden.all_passed:
            problems.append("buggy workspace passes the held-out suite - the seeded bug is not observable")
    finally:
        sandbox.cleanup()

    # --- invariant 3 and 4: the task must be solvable honestly ---
    root = Path(tempfile.mkdtemp(prefix=f"litmus-val-ref-{pack.id}-"))
    sandbox = Sandbox(pack, root, timeout_s=VALIDATION_TIMEOUT_S)
    try:
        sandbox.materialize()
        for source in pack.reference_dir.rglob("*"):
            if source.is_file():
                target = sandbox.root / source.relative_to(pack.reference_dir)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
        sandbox.freeze()
        public = sandbox.run_public_tests()
        hidden = sandbox.run_hidden_tests()

        if not public.all_passed:
            problems.append(f"reference implementation fails the public suite: {_describe(public)}")
        if not hidden.all_passed:
            problems.append(f"reference implementation fails the held-out suite: {_describe(hidden)}")
    finally:
        sandbox.cleanup()

    return problems
