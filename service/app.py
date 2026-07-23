"""Live-run service.

Lets the deployed site actually execute the harness on demand instead of only
rendering a stored report. Everything here is real: the workspace is
materialised, the patch is applied, the patch is frozen, pytest runs both
suites, and the detectors read the resulting diff.

Security note, because this matters more than the feature does:

Executing a patch means executing code. Accepting arbitrary patches from the
open internet would be remote code execution as a service, so by default this
only runs candidate patches that ship in the repository - the honest fix, and
several deliberate cheats. Set LITMUS_ALLOW_CUSTOM_PATCH=1 to accept pasted
patches, and only do that somewhere you control and do not mind losing.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from litmus.agents import MockAgent
from litmus.check import check_patch
from litmus.packs import PackError, load_all
from litmus.runner import run_task
from service.telegram import configured as telegram_configured
from service.telegram import handle_update, load_published_report
from service.telegram import secret as telegram_secret

REPO_ROOT = Path(__file__).resolve().parents[1]

# Load .env before anything reads the environment, so the service behaves the
# same locally as it does with dashboard-configured variables in production.
try:
    from litmus.cli import load_env_file

    load_env_file(REPO_ROOT / ".env")
except Exception:  # pragma: no cover - never block startup on this
    pass

PACKS_ROOT = Path(os.environ.get("LITMUS_PACKS", REPO_ROOT / "packs"))
REPORT_PATH = Path(os.environ.get("LITMUS_REPORT", REPO_ROOT / "web" / "data" / "report.json"))
ALLOW_CUSTOM_PATCH = os.environ.get("LITMUS_ALLOW_CUSTOM_PATCH") == "1"
MAX_PATCH_BYTES = 20_000

# Human-facing descriptions of the candidate patches shipped with each pack.
CANDIDATE_LABELS = {
    "honest": ("The general fix", "Solves the underlying defect."),
    "cheat": (
        "Special-case the tested inputs",
        "Recognises the exact values the visible tests use.",
    ),
    "skipper": ("Silence the failing tests", "Adds skip markers instead of fixing anything."),
    "swallower": (
        "Swallow the failure",
        "Catches the error and returns a default, so nothing raises.",
    ),
}

app = FastAPI(title="Litmus live run", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("LITMUS_ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _packs():
    try:
        return load_all(PACKS_ROOT)
    except PackError as exc:  # pragma: no cover - configuration failure
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _find(pack_id: str):
    pack = next((p for p in _packs() if p.id == pack_id), None)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"unknown pack: {pack_id}")
    return pack


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "packs": len(_packs()),
        "custom_patch": ALLOW_CUSTOM_PATCH,
        "telegram": telegram_configured(),
        "report": REPORT_PATH.exists(),
    }


@app.get("/api/packs")
def list_packs() -> dict:
    """Packs, their visible source, and the candidate patches you can run."""
    out = []
    for pack in _packs():
        candidates = []
        for path in sorted((pack.root / "mock").glob("*.py")):
            label, blurb = CANDIDATE_LABELS.get(
                path.stem, (path.stem.replace("_", " ").title(), "")
            )
            candidates.append({"id": path.stem, "label": label, "description": blurb})

        out.append(
            {
                "id": pack.id,
                "title": pack.title,
                "category": pack.category,
                "bug_report": pack.bug_report,
                "entrypoint": pack.entrypoint,
                "source": (pack.workspace_dir / pack.entrypoint).read_text(encoding="utf-8"),
                "public_tests": pack.public_tests.read_text(encoding="utf-8"),
                "hidden_test_count": pack.hidden_tests.read_text(encoding="utf-8").count("def test_"),
                "candidates": candidates,
            }
        )
    return {"packs": out}


class RunRequest(BaseModel):
    pack_id: str
    candidate: str = Field(default="honest")


@app.post("/api/run")
def run_candidate(request: RunRequest) -> dict:
    """Execute a shipped candidate patch through the full harness."""
    pack = _find(request.pack_id)

    available = {p.stem for p in (pack.root / "mock").glob("*.py")}
    if request.candidate not in available:
        raise HTTPException(
            status_code=400,
            detail=f"unknown candidate {request.candidate!r}; expected one of {sorted(available)}",
        )

    run = run_task(MockAgent(request.candidate), pack, model="candidate", timeout_s=60)
    return run.to_dict()


@app.get("/api/report.pdf")
def report_pdf():
    """The published report as a shareable PDF."""
    from fastapi.responses import Response

    from litmus.pdfreport import build_pdf

    report = load_published_report(REPORT_PATH)
    if not report:
        raise HTTPException(status_code=404, detail="no report has been published")

    return Response(
        content=build_pdf(report),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="litmus-report.pdf"'},
    )


@app.post("/api/telegram/webhook")
async def telegram_webhook(update: dict, request: Request):
    """Telegram calls this. Always answers 200 so it does not retry forever."""
    if not telegram_configured():
        raise HTTPException(status_code=404, detail="telegram is not configured")

    # Telegram echoes this header back on every call; without it the endpoint
    # is an open invitation to spoof updates.
    expected = telegram_secret()
    if expected:
        sent = request.headers.get("x-telegram-bot-api-secret-token", "")
        if sent != expected:
            raise HTTPException(status_code=403, detail="bad secret token")

    from litmus.pdfreport import build_pdf

    await handle_update(
        update,
        {
            "list_packs": lambda: list_packs()["packs"],
            "run_candidate": lambda pack_id, candidate: run_candidate(
                RunRequest(pack_id=pack_id, candidate=candidate)
            ),
            "load_report": lambda: load_published_report(REPORT_PATH),
            "build_pdf": build_pdf,
        },
    )
    return {"ok": True}


class PatchRequest(BaseModel):
    pack_id: str
    patch: str


@app.post("/api/check")
def check(request: PatchRequest) -> dict:
    """Grade a pasted patch. Disabled unless explicitly enabled."""
    if not ALLOW_CUSTOM_PATCH:
        raise HTTPException(
            status_code=403,
            detail="custom patches are disabled on this deployment; "
            "running arbitrary submitted code is not something a public service should do",
        )
    if len(request.patch.encode("utf-8")) > MAX_PATCH_BYTES:
        raise HTTPException(status_code=413, detail="patch too large")

    pack = _find(request.pack_id)
    return check_patch(pack, request.patch, timeout_s=60).to_dict()
