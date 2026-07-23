"""Telegram bot, served as a webhook off the existing FastAPI app.

Webhook rather than polling, deliberately: polling needs a process that never
sleeps, and the free hosting this runs on sleeps after fifteen minutes idle.
An incoming webhook wakes it instead, and Telegram retries if the first attempt
times out — so a sleeping service costs a few seconds, not the feature.

What it can do:
    /packs                     list the task packs
    /run <pack> <candidate>    execute a candidate patch and report the verdict
    /report                    the current integrity report as a PDF
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx

# Read lazily rather than at import. The service loads .env during startup, and
# module-level constants would be captured before that happens.
def token() -> str:
    return os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()


def secret() -> str:
    return os.environ.get("TELEGRAM_WEBHOOK_SECRET", "").strip()


def _api() -> str:
    return f"https://api.telegram.org/bot{token()}"

INTRO = (
    "*Litmus*\n\n"
    "I grade coding agents twice: once on tests they can read, once on tests "
    "they have never seen. The distance between those two scores is the "
    "integrity gap.\n\n"
    "`/packs` — the task packs\n"
    "`/run <pack> <candidate>` — execute a patch and see the verdict\n"
    "`/report` — the current report as a PDF"
)


def configured() -> bool:
    return bool(token())


async def _post(method: str, payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{_api()}/{method}", json=payload)
        try:
            return response.json()
        except Exception:
            return {"ok": False}


async def _send(chat_id: int, text: str) -> None:
    """Send Markdown, but fall back to plain text if Telegram rejects it.

    Detector evidence and task titles carry characters legacy Markdown treats
    as formatting - underscores in identifiers, asterisks in `2**attempt`. An
    unbalanced one makes Telegram reject the whole message with 400, so a
    verdict would silently never arrive. Plain text always gets through.
    """
    result = await _post(
        "sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    )
    if not result.get("ok"):
        stripped = text.replace("*", "").replace("`", "")
        await _post("sendMessage", {"chat_id": chat_id, "text": stripped})


async def _send_pdf(chat_id: int, data: bytes, filename: str, caption: str) -> None:
    async with httpx.AsyncClient(timeout=60) as client:
        await client.post(
            f"{_api()}/sendDocument",
            data={"chat_id": str(chat_id), "caption": caption},
            files={"document": (filename, data, "application/pdf")},
        )


def _format_run(run: dict[str, Any]) -> str:
    verdict = run["verdict"]
    mark = {
        "fixed": "held up",
        "gamed": "GAMED",
        "incomplete": "nearly - missed an edge case",
        "failed": "did not go green",
    }[verdict]

    lines = [
        f"*{run['task_title']}*",
        f"Verdict: *{mark}*",
        "",
        f"Visible suite:  {run['public']['passed']}/{run['public']['total']}",
        f"Held-out suite: {run['hidden']['passed']}/{run['hidden']['total']}",
    ]

    if verdict == "gamed":
        lines += ["", "_Any ordinary CI run would have called this green._"]

    if run.get("flags"):
        lines += ["", f"*{len(run['flags'])} detector findings*"]
        for flag in run["flags"][:3]:
            lines.append(f"`{flag['file']}:{flag['line']}` {flag['evidence'][:70]}")

    return "\n".join(lines)


async def handle_update(update: dict[str, Any], deps: dict[str, Any]) -> None:
    """Process one Telegram update. Never raises into the request handler."""
    message = update.get("message") or update.get("edited_message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    text = (message.get("text") or "").strip()
    if not chat_id or not text.startswith("/"):
        return

    parts = text.split()
    command = parts[0].split("@")[0].lower()
    args = parts[1:]

    try:
        if command in ("/start", "/help"):
            await _send(chat_id, INTRO)

        elif command == "/packs":
            packs = deps["list_packs"]()
            lines = ["*Task packs*", ""]
            for pack in packs:
                candidates = ", ".join(c["id"] for c in pack["candidates"]) or "none"
                lines.append(f"`{pack['id']}`\n{pack['title']}\ncandidates: {candidates}\n")
            await _send(chat_id, "\n".join(lines))

        elif command == "/run":
            if len(args) < 1:
                await _send(chat_id, "Usage: `/run <pack> <candidate>`  — see `/packs`")
                return
            pack_id, candidate = args[0], (args[1] if len(args) > 1 else "cheat")
            await _send(chat_id, f"Running `{candidate}` against `{pack_id}`…")
            run = deps["run_candidate"](pack_id, candidate)
            await _send(chat_id, _format_run(run))

        elif command == "/report":
            report = deps["load_report"]()
            if not report:
                await _send(chat_id, "No report has been published yet.")
                return
            await _send(chat_id, "Building the report…")
            pdf = deps["build_pdf"](report)
            await _send_pdf(
                chat_id, pdf, "litmus-report.pdf", "Litmus integrity report"
            )

        else:
            await _send(chat_id, "Unknown command. Try `/help`.")

    except Exception as exc:  # a bad command must not take the webhook down
        await _send(chat_id, f"That did not work: `{type(exc).__name__}: {exc}`"[:400])


def load_published_report(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
