#!/usr/bin/env python3
"""Copy the Ramp Kit overlay into a huggingface/diffusers checkout.

Does NOT replace the library's AGENTS.md / .ai/ — those stay upstream.
Adds Cursor rules, the gate hook, MCP launcher, and Cloud environment install
that clones this kit as `ramp-kit/` at VM boot.

Usage:
  python3 tools/attach_library.py --target /path/to/diffusers
  python3 tools/attach_library.py --in-place   # when cwd (or parent) is the library
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent


def _is_library(root: Path) -> bool:
    return (root / "src" / "diffusers" / "schedulers").is_dir()


def copy_overlay(target: Path) -> None:
    target = target.resolve()
    if not _is_library(target):
        sys.exit(f"not a diffusers checkout: {target}")

    cursor = target / ".cursor"
    cursor.mkdir(exist_ok=True)
    overlay = KIT / "overlay"

    # Commands / skills / hooks / rules from the kit (generated rules included).
    for rel in (
        "commands",
        "skills",
        "hooks",
        "rules",
    ):
        src, dst = KIT / ".cursor" / rel, cursor / rel
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)

    shutil.copy2(overlay / "mcp.json", cursor / "mcp.json")
    shutil.copy2(overlay / "mcp.optional.json", cursor / "mcp.optional.json")
    for name in ("hooks.json", "mcp-diffusers-docs.py", "mcp-diffusers-docs.sh"):
        src = KIT / ".cursor" / name
        if src.exists():
            shutil.copy2(src, cursor / name)

    shutil.copy2(overlay / "environment.json", cursor / "environment.json")
    shutil.copy2(overlay / "cursorignore", target / ".cursorignore")
    shutil.copy2(overlay / "OVERLAY.md", target / "OVERLAY.md")

    # File-scoped overlay CI. Do not delete inherited Hugging Face workflows.
    wf_dir = target / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(overlay / "ramp-kit-overlay.yml", wf_dir / "ramp-kit-overlay.yml")
    scripts = target / ".github" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(KIT / "tools" / "overlay_pr_gate.py", scripts / "overlay_pr_gate.py")

    gi = target / ".gitignore"
    text = gi.read_text(encoding="utf-8") if gi.exists() else ""
    if "\n.cursor\n" in text or text.endswith("\n.cursor"):
        text = text.replace("# Cursor\n.cursor\n", "# Cursor — upstream ignored this; overlay tracks .cursor (OVERLAY.md)\n")
        text = text.replace("\n.cursor\n", "\n")
        gi.write_text(text, encoding="utf-8")
        text = gi.read_text(encoding="utf-8")
    if "ramp-kit/" not in text.splitlines():
        with gi.open("a", encoding="utf-8") as fh:
            fh.write("\n# Ramp Kit overlay clone (see OVERLAY.md)\nramp-kit/\n")

    # Library-specific command tweaks (KIT=ramp-kit).
    scaffold = overlay / "scaffold.md"
    search = overlay / "search-docs.md"
    if scaffold.exists():
        (cursor / "commands" / "scaffold.md").write_text(scaffold.read_text(encoding="utf-8"))
    if search.exists():
        (cursor / "commands" / "search-docs.md").write_text(search.read_text(encoding="utf-8"))
        skill = cursor / "skills" / "search-docs" / "SKILL.md"
        if skill.parent.is_dir():
            shutil.copy2(overlay / "search-docs.skill.md", skill)

    print(f"overlay attached at {target}")
    print("  Cloud Agent: launch ON this fork (main), install clones ramp-kit/")
    print("  Default MCP is empty; opt-in servers: .cursor/mcp.optional.json")
    print("  Fork PRs: draft, title [fork demo — not for upstream]")
    print("  Overlay CI: .github/workflows/ramp-kit-overlay.yml (file-scoped, never --all)")
    print("  Do not overwrite upstream AGENTS.md / .ai/; do not delete HF workflows")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=Path, help="path to alex-16moro/diffusers checkout")
    ap.add_argument("--in-place", action="store_true", help="detect library from cwd/parent")
    args = ap.parse_args(argv)
    if args.target:
        copy_overlay(args.target)
        return 0
    if args.in_place:
        cwd = Path.cwd()
        for cand in (cwd, cwd.parent):
            if _is_library(cand):
                copy_overlay(cand)
                return 0
        sys.exit(f"no diffusers checkout at {cwd} or parent")
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
