"""Codex CLI as an agent under test.

Unlike the API providers, Codex is not a chat endpoint we drive turn by turn -
it is a complete agent with its own planning and tool loop. So it does not
implement `Conversation`; it gets handed the sandbox directory and told to fix
the bug, and Litmus grades whatever it leaves behind.

The integrity guarantees are unchanged, and in fact rest on the same
structural fact as everywhere else: the held-out suite is not on disk while the
agent is working, so `--cd sandbox` cannot reach it. Codex runs under its own
`workspace-write` sandbox as well, which confines writes to that directory.

Auth comes from the ChatGPT sign-in the CLI already holds, so this works on the
free tier with no API key.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from .agents import NEUTRAL_PROMPT, PROMPTS, REVIEW_PROMPT, AgentOutcome, _current_patch
from .models import TaskPack, TraceStep
from .sandbox import Sandbox

CODEX_TIMEOUT_S = 420
CONFIGS = {"iterative", "reviewed", "pressured", "guided", "adversarial"}


class CodexUnavailable(RuntimeError):
    """The CLI is missing or not signed in."""


def codex_command() -> list[str]:
    """Resolve the CLI, preferring the .cmd shim over .ps1 on Windows."""
    found = shutil.which("codex")
    if not found:
        raise CodexUnavailable(
            "codex CLI not found on PATH - install with: npm install -g @openai/codex"
        )
    if found.lower().endswith(".ps1"):
        shim = Path(found).with_suffix(".cmd")
        if shim.exists():
            return [str(shim)]
    return [found]


def _parse_trace(jsonl: str, start_index: int = 0) -> list[TraceStep]:
    """Turn the Codex event stream into ordered trace steps.

    Each `item.completed` carries the action the agent just finished. The shape
    varies by item type, so this reads defensively and falls back to the type
    name rather than dropping the step.
    """
    steps: list[TraceStep] = []
    for line in jsonl.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "item.completed":
            continue

        item = event.get("item") or {}
        item_type = str(item.get("type") or item.get("item_type") or "item")

        detail = ""
        kind = "other"
        if "command" in item:
            command = str(item.get("command") or "")
            detail = command[:160]
            kind = "test" if "pytest" in command else "read"
        elif "patch" in item_type or "file_change" in item_type:
            kind = "write"
            changes = item.get("changes") or item.get("files") or []
            names = [str(c.get("path", c)) if isinstance(c, dict) else str(c) for c in changes]
            detail = ", ".join(names)[:160] or "applied a patch"
        elif "message" in item_type or "text" in item:
            kind = "message"
            detail = str(item.get("text") or "").strip().splitlines()[:1]
            detail = (detail[0] if detail else "")[:160]
        else:
            detail = item_type

        steps.append(
            TraceStep(
                index=start_index + len(steps) + 1,
                kind=kind,
                detail=detail or item_type,
                result=str(item.get("status") or ""),
            )
        )
    return steps


def _count_turns(jsonl: str) -> int:
    """Count agent actions from the event stream.

    Codex emits `thread.started`, `turn.started`, `item.started`,
    `item.completed`, `turn.completed`. One `codex exec` is a single `turn`
    however much work happens inside it, so counting turns would always report
    1 and say nothing. `item.completed` is the closer analogue to a turn in the
    API providers: one model action - a message, a command, a patch.
    """
    items = 0
    turns = 0
    for line in jsonl.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = str(event.get("type", ""))
        if kind == "item.completed":
            items += 1
        elif kind == "turn.completed":
            turns += 1
    return items or turns


class CodexCliAgent:
    """Runs `codex exec` against the sandbox.

    config:
      iterative - one Codex run; it plans, edits and reruns tests on its own
      reviewed  - the same, then a second run forced to critique its own diff
    """

    def __init__(
        self,
        config: str = "iterative",
        model: str | None = None,
        timeout_s: int = CODEX_TIMEOUT_S,
        unsandboxed: bool = False,
    ):
        if config not in CONFIGS:
            raise ValueError(
                f"codex:{config} is not available. The CLI always runs its own tool "
                f"loop, so there is no honest 'oneshot' mode. Use one of {sorted(CONFIGS)}."
            )
        # `reviewed` is the neutral brief plus a self-critique pass; the others
        # differ only in how the task is framed.
        self.config = config
        self.model = model or ""
        self.timeout_s = timeout_s
        self.unsandboxed = unsandboxed
        self.name = f"codex:{config}"

    def solve(self, sandbox: Sandbox, pack: TaskPack) -> AgentOutcome:
        if not self.unsandboxed:
            return AgentOutcome(
                turns=0,
                error=(
                    "codex needs write access to the workspace, and on this platform the "
                    "CLI reports sandbox: read-only for every --sandbox value. The only "
                    "way through is --dangerously-bypass-approvals-and-sandbox, which "
                    "turns off OS-level confinement. Re-run with --allow-codex-unsandboxed "
                    "to accept that; Litmus still confines Codex to a throwaway temp "
                    "directory via --cd and deletes it afterwards."
                ),
            )

        try:
            base = codex_command()
        except CodexUnavailable as exc:
            return AgentOutcome(turns=0, error=str(exc))

        trace: list[TraceStep] = []
        turns, error, steps = self._exec(base, sandbox, self._brief(sandbox, pack), trace)
        trace.extend(steps)

        if self.config == "reviewed" and error is None:
            patch = _current_patch(sandbox) or "(no changes)"
            trace.append(
                TraceStep(index=len(trace) + 1, kind="message", detail="self-review turn")
            )
            extra, error, more = self._exec(
                base, sandbox, REVIEW_PROMPT.format(patch=patch), trace
            )
            trace.extend(more)
            turns += extra

        return AgentOutcome(turns=turns, error=error, trace=trace)

    def _brief(self, sandbox: Sandbox, pack: TaskPack) -> str:
        listing = "\n".join(f"- {f}" for f in sandbox.list_files())
        if pack.language == "javascript":
            how = f"Run `node --test {sandbox.public_test_name}`"
        else:
            how = f"Run {sandbox.public_test_name} with pytest"
        return (
            f"{PROMPTS.get(self.config, NEUTRAL_PROMPT)}\n\n"
            f"# Bug report\n\n{pack.bug_report}\n\n"
            f"# Files in the workspace\n{listing}\n\n"
            f"The entry point is {pack.entrypoint}. {how} to check your work, then stop."
        )

    def _exec(
        self, base: list[str], sandbox: Sandbox, prompt: str, so_far: list[TraceStep]
    ) -> tuple[int, str | None, list[TraceStep]]:
        # Every option goes before the positional, and the prompt is fed over
        # stdin as "-". Passing a multi-line prompt as argv made clap stop
        # parsing the flags that follow it.
        cmd = base + [
            "exec",
            "--cd", str(sandbox.root),
            # Every --sandbox value still reports read-only on Windows, so this
            # is the only mode that can actually apply a patch. The workspace is
            # a temp copy that Litmus creates and deletes.
            "--dangerously-bypass-approvals-and-sandbox",
            "--skip-git-repo-check",   # the sandbox is a bare directory
            "--ephemeral",             # leave no session files behind
            "--ignore-user-config",    # reproducible across machines
            "--color", "never",
            "--json",
        ]
        if self.model:
            cmd += ["--model", self.model]
        cmd.append("-")

        try:
            proc = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return 0, f"codex exec timed out after {self.timeout_s}s", []
        except OSError as exc:
            return 0, f"could not launch codex: {exc}", []

        stdout = proc.stdout or ""
        turns = _count_turns(stdout)
        steps = _parse_trace(stdout, start_index=len(so_far))

        if proc.returncode != 0:
            tail = ((proc.stderr or "") + stdout).strip()[-400:]
            return turns, f"codex exec exited {proc.returncode}: {tail}", steps
        return turns, None, steps


def preflight() -> tuple[bool, str]:
    """Check the CLI is present and signed in before a long run starts."""
    try:
        base = codex_command()
    except CodexUnavailable as exc:
        return False, str(exc)

    try:
        proc = subprocess.run(
            base + ["--version"], capture_output=True, text=True, timeout=60
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return False, f"codex is installed but did not respond: {exc}"

    if proc.returncode != 0:
        return False, "codex --version failed; try running `codex` once to sign in"
    return True, (proc.stdout or "").strip()
