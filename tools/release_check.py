#!/usr/bin/env python3
"""Thin wrapper: BUILD-VERIFIED / PACKAGING-ELIGIBLE on a library checkout.

Invokes the library's own tests and `python -m build`. Does not publish,
tag, twine-upload, or run `make pre-release`. Not a new product — same
idea as overlay_pr_gate.py (invoke team tooling, report).

Run ONLY on a huggingface/diffusers checkout (the fork), never the kit
stand-in:

  python ramp-kit/tools/release_check.py --object PNDMLiteScheduler
  python ramp-kit/tools/release_check.py --json   # detect new export vs origin/main
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
VERDICT_PASS = "BUILD-VERIFIED / PACKAGING-ELIGIBLE"
VERDICT_FAIL = "NOT PACKAGING-ELIGIBLE"
NOTE = (
    "Stops at build-verified. Handoff: the customer's index, creds, and tag. "
    "Not CD. This wrapper does not publish."
)


def _is_library_checkout(root: Path) -> bool:
    return (
        (root / "setup.py").is_file()
        and (root / "tests" / "others" / "test_dependencies.py").is_file()
        and (root / "src" / "diffusers" / "__init__.py").is_file()
    )


def resolve_library_root() -> Path:
    cwd = Path.cwd().resolve()
    if _is_library_checkout(cwd):
        return cwd
    parent = KIT.parent
    if _is_library_checkout(parent):
        return parent
    env = os.environ.get("DIFFUSERS_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if _is_library_checkout(p):
            return p
    sys.stderr.write(
        "release_check: run on a huggingface/diffusers checkout (fork), "
        "not the kit stand-in. Need setup.py + tests/others/test_dependencies.py.\n"
    )
    sys.exit(2)


def snake_from_export(name: str) -> str:
    name = name.removesuffix("Scheduler")
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _run(cmd: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def detect_new_export(lib: Path) -> str:
    proc = _run(
        ["git", "diff", "origin/main", "--", "src/diffusers/__init__.py"],
        cwd=lib,
    )
    if proc.returncode != 0:
        proc = _run(
            ["git", "diff", "main", "--", "src/diffusers/__init__.py"],
            cwd=lib,
        )
    diff = proc.stdout or ""
    added = re.findall(r'^\+\s+"([A-Za-z_][A-Za-z0-9_]+)",?\s*$', diff, re.M)
    added += re.findall(r"^\+\s+([A-Z][A-Za-z0-9]+),?\s*$", diff, re.M)
    removed = set(re.findall(r'^\-\s+"([A-Za-z_][A-Za-z0-9_]+)",?\s*$', diff, re.M))
    removed |= set(re.findall(r"^\-\s+([A-Z][A-Za-z0-9]+),?\s*$", diff, re.M))
    new = []
    for name in added:
        if name in removed or name in new:
            continue
        new.append(name)
    sched = [n for n in new if n.endswith("Scheduler")]
    pick = sched if sched else new
    if len(pick) == 1:
        return pick[0]
    if not pick:
        sys.stderr.write(
            "release_check: could not detect a new export in "
            "src/diffusers/__init__.py vs origin/main; pass --object\n"
        )
        sys.exit(2)
    sys.stderr.write(
        "release_check: multiple new exports "
        f"{pick}; pass --object\n"
    )
    sys.exit(2)


def _step(name: str, command: str, status: str, detail: str = "") -> dict:
    return {"name": name, "command": command, "status": status, "detail": detail}


def advisories(lib: Path, obj: str) -> list[str]:
    notes: list[str] = []
    names = _run(
        ["git", "diff", "--name-only", "origin/main"],
        cwd=lib,
    ).stdout
    if "changelog" not in names.lower() and "release note" not in names.lower():
        notes.append("no changelog/release-notes entry for the change")
    version_diff = _run(
        ["git", "diff", "origin/main", "--", "setup.py", "src/diffusers/__init__.py"],
        cwd=lib,
    ).stdout
    if not re.search(r"^[-+].*__version__|^[-+].*version", version_diff, re.M | re.I):
        notes.append(
            "public API surface changed; confirm a version/semver decision"
        )
    stem = f"scheduling_{snake_from_export(obj)}.py"
    impl = lib / "src" / "diffusers" / "schedulers" / stem
    if impl.is_file() and "TODO(engineer)" in impl.read_text(encoding="utf-8"):
        notes.append(
            "step() still TODO(engineer); this is a scaffold, not a product release"
        )
    return notes


def ensure_build_module() -> None:
    proc = subprocess.run(
        [sys.executable, "-c", "import build"],
        capture_output=True,
        check=False,
    )
    if proc.returncode == 0:
        return
    inst = subprocess.run(
        [sys.executable, "-m", "pip", "install", "build"],
        capture_output=True,
        text=True,
        check=False,
    )
    if inst.returncode != 0:
        sys.stderr.write(inst.stdout + inst.stderr)
        sys.exit(2)


def restore_editable(lib: Path) -> None:
    _run([sys.executable, "-m", "pip", "install", "-e", ".", "-q"], cwd=lib)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--object", help="public export to import from the wheel")
    ap.add_argument("--json", action="store_true", help="print a JSON report")
    args = ap.parse_args(argv)

    lib = resolve_library_root()
    obj = args.object or detect_new_export(lib)
    steps: list[dict] = []
    ok = True
    wheel_path: Path | None = None
    import_file = ""

    # 1. Dependency contract (library's own pytest job).
    dep_cmd = [sys.executable, "-m", "pytest", "tests/others/test_dependencies.py", "-q"]
    dep = _run(dep_cmd, cwd=lib)
    dep_status = "pass" if dep.returncode == 0 else "fail"
    steps.append(
        _step(
            "dependency_contract",
            " ".join(dep_cmd),
            dep_status,
            (dep.stdout + dep.stderr)[-2000:],
        )
    )
    if dep_status != "pass":
        ok = False

    # 2. Build a wheel (wipe dist/ first).
    if ok:
        ensure_build_module()
        dist = lib / "dist"
        if dist.exists():
            shutil.rmtree(dist)
        build_cmd = [sys.executable, "-m", "build", "--wheel"]
        built = _run(build_cmd, cwd=lib)
        wheels = sorted(dist.glob("*.whl")) if dist.is_dir() else []
        if built.returncode == 0 and len(wheels) == 1:
            wheel_path = wheels[0]
            steps.append(
                _step("build", " ".join(build_cmd), "pass", str(wheel_path))
            )
        else:
            ok = False
            steps.append(
                _step(
                    "build",
                    " ".join(build_cmd),
                    "fail",
                    (built.stdout + built.stderr)[-2000:],
                )
            )

    # 3. Install the exact wheel and import with PYTHONPATH stripped.
    if ok and wheel_path is not None:
        inst_cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--force-reinstall",
            str(wheel_path),
        ]
        inst = _run(inst_cmd, cwd=lib)
        if inst.returncode != 0:
            ok = False
            steps.append(
                _step(
                    "install_and_import",
                    " ".join(inst_cmd),
                    "fail",
                    (inst.stdout + inst.stderr)[-2000:],
                )
            )
        else:
            prove = (
                "import diffusers, sys; "
                "assert 'site-packages' in diffusers.__file__, diffusers.__file__; "
                f"from diffusers import {obj}; "
                "print(diffusers.__file__)"
            )
            prove_cmd = [
                "env",
                "-u",
                "PYTHONPATH",
                sys.executable,
                "-c",
                prove,
            ]
            proved = subprocess.run(
                prove_cmd,
                cwd="/tmp",
                capture_output=True,
                text=True,
                check=False,
            )
            out = (proved.stdout or "").strip()
            import_file = out.splitlines()[-1] if out else ""
            cmd_shown = (
                f"env -u PYTHONPATH {sys.executable} -c "
                f"\"import diffusers, sys; "
                f"assert 'site-packages' in diffusers.__file__, diffusers.__file__; "
                f"from diffusers import {obj}; print(diffusers.__file__)\""
            )
            src_root = str((lib / "src").resolve())
            if (
                proved.returncode == 0
                and "site-packages" in import_file
                and src_root not in import_file
            ):
                steps.append(_step("install_and_import", cmd_shown, "pass", import_file))
            else:
                ok = False
                steps.append(
                    _step(
                        "install_and_import",
                        cmd_shown,
                        "fail",
                        (proved.stdout + proved.stderr + import_file)[-2000:],
                    )
                )

    restore_editable(lib)

    verdict = VERDICT_PASS if ok else VERDICT_FAIL
    report = {
        "verdict": verdict,
        "object": obj,
        "library_root": str(lib),
        "steps": steps,
        "advisories": advisories(lib, obj),
        "note": NOTE,
        "diffusers_file": import_file,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"object: {obj}")
        print(f"library: {lib}")
        for st in steps:
            print(f"{st['status'].upper()} {st['name']}: {st['command']}")
            if st["detail"]:
                print(f"  {st['detail'][:500]}")
        print(f"verdict: {verdict}")
        if report["advisories"]:
            print("advisories (not blocking):")
            for a in report["advisories"]:
                print(f"  - {a}")
        print(NOTE)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
