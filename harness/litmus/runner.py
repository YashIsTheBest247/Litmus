"""Orchestration: one agent against one pack, and the batch version."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

from .agents import Agent
from .detectors import detect
from .models import SuiteResult, TaskPack, TaskRun
from .sandbox import Sandbox


def run_task(agent: Agent, pack: TaskPack, model: str = "", timeout_s: int = 60) -> TaskRun:
    """The full lifecycle: materialise, let the agent work, freeze, then grade.

    Order matters. `freeze()` happens before the held-out suite is copied in,
    so there is no window in which the agent could observe it.
    """
    started = time.perf_counter()
    run_root = Path(tempfile.mkdtemp(prefix=f"litmus-{pack.id}-"))
    sandbox = Sandbox(pack, run_root, timeout_s=timeout_s)

    error: str | None = None
    turns = 0
    try:
        sandbox.materialize()
        outcome = agent.solve(sandbox, pack)
        turns, error = outcome.turns, outcome.error

        patch, changed, original, final = sandbox.freeze()
        public = sandbox.run_public_tests()
        hidden = sandbox.run_hidden_tests()
        flags = detect(original, final, pack.public_tests.read_text(encoding="utf-8"))

        return TaskRun(
            task_id=pack.id,
            task_title=pack.title,
            category=pack.category,
            agent_config=agent.name,
            model=model,
            public=public,
            hidden=hidden,
            bug_report=pack.bug_report,
            flags=flags,
            patch=patch,
            files_changed=changed,
            turns=turns,
            wall_s=time.perf_counter() - started,
            error=error,
        )
    except Exception as exc:  # a harness failure must not be scored as a fix
        return TaskRun(
            task_id=pack.id,
            task_title=pack.title,
            category=pack.category,
            agent_config=agent.name,
            model=model,
            public=SuiteResult(suite="public", collection_error=True),
            hidden=SuiteResult(suite="hidden", collection_error=True),
            turns=turns,
            wall_s=time.perf_counter() - started,
            error=error or f"{type(exc).__name__}: {exc}",
        )
    finally:
        sandbox.cleanup()


def run_suite(
    agent: Agent, packs: list[TaskPack], model: str = "", timeout_s: int = 60, on_result=None
) -> list[TaskRun]:
    results: list[TaskRun] = []
    for pack in packs:
        result = run_task(agent, pack, model=model, timeout_s=timeout_s)
        results.append(result)
        if on_result:
            on_result(result)
    return results
