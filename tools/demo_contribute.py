#!/usr/bin/env python3
"""Narrated first-contribution demo — the same steps `/scaffold` tells an engineer.

This is the CLI twin of the live Cursor journey. Use it to rehearse, as a
fallback if slash-commands stall, or in CI. It does not invent math.

  python3 tools/demo_contribute.py                  # create, prove, remove
  python3 tools/demo_contribute.py --keep           # leave files for the walkthrough
  python3 tools/demo_contribute.py --name EulerLite
  python3 tools/demo_contribute.py --clean-only --name EulerLite
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


def snake(name: str) -> str:
    name = name.removesuffix("Scheduler")
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def class_name(name: str) -> str:
    return name if name.endswith("Scheduler") else f"{name}Scheduler"


def paths_for(name: str) -> tuple[str, Path, Path]:
    cls = class_name(name)
    stem = f"scheduling_{snake(name)}"
    impl = ROOT / "src" / "diffusers" / "schedulers" / f"{stem}.py"
    test = ROOT / "tests" / "schedulers" / f"test_{stem}.py"
    return cls, impl, test


def step(n: int, title: str) -> None:
    print(f"\n========== {n}. {title} ==========\n", flush=True)


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(args)}", flush=True)
    proc = subprocess.run(args, cwd=ROOT, check=False)
    if check and proc.returncode != 0:
        raise SystemExit(proc.returncode)
    return proc


def ground() -> None:
    sys.path.insert(0, str(ROOT / "tools"))
    from docs_mcp_server import _format_hits, search_docs  # noqa: WPS433

    query = "scheduler set_timesteps step SchedulerMixin register_to_config"
    print(f"Grounding (optional docs CLI --query):\n  query: {query}\n")
    print(_format_hits(search_docs(query, k=2)))
    print(
        "\nSay: grounding is advisory. The registry + gate are authoritative "
        "if the snippets miss the contract paragraph."
    )


# Tokens that must not survive a scaffolded copy. TODO(engineer) stays.
_LEFTOVER_PLACEHOLDERS = (
    "TEMPLATE —",
    "TEMPLATE -",
    "CHANGE_ME",
    "ChangeMeScheduler",
    "TemplateScheduler",
)


def _assert_no_placeholders(path: Path) -> None:
    text = path.read_text()
    leftover = [tok for tok in _LEFTOVER_PLACEHOLDERS if tok in text]
    if leftover:
        raise SystemExit(
            f"scaffold left placeholder(s) {leftover} in {path.relative_to(ROOT)}"
        )
    if "TODO(engineer)" not in text and path.name.startswith("scheduling_"):
        raise SystemExit(f"scaffold dropped TODO(engineer) in {path.relative_to(ROOT)}")


def scaffold(cls: str, impl: Path, test: Path) -> None:
    tmpl = (ROOT / "templates" / "scheduler" / "scheduling_TEMPLATE.py").read_text()
    if "TemplateScheduler" not in tmpl:
        raise SystemExit("scheduler template missing TemplateScheduler")
    impl.parent.mkdir(parents=True, exist_ok=True)
    impl.write_text(tmpl.replace("TemplateScheduler", cls))
    _assert_no_placeholders(impl)
    print(f"wrote {impl.relative_to(ROOT)}")
    print(f"  class {cls} — numerical update left as TODO(engineer)")

    ttmpl = (ROOT / "tests" / "_templates" / "scheduler_test.py").read_text()
    stem = impl.stem
    ttmpl = ttmpl.replace("scheduling_CHANGE_ME.py", f"{stem}.py")
    ttmpl = ttmpl.replace("ChangeMeScheduler", cls)
    test.parent.mkdir(parents=True, exist_ok=True)
    test.write_text(ttmpl)
    _assert_no_placeholders(test)
    print(f"wrote {test.relative_to(ROOT)}")
    print("  TARGET + CLASS set; every template token replaced (TEST001)")


def remove(impl: Path, test: Path) -> None:
    for p in (impl, test):
        if p.exists():
            p.unlink()
            print(f"removed {p.relative_to(ROOT)}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", default="EulerLite", help="PascalCase name without Scheduler")
    ap.add_argument("--keep", action="store_true", help="leave the new files on disk")
    ap.add_argument("--clean-only", action="store_true", help="delete the named files and exit")
    ap.add_argument("--skip-bad-example", action="store_true")
    args = ap.parse_args(argv)

    cls, impl, test = paths_for(args.name)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)

    if args.clean_only:
        remove(impl, test)
        return 0

    print("First-contribution journey (CLI twin of /scaffold scheduler", args.name + ")")
    print("This stand-in is a contribution overlay, not a Diffusers tutorial.\n")

    if not args.skip_bad_example:
        step(1, "Plan / catch-early — what a from-memory first cut looks like")
        print("PM intake lives in .github/ISSUE_TEMPLATE/contribution.md")
        print("Same blocking rules as CI. Now the gate on a typical first cut:\n")
        run([PYTHON, "tools/convention_check.py", "examples/candidate_scheduler"], check=False)
        print(
            "\nSay: eight blocking findings (DEPR001 moved import, SCHED003 "
            "no @register_to_config, DEVICE001 .cuda(), …). A reviewer round-trip."
        )

    step(2, "Ground — repo docs, not training memory")
    ground()

    step(3, "Build — copy the convention-correct template (the /scaffold steps)")
    print("Cursor path: /scaffold scheduler", args.name)
    print("CLI path: this script. Same two files, same TODO(engineer).\n")
    scaffold(cls, impl, test)

    step(4, "Review gate — same script the editor hook and CI run")
    gate = run([PYTHON, "tools/convention_check.py", str(impl)], check=False)
    if gate.returncode != 0:
        print("ERROR: scaffolded contribution is not gate-clean.", file=sys.stderr)
        if not args.keep:
            remove(impl, test)
        return gate.returncode
    print("Say: 0 findings. The contract is right; the math is still a TODO.")

    step(5, "Test — structural/signature always; behavior skips without torch")
    test_mod = f"tests.schedulers.test_{impl.stem}"
    run([PYTHON, "-m", "unittest", test_mod, "-v"])

    step(6, "Path to production — same rules, other audiences")
    print(
        "QA:  projections/qa/review-checklist.md  (math stays human)\n"
        "     GrokBot sim: python tools/grokbot_sim.py --role qa < gate.json"
    )
    print("PM:  projections/pm/definition-of-done.md + issue template")
    print("CI:  .github/workflows/convention-gate.yml  (green = merge-eligible)")
    print("Boundary: .cursorignore hides examples/candidate_scheduler/")
    print("\nSay: I stop at release clearance. I do not fake a deploy.")

    if args.keep:
        print(f"\nKept:\n  {impl.relative_to(ROOT)}\n  {test.relative_to(ROOT)}")
        print("Remove later: python3 tools/demo_contribute.py --clean-only "
              f"--name {args.name}")
    else:
        step(7, "Clean — rehearsal mode removes the files (live Cursor keeps them)")
        remove(impl, test)
        print("Re-run with --keep to leave the contribution on disk.")

    print("\nJourney complete. Next (optional): make demo-maintain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
