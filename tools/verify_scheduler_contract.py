#!/usr/bin/env python3
"""Re-verify scheduler contract rules against the library fork's reference source.

This is the automated version of the manual check: SCHED001/002/003 must still
match `scheduling_ddpm.py` and `scheduling_euler_discrete.py`. Docs that still
say `set_num_inference_steps` are stale; source wins.

Exit 0 = contract holds. Exit 1 = drift. Exit 2 = library not found
(unless --allow-missing, then 0 with a skip message).

Usage:
  python3 tools/verify_scheduler_contract.py
  python3 tools/verify_scheduler_contract.py --library /path/to/diffusers
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("verify_scheduler_contract needs PyYAML\n")
    sys.exit(2)

from library_paths import KIT_ROOT, resolve_library_root  # noqa: E402

REFERENCES = (
    "src/diffusers/schedulers/scheduling_ddpm.py",
    "src/diffusers/schedulers/scheduling_euler_discrete.py",
)
REQUIRED_BASES = {"SchedulerMixin", "ConfigMixin"}
REQUIRED_METHODS = {"set_timesteps", "step"}
STALE_METHOD = "set_num_inference_steps"


def _base_names(cls: ast.ClassDef) -> set[str]:
    names = set()
    for b in cls.bases:
        if isinstance(b, ast.Name):
            names.add(b.id)
        elif isinstance(b, ast.Attribute):
            names.add(b.attr)
    return names


def _methods(cls: ast.ClassDef) -> set[str]:
    return {
        n.name
        for n in cls.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _init_registered(cls: ast.ClassDef) -> bool:
    for n in cls.body:
        if isinstance(n, ast.FunctionDef) and n.name == "__init__":
            deco = set()
            for d in n.decorator_list:
                if isinstance(d, ast.Name):
                    deco.add(d.id)
                elif isinstance(d, ast.Attribute):
                    deco.add(d.attr)
            return "register_to_config" in deco
    return False


def _scheduler_classes(tree: ast.AST) -> list[ast.ClassDef]:
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name.endswith("Scheduler"):
            out.append(node)
    return out


def check_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    classes = _scheduler_classes(tree)
    if not classes:
        return [f"{path.name}: no *Scheduler class found"]
    problems = []
    for cls in classes:
        bases = _base_names(cls)
        missing_bases = REQUIRED_BASES - bases
        if missing_bases:
            problems.append(
                f"{path.name}: {cls.name} missing bases {sorted(missing_bases)}"
            )
        defined = _methods(cls)
        missing_m = REQUIRED_METHODS - defined
        if missing_m:
            problems.append(
                f"{path.name}: {cls.name} missing methods {sorted(missing_m)}"
            )
        if STALE_METHOD in defined and "set_timesteps" not in defined:
            problems.append(
                f"{path.name}: {cls.name} uses stale {STALE_METHOD} "
                f"without set_timesteps"
            )
        if not _init_registered(cls):
            problems.append(
                f"{path.name}: {cls.name}.__init__ lacks @register_to_config"
            )
    return problems


def registry_contract() -> tuple[set[str], set[str]]:
    data = yaml.safe_load((KIT_ROOT / "conventions" / "rules.yaml").read_text())
    methods = set(REQUIRED_METHODS)
    for r in data["rules"]:
        if r["id"] == "SCHED002":
            methods = set((r.get("params") or {}).get("required_methods") or methods)
    return REQUIRED_BASES, methods


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--library", type=Path, help="diffusers checkout (fork)")
    ap.add_argument(
        "--allow-missing",
        action="store_true",
        help="exit 0 if reference files are not present (kit-only CI)",
    )
    args = ap.parse_args(argv)

    lib = args.library.resolve() if args.library else resolve_library_root()
    files = [lib / rel for rel in REFERENCES]
    missing_files = [p for p in files if not p.is_file()]
    if missing_files:
        msg = (
            "scheduler contract re-verify: reference files not found at "
            f"{lib} ({[str(p) for p in missing_files]})"
        )
        if args.allow_missing:
            print(f"SKIP: {msg}")
            return 0
        # Kit stand-in has no DDPM/Euler sources; skip rather than false-red.
        if lib == KIT_ROOT:
            print(f"SKIP: {msg} (kit stand-in; attach the fork to enforce)")
            return 0
        sys.stderr.write(f"DRIFT: {msg}\n")
        return 1

    bases, methods = registry_contract()
    global REQUIRED_BASES, REQUIRED_METHODS
    REQUIRED_BASES, REQUIRED_METHODS = bases, methods

    problems: list[str] = []
    for p in files:
        problems.extend(check_file(p))

    if problems:
        sys.stderr.write("scheduler contract DRIFT vs fork reference source:\n")
        for line in problems:
            sys.stderr.write(f"  - {line}\n")
        sys.stderr.write(
            "SCHED001/002/003 no longer match scheduling_ddpm.py / "
            "scheduling_euler_discrete.py. Update conventions/rules.yaml "
            "from source (source wins over docs).\n"
        )
        return 1

    print(
        f"scheduler contract OK: {lib}\n"
        f"  files: {', '.join(p.name for p in files)}\n"
        f"  bases {sorted(REQUIRED_BASES)}; methods {sorted(REQUIRED_METHODS)}; "
        f"@register_to_config on __init__"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
