#!/usr/bin/env python3
"""
convention_check.py — the runnable guardrail for the diffusers Ramp Kit.

ONE script, THREE surfaces (this is the point):
  - in-editor     : Cursor hook runs it after an agent edit -> instant feedback
  - pre-PR        : `make check` / the self-review command -> catch before review
  - CI            : projections/devops/ci-gate.yml runs the exact same script

It reads conventions/rules.yaml (the single source of truth) so the check can
NEVER disagree with what the agent was told or what the reviewer looks for.

Design choices (be ready to defend these):
  - AST over regex wherever structure matters (class bases, method presence,
    mutable defaults, docstrings). AST doesn't false-positive on comments,
    strings, or reformatting the way grep does.
  - Regex only for line-level lexical patterns (deprecated substrings, print).
  - Every finding carries a rule id, severity, file:line, and a fix hint pulled
    from the registry — so the output is actionable, not just red.
  - Exit code = number of BLOCK findings (0 = clean). warn/info never fail CI.

Dependencies: Python 3.9+ and PyYAML. Nothing else — so it runs anywhere,
including a GPU-less CI runner and a fresh clone during the live demo.

Usage:
  python3 tools/convention_check.py <path> [<path> ...] [--json] [--all]
  python3 tools/convention_check.py examples/candidate_scheduler
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write(
        "convention_check needs PyYAML. Install with:\n"
        "  pip install pyyaml --break-system-packages\n"
    )
    sys.exit(2)

from library_paths import KIT_ROOT, resolve_library_root  # noqa: E402

REPO_ROOT = KIT_ROOT  # overlay kit (rules, templates)
LIBRARY_ROOT = resolve_library_root()  # fork when attached; kit stand-in otherwise
RULES_PATH = REPO_ROOT / "conventions" / "rules.yaml"

SEVERITY_ORDER = {"block": 0, "warn": 1, "info": 2}


@dataclass
class Finding:
    rule_id: str
    severity: str
    file: str
    line: int
    message: str
    hint: str = ""

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Rule:
    id: str
    title: str
    severity: str
    check: str
    applies_to: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    agent_hint: str = ""


# --------------------------------------------------------------------------- #
# Registry loading + integrity                                                 #
# --------------------------------------------------------------------------- #
def load_rules() -> list[Rule]:
    data = yaml.safe_load(RULES_PATH.read_text())
    rules = []
    for r in data["rules"]:
        rules.append(
            Rule(
                id=r["id"],
                title=r["title"],
                severity=r["severity"],
                check=r["check"],
                applies_to=r.get("applies_to", []),
                params=r.get("params", {}) or {},
                agent_hint=r.get("agent_hint", ""),
            )
        )
    return rules


def _paths_for_apply(rel_path: str) -> tuple[str, ...]:
    """Repo-relative paths to match against applies_to globs.

    On the library fork the overlay clone lives at ``ramp-kit/``, so a fixture
    such as ``ramp-kit/examples/candidate_scheduler/scheduling_my_sde.py`` must
    still match ``examples/**``. Strip only that overlay-clone prefix. Do not
    rewrite any other leading segment (real library files stay exact).
    """
    rel = rel_path.replace("\\", "/")
    out = [rel]
    prefix = "ramp-kit/"
    if rel.startswith(prefix):
        stripped = rel[len(prefix) :]
        if stripped:
            out.append(stripped)
    return tuple(out)


def rule_applies(rule: Rule, rel_path: str) -> bool:
    """A rule applies if any of its globs match the file's repo-relative path.

    Matching is deliberately precise so a rule never leaks onto files it wasn't
    scoped to (e.g. the kit's own tooling/tests). Two ways a glob can match:
      1. full-path fnmatch against the repo-relative path (and, if present, the
         same path with a leading ``ramp-kit/`` overlay-clone prefix stripped),
      2. a *filename-convention* glob (like `.../scheduling_*.py`) matched
         against just the basename — but only when that basename glob is a real
         pattern, never a bare `**` catch-all.
    """
    from fnmatch import fnmatch

    for candidate in _paths_for_apply(rel_path):
        for pat in rule.applies_to:
            if fnmatch(candidate, pat):
                return True
            base = pat.split("/")[-1]
            if base not in ("**", "*") and "*" in base and fnmatch(Path(candidate).name, base):
                return True
    return False


# --------------------------------------------------------------------------- #
# Checks. Each returns list[Finding] for one file.                            #
# Signature: check(rule, path, rel, source, tree_or_None) -> list[Finding]    #
# --------------------------------------------------------------------------- #
def _iter_classes(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            yield node


def _base_names(cls: ast.ClassDef) -> set[str]:
    names = set()
    for b in cls.bases:
        if isinstance(b, ast.Name):
            names.add(b.id)
        elif isinstance(b, ast.Attribute):
            names.add(b.attr)
    return names


def _looks_like_scheduler(cls: ast.ClassDef, rel: str) -> bool:
    return cls.name.endswith("Scheduler") or "scheduling_" in Path(rel).name


def check_ast_class_bases(rule, path, rel, source, tree):
    out = []
    required = {"SchedulerMixin", "ConfigMixin"}
    for cls in _iter_classes(tree):
        if not _looks_like_scheduler(cls, rel):
            continue
        missing = required - _base_names(cls)
        if missing:
            out.append(Finding(
                rule.id, rule.severity, rel, cls.lineno,
                f"class {cls.name} is missing base(s): {', '.join(sorted(missing))}",
                rule.agent_hint,
            ))
    return out


def check_ast_required_methods(rule, path, rel, source, tree):
    out = []
    required = set(rule.params.get("required_methods", []))
    for cls in _iter_classes(tree):
        if not _looks_like_scheduler(cls, rel):
            continue
        defined = {n.name for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        missing = required - defined
        if missing:
            out.append(Finding(
                rule.id, rule.severity, rel, cls.lineno,
                f"class {cls.name} is missing required method(s): {', '.join(sorted(missing))}",
                rule.agent_hint,
            ))
    return out


def check_ast_init_registered(rule, path, rel, source, tree):
    out = []
    for cls in _iter_classes(tree):
        if not _looks_like_scheduler(cls, rel):
            continue
        for n in cls.body:
            if isinstance(n, ast.FunctionDef) and n.name == "__init__":
                deco = set()
                for d in n.decorator_list:
                    if isinstance(d, ast.Name):
                        deco.add(d.id)
                    elif isinstance(d, ast.Attribute):
                        deco.add(d.attr)
                if "register_to_config" not in deco:
                    out.append(Finding(
                        rule.id, rule.severity, rel, n.lineno,
                        f"{cls.name}.__init__ is not decorated with @register_to_config",
                        rule.agent_hint,
                    ))
    return out


def check_ast_mutable_defaults(rule, path, rel, source, tree):
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults + node.args.kw_defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    out.append(Finding(
                        rule.id, rule.severity, rel, default.lineno,
                        f"mutable default argument in {node.name}()",
                        rule.agent_hint,
                    ))
    return out


def check_ast_public_docstrings(rule, path, rel, source, tree):
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            if ast.get_docstring(node) is None:
                out.append(Finding(
                    rule.id, rule.severity, rel, node.lineno,
                    f"public method {node.name}() has no docstring",
                    rule.agent_hint,
                ))
    return out


def check_ast_generator_randomness(rule, path, rel, source, tree):
    out = []
    sampling = {"randn", "rand", "randint", "normal", "randn_like"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fname = None
            if isinstance(node.func, ast.Attribute):
                fname = node.func.attr
            elif isinstance(node.func, ast.Name):
                fname = node.func.id
            if fname in sampling:
                kwargs = {kw.arg for kw in node.keywords if kw.arg}
                if "generator" not in kwargs:
                    out.append(Finding(
                        rule.id, rule.severity, rel, node.lineno,
                        f"{fname}(...) called without an explicit generator= (non-reproducible)",
                        rule.agent_hint,
                    ))
    return out


def check_regex(rule, path, rel, source, tree):
    out = []
    pat = re.compile(rule.params["pattern"], re.MULTILINE)
    for i, line in enumerate(source.splitlines(), start=1):
        if pat.search(line):
            out.append(Finding(
                rule.id, rule.severity, rel, i,
                f"matched disallowed pattern: {line.strip()[:80]}",
                rule.agent_hint,
            ))
    return out


def check_deprecation_map(rule, path, rel, source, tree):
    out = []
    dep = rule.params.get("deprecated", {})
    for i, line in enumerate(source.splitlines(), start=1):
        for bad, good in dep.items():
            if bad in line:
                out.append(Finding(
                    rule.id, rule.severity, rel, i,
                    f"deprecated `{bad}` -> use `{good}`",
                    rule.agent_hint,
                ))
    return out


def check_copied_from_wellformed(rule, path, rel, source, tree):
    out = []
    marker = re.compile(r"#\s*Copied from\s+(.+)$")
    good_ref = re.compile(r"^diffusers(\.\w+)+(\s+with\s+.+)?$")
    for i, line in enumerate(source.splitlines(), start=1):
        m = marker.search(line)
        if m and not good_ref.match(m.group(1).strip()):
            out.append(Finding(
                rule.id, rule.severity, rel, i,
                f"malformed # Copied from reference: {m.group(1).strip()[:60]}",
                rule.agent_hint,
            ))
    return out


def _companion_test_candidates(rel: str, path: Path, glob: str) -> list[Path]:
    stem = Path(rel).stem  # scheduling_foo
    expected = glob.format(stem=stem)
    return [
        LIBRARY_ROOT / expected,
        REPO_ROOT / expected,
        Path(path).parent.parent / "tests" / f"test_{stem}.py",
        LIBRARY_ROOT / "tests" / f"test_{stem}.py",
        REPO_ROOT / "tests" / f"test_{stem}.py",
    ]


def _shown_path(found: Path) -> str:
    for root in (LIBRARY_ROOT, REPO_ROOT):
        try:
            return str(found.resolve().relative_to(root))
        except ValueError:
            continue
    return str(found)


def _is_test_path(rel: str) -> bool:
    name = Path(rel).name
    return name.startswith("test_") and name.endswith(".py")


def _test_functions(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            yield node


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return ""


def _function_has_assertion(fn: ast.AST) -> bool:
    """True if the function contains an assert statement or unittest/pytest assertion call."""
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call):
            name = _call_name(node)
            if name.startswith("assert") or name in {"raises", "warns"}:
                return True
        if isinstance(node, ast.withitem) and isinstance(node.context_expr, ast.Call):
            name = _call_name(node.context_expr)
            if name.startswith("assert") or name in {"raises", "warns"}:
                return True
    return False


def check_test_presence(rule, path, rel, source, tree):
    """Repo-level: a new scheduler file must have a matching contract test."""
    out = []
    glob = rule.params.get("test_glob", "tests/schedulers/test_{stem}.py")
    expected = glob.format(stem=Path(rel).stem)
    found = next((c for c in _companion_test_candidates(rel, path, glob) if c.exists()), None)
    if found is None:
        out.append(Finding(
            rule.id, rule.severity, rel, 1,
            f"no test file found for {Path(rel).name} (expected {expected})",
            rule.agent_hint,
        ))
        return out
    mentions = rule.params.get("required_mentions") or []
    text = found.read_text(encoding="utf-8", errors="replace")
    missing = [m for m in mentions if not re.search(rf"\b{re.escape(m)}\b", text)]
    if missing:
        out.append(Finding(
            rule.id, rule.severity, rel, 1,
            f"{_shown_path(found)} exists but does not exercise {', '.join(missing)}",
            "Assert the scheduler contract methods in the test (see tests/_templates/scheduler_test.py).",
        ))
    return out


def check_test_adequacy(rule, path, rel, source, tree):
    """Weak-test detection: empty test_* functions, plus scheduler determinism/shape/dtype."""
    out = []
    glob = rule.params.get("test_glob", "tests/schedulers/test_{stem}.py")
    if _is_test_path(rel):
        test_path, test_rel, test_source = path, rel, source
        test_tree = tree
        if test_tree is None:
            try:
                test_tree = ast.parse(test_source, filename=str(path))
            except SyntaxError as e:
                out.append(Finding(
                    rule.id, rule.severity, rel, e.lineno or 1,
                    f"test file does not parse: {e.msg}",
                    "Fix the syntax error first.",
                ))
                return out
    else:
        found = next((c for c in _companion_test_candidates(rel, path, glob) if c.exists()), None)
        if found is None:
            return out  # TEST001 already flags a missing file
        test_path = found
        test_rel = _shown_path(found)
        test_source = found.read_text(encoding="utf-8", errors="replace")
        try:
            test_tree = ast.parse(test_source, filename=str(found))
        except SyntaxError as e:
            out.append(Finding(
                rule.id, rule.severity, test_rel, e.lineno or 1,
                f"test file does not parse: {e.msg}",
                "Fix the syntax error in the companion test.",
            ))
            return out

    if rule.params.get("require_assertions", True):
        test_fns = list(_test_functions(test_tree) if test_tree is not None else [])
        if not test_fns:
            out.append(Finding(
                rule.id, rule.severity, test_rel, 1,
                f"{Path(test_rel).name} has no test_* functions with assertions",
                rule.agent_hint,
            ))
        for fn in test_fns:
            if not _function_has_assertion(fn):
                out.append(Finding(
                    rule.id, rule.severity, test_rel, fn.lineno,
                    f"test function {fn.name}() has zero assertions",
                    rule.agent_hint,
                ))

    if rule.params.get("require_determinism"):
        det = re.search(r"torch\.equal|same_seed|same seed", test_source, re.IGNORECASE)
        if not det:
            out.append(Finding(
                rule.id, rule.severity, test_rel, 1,
                "scheduler test has no same-seed determinism assertion (torch.equal / same seed)",
                "Add test_same_seed_same_output using torch.equal on two seeded step() calls.",
            ))

    if rule.params.get("require_shape_dtype"):
        has_shape = re.search(r"\bshape\b", test_source) is not None
        has_dtype = re.search(r"\bdtype\b", test_source) is not None
        missing = [n for n, ok in (("shape", has_shape), ("dtype", has_dtype)) if not ok]
        if missing:
            out.append(Finding(
                rule.id, rule.severity, test_rel, 1,
                f"scheduler test is missing { ' and '.join(missing) } assertion(s)",
                "Assert prev_sample.shape and prev_sample.dtype against the input sample.",
            ))
    return out


CHECKS: dict[str, Callable] = {
    "ast_class_bases": check_ast_class_bases,
    "ast_required_methods": check_ast_required_methods,
    "ast_init_registered": check_ast_init_registered,
    "ast_mutable_defaults": check_ast_mutable_defaults,
    "ast_public_docstrings": check_ast_public_docstrings,
    "ast_generator_randomness": check_ast_generator_randomness,
    "regex": check_regex,
    "deprecation_map": check_deprecation_map,
    "copied_from_wellformed": check_copied_from_wellformed,
    "test_presence": check_test_presence,
    "test_adequacy": check_test_adequacy,
}

AST_CHECKS = {
    "ast_class_bases", "ast_required_methods", "ast_init_registered",
    "ast_mutable_defaults", "ast_public_docstrings", "ast_generator_randomness",
}


# --------------------------------------------------------------------------- #
# Runner                                                                       #
# --------------------------------------------------------------------------- #
# Paths skipped only during a repo-wide `--all` scan. These are intentional
# teaching fixtures of BAD code (scanned explicitly by `make demo`) and the
# kit's own generated/vendored areas — not part of a contribution surface.
ALL_SCAN_EXCLUDES = ("candidate_scheduler", "/_templates/", "templates/")


def gather_py_files(paths: list[str], scanning_all: bool = False) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            files.extend(sorted(pp.rglob("*.py")))
        elif pp.suffix == ".py":
            files.append(pp)
    if scanning_all:
        files = [f for f in files if not any(x in str(f) for x in ALL_SCAN_EXCLUDES)]
    files = [
        f for f in files
        if "__pycache__" not in f.parts and ".cursor" not in f.parts
    ]
    return files


def relpath(p: Path) -> str:
    resolved = p.resolve()
    for root in (LIBRARY_ROOT, REPO_ROOT):
        try:
            return str(resolved.relative_to(root.resolve()))
        except ValueError:
            continue
    return str(p)


def check_file(path: Path, rules: list[Rule]) -> list[Finding]:
    rel = relpath(path)
    source = path.read_text(encoding="utf-8", errors="replace")
    tree = None
    findings: list[Finding] = []
    applicable = [r for r in rules if rule_applies(r, rel)]
    needs_ast = any(r.check in AST_CHECKS for r in applicable)
    if needs_ast:
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as e:
            findings.append(Finding(
                "PARSE000", "block", rel, e.lineno or 1,
                f"file does not parse: {e.msg}", "Fix the syntax error first.",
            ))
            return findings
    for rule in applicable:
        fn = CHECKS.get(rule.check)
        if fn is None:
            continue
        if rule.check in AST_CHECKS and tree is None:
            continue
        findings.extend(fn(rule, path, rel, source, tree))
    return findings


def render_human(findings: list[Finding], n_files: int) -> str:
    if not findings:
        return f"✓ convention_check: {n_files} file(s) scanned, 0 findings. Clean.\n"
    findings = sorted(findings, key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), f.file, f.line))
    icon = {"block": "✗", "warn": "!", "info": "i"}
    lines = [""]
    for f in findings:
        lines.append(f"{icon.get(f.severity,'?')} [{f.severity.upper():5}] {f.rule_id}  {f.file}:{f.line}")
        lines.append(f"        {f.message}")
        if f.hint:
            lines.append(f"        fix: {f.hint}")
    n_block = sum(1 for f in findings if f.severity == "block")
    n_warn = sum(1 for f in findings if f.severity == "warn")
    lines.append("")
    lines.append(f"convention_check: {n_files} file(s), {n_block} blocking, {n_warn} warning(s).")
    lines.append("Blocking findings must be fixed before this change can move to review/CI." if n_block else "No blocking findings; warnings are advisory.")
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="diffusers Ramp Kit convention gate")
    ap.add_argument("paths", nargs="*", default=["."], help="files or dirs to scan")
    ap.add_argument("--json", action="store_true", help="emit JSON (for CI / dashboards)")
    ap.add_argument("--all", action="store_true", help="scan the whole repo")
    args = ap.parse_args(argv)

    rules = load_rules()
    paths = ["."] if args.all else (args.paths or ["."])
    files = gather_py_files(paths, scanning_all=args.all)
    # never scan our own tooling or vendored code
    files = [f for f in files if "tools/convention_check" not in str(f)]

    all_findings: list[Finding] = []
    for f in files:
        all_findings.extend(check_file(f, rules))

    if args.json:
        payload = {
            "scanned": len(files),
            "findings": [f.to_row() for f in all_findings],
            "blocking": sum(1 for f in all_findings if f.severity == "block"),
            "warnings": sum(1 for f in all_findings if f.severity == "warn"),
        }
        print(json.dumps(payload, indent=2))
    else:
        sys.stdout.write(render_human(all_findings, len(files)))

    return sum(1 for f in all_findings if f.severity == "block")


if __name__ == "__main__":
    raise SystemExit(main())
