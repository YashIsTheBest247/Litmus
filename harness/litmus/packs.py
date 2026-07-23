"""Loading task packs off disk.

A pack looks like this:

    packs/p001-example/
      meta.yaml
      workspace/          <- copied into the sandbox; the agent sees only this
        solution.py
        tests_public.py
      hidden/
        tests_hidden.py   <- injected only after the patch is frozen
      reference/
        solution.py       <- correct implementation, used to validate the pack
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import TaskPack
from .runtimes import LANGUAGES

REQUIRED_META_FIELDS = ("id", "title", "category", "difficulty", "entrypoint")


class PackError(Exception):
    """Raised when a pack is structurally invalid and cannot even be loaded."""


def load_pack(pack_dir: Path) -> TaskPack:
    meta_path = pack_dir / "meta.yaml"
    if not meta_path.exists():
        raise PackError(f"{pack_dir.name}: missing meta.yaml")

    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    missing = [f for f in REQUIRED_META_FIELDS if not meta.get(f)]
    if missing:
        raise PackError(f"{pack_dir.name}: meta.yaml missing {', '.join(missing)}")

    if meta["id"] != pack_dir.name:
        raise PackError(
            f"{pack_dir.name}: meta.yaml id is {meta['id']!r}, must match directory name"
        )

    language = str(meta.get("language", "python")).lower()
    if language not in LANGUAGES:
        raise PackError(
            f"{pack_dir.name}: unknown language {language!r}; expected one of {sorted(LANGUAGES)}"
        )

    pack = TaskPack(
        id=meta["id"],
        title=meta["title"],
        category=meta["category"],
        difficulty=meta["difficulty"],
        entrypoint=meta["entrypoint"],
        cheat_temptation=meta.get("cheat_temptation", "unknown"),
        bug_report=(meta.get("bug_report") or "").strip(),
        root=pack_dir,
        language=language,
    )

    for required in (pack.workspace_dir, pack.hidden_dir, pack.reference_dir):
        if not required.is_dir():
            raise PackError(f"{pack.id}: missing {required.name}/ directory")
    for required_file in (pack.public_tests, pack.hidden_tests):
        if not required_file.exists():
            raise PackError(f"{pack.id}: missing {required_file.name}")
    if not (pack.workspace_dir / pack.entrypoint).exists():
        raise PackError(f"{pack.id}: entrypoint {pack.entrypoint} not in workspace/")

    return pack


def load_all(packs_root: Path) -> list[TaskPack]:
    """Load every pack under packs_root, sorted by id for stable run ordering."""
    if not packs_root.is_dir():
        raise PackError(f"packs directory not found: {packs_root}")

    packs = [
        load_pack(child)
        for child in sorted(packs_root.iterdir())
        if child.is_dir() and not child.name.startswith((".", "_"))
    ]
    if not packs:
        raise PackError(f"no packs found under {packs_root}")
    return packs
