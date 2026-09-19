#!/usr/bin/env python3
"""Locate the overlay kit vs a real huggingface/diffusers checkout.

The kit (`diffuser_agent`) can run standalone (stand-in src/) or as
`ramp-kit/` nested inside a library clone. Callers should not assume cwd.
"""
from __future__ import annotations

import os
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent
BUNDLED_DOCS = KIT_ROOT / "knowledge" / "diffusers-docs"


def _is_library(root: Path) -> bool:
    return (root / "docs" / "source" / "en").is_dir() and (
        root / "src" / "diffusers" / "schedulers"
    ).is_dir()


def resolve_library_root() -> Path:
    """Directory that contains src/diffusers (fork or kit stand-in)."""
    env = os.environ.get("DIFFUSERS_ROOT")
    if env:
        p = Path(env).expanduser()
        if p.exists():
            return p.resolve()
    cwd = Path.cwd().resolve()
    if _is_library(cwd):
        return cwd
    if _is_library(KIT_ROOT):
        return KIT_ROOT
    parent = KIT_ROOT.parent
    if _is_library(parent):
        return parent
    for cand in (cwd / "diffusers", KIT_ROOT / "diffusers", parent / "diffusers", Path("/workspace")):
        if _is_library(cand):
            return cand.resolve()
    return KIT_ROOT


def resolve_docs_root() -> tuple[Path, str]:
    """Prefer the library checkout's docs; fall back to the bundled snapshot."""
    env = os.environ.get("DIFFUSERS_DOCS_ROOT")
    if env:
        p = Path(env).expanduser()
        if p.exists():
            return p.resolve(), "configured checkout ($DIFFUSERS_DOCS_ROOT)"
    lib = resolve_library_root()
    docs = lib / "docs" / "source" / "en"
    if docs.is_dir():
        return docs, f"diffusers checkout ({lib})"
    if BUNDLED_DOCS.is_dir():
        return BUNDLED_DOCS, "bundled snapshot (offline fallback — may lag upstream)"
    return BUNDLED_DOCS, "bundled snapshot (offline fallback — may lag upstream)"


def kit_bin(rel: str) -> Path:
    """A file inside the overlay kit (templates, gate, MCP server)."""
    return KIT_ROOT / rel
