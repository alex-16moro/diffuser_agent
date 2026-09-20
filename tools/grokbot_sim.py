#!/usr/bin/env python3
"""GrokBot role-agent SIMULATION.

Fuses convention_check --json with an optional role-native change-context
and prints a grounded, role-tailored briefing. This is NOT a gate. The
gate is convention_check.py; CI is the YAML generated from the same
registry. GrokBot only translates. It never merges and never fails CI.

  python3 tools/grokbot_sim.py --role qa < gate.json
  python3 tools/convention_check.py --json examples/candidate_scheduler \\
    | python3 tools/grokbot_sim.py --role qa
  python3 tools/grokbot_sim.py --role devops \\
    --context examples/change_context.example.json

When gate JSON is omitted and stdin is a TTY, the sim scans
examples/scaffolded_scheduler (0 findings) so the EulerLite context
demo is offline-runnable.

Roles: pm (DoD / merge-eligibility), qa (test adequacy), devops (pipeline).
Every claim line cites [gate] [ci] [issue] or [drift]. Prompt content is
loaded from conventions/rules.yaml `owner:` tags.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("grokbot_sim needs PyYAML\n")
    sys.exit(2)

KIT = Path(__file__).resolve().parent.parent
ROLES = ("pm", "qa", "devops")
OUTPUT = {
    "pm": "STATUS DIGEST",
    "qa": "RISK BRIEFING",
    "devops": "HEALTH / SIGNAL",
}
VALID_STATES = ("scaffolded", "gate-green", "tests-pass", "merge-eligible")
SOURCE_TAGS = ("gate", "ci", "issue", "drift")
CANNOT_SEE = {
    "pm": (
        ("issue", "team velocity / sprint capacity — not wired"),
        ("issue", "roadmap dependencies beyond this PR's issue/milestone — not wired"),
        ("issue", "calendar ship dates — not wired; do not invent an ETA"),
    ),
    "qa": (
        ("gate", "real numerical correctness vs the paper — gate does not judge math"),
        ("gate", "whether the sampler duplicates EulerDiscrete in meaning — not wired"),
        ("ci", "GPU / pipeline integration results — not wired"),
    ),
    "devops": (
        ("ci", "production deploy environment — not wired"),
        ("ci", "whether inherited Hugging Face CI will go green on this fork — not wired"),
        ("ci", "secrets / runner-fleet health beyond this repo — not wired"),
    ),
}


def load_rules() -> dict:
    data = yaml.safe_load((KIT / "conventions" / "rules.yaml").read_text())
    return {r["id"]: r for r in data["rules"]}


def read_gate(path: str | None) -> dict:
    raw = ""
    if path:
        raw = Path(path).read_text(encoding="utf-8")
    elif not sys.stdin.isatty():
        raw = sys.stdin.read()
    if raw.strip():
        return json.loads(raw)
    proc = subprocess.run(
        [
            sys.executable,
            str(KIT / "tools" / "convention_check.py"),
            "--json",
            str(KIT / "examples" / "scaffolded_scheduler"),
        ],
        cwd=KIT,
        capture_output=True,
        text=True,
        check=False,
    )
    if not proc.stdout.strip():
        sys.stderr.write(
            "grokbot_sim: expected gate JSON on stdin or as a file path "
            "(default scaffolded_scheduler scan produced no JSON)\n"
        )
        sys.exit(2)
    return json.loads(proc.stdout)


def read_context(path: str | None) -> dict:
    if not path:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        sys.stderr.write("grokbot_sim: --context must be a JSON object\n")
        sys.exit(2)
    return data


def _get(data: dict, *keys, default=None):
    cur = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _bullet(tag: str, text: str) -> str:
    if tag not in SOURCE_TAGS:
        raise ValueError(f"unknown source tag: {tag}")
    return f"- [{tag}] {text}"


def _finding_line(f: dict, rec: dict | None = None) -> str:
    extra = ""
    if rec is not None:
        extra = f" owner={rec.get('owner', '?')}"
    return (
        f"[{f.get('severity', '?').upper()}] {f.get('rule_id')}{extra} "
        f"{f.get('file')}:{f.get('line')} — {f.get('message')}"
    )


def brief(
    role: str,
    gate: dict,
    rules: dict,
    context: dict | None = None,
    packaging: dict | None = None,
) -> str:
    context = context or {}
    findings = gate.get("findings") or []
    blocking = gate.get(
        "blocking", sum(1 for f in findings if f.get("severity") == "block")
    )
    warnings = gate.get(
        "warnings", sum(1 for f in findings if f.get("severity") == "warn")
    )
    scanned = gate.get("scanned", "?")
    merge_eligible = blocking == 0

    by_owner = defaultdict(list)
    for f in findings:
        rid = f.get("rule_id", "")
        rec = rules.get(rid)
        if rec is None:
            by_owner["unassigned"].append((f, {}))
            continue
        by_owner[rec.get("owner", "unassigned")].append((f, rec))

    owned_rules = [r for r in rules.values() if r.get("owner") == role]
    owned_findings = by_owner.get(role) or []
    owned_ids = ", ".join(r["id"] for r in owned_rules) or "(none)"

    pr_number = _get(context, "pr", "number")
    pr_title = _get(context, "pr", "title")
    pr_issue = _get(context, "pr", "issue")
    pr_milestone = _get(context, "pr", "milestone")
    pr_labels = _get(context, "pr", "labels")
    pr_draft = _get(context, "pr", "draft")
    ci_gate = _get(context, "ci", "convention_gate")
    ci_drift = _get(context, "ci", "drift_check")
    ci_inherited = _get(context, "ci", "inherited_workflows")
    declared_state = _get(context, "state")

    lines = [
        f"=== GrokBot {role.upper()} · {OUTPUT[role]} ===",
        "SIMULATION — translates gate JSON + optional change-context. "
        "Does not gate. Does not merge.",
        "",
    ]

    if role == "devops":
        lines.append("## Pipeline health")
        if ci_gate is None:
            lines.append(_bullet("ci", "no CI context; convention_gate not wired"))
        else:
            lines.append(_bullet("ci", f"convention_gate: {ci_gate}"))
        if ci_drift is None:
            lines.append(_bullet("drift", "no change-context; drift_check not wired"))
        else:
            lines.append(_bullet("drift", f"drift_check: {ci_drift}"))
        if ci_inherited is None:
            lines.append(_bullet("ci", "inherited_workflows not wired"))
        else:
            lines.append(_bullet("ci", f"inherited_workflows: {ci_inherited}"))
        lines.append(
            _bullet(
                "gate",
                f"overlay convention_check: {scanned} file(s), "
                f"{blocking} blocking, {warnings} warning(s).",
            )
        )
        lines.append("")
        lines.append("## DevOps-owned findings")
        if owned_findings:
            for f, rec in owned_findings:
                lines.append(_bullet("gate", _finding_line(f, rec)))
        else:
            lines.append(_bullet("gate", "no DevOps-owned findings in this report."))
        lines.append("")
        lines.append("## Signal")
        if merge_eligible:
            lines.append(
                _bullet(
                    "gate",
                    "mechanical GREEN (blocking=0). Overlay clearance ≠ "
                    "upstream Hugging Face CI.",
                )
            )
        else:
            lines.append(
                _bullet(
                    "gate",
                    f"mechanical RED until blocking is 0 (blocking={blocking}).",
                )
            )
        lines.append(
            _bullet(
                "ci",
                "this briefing never fails a job and never merges.",
            )
        )
        lines.append("")
        lines.append("## Packaging")
        if packaging and packaging.get("verdict"):
            lines.append(
                _bullet("ci", f"verdict: {packaging.get('verdict')}")
            )
            if packaging.get("object"):
                lines.append(_bullet("ci", f"object: {packaging.get('object')}"))
            proven = packaging.get("diffusers_file") or ""
            if proven:
                lines.append(_bullet("ci", f"diffusers.__file__: {proven}"))
            for st in packaging.get("steps") or []:
                lines.append(
                    _bullet(
                        "ci",
                        f"{st.get('name')}: {st.get('status')} ({st.get('command')})",
                    )
                )
            for adv in packaging.get("advisories") or []:
                lines.append(_bullet("ci", f"advisory: {adv}"))
            if packaging.get("note"):
                lines.append(_bullet("ci", packaging["note"]))
        else:
            lines.append(_bullet("ci", "packaging check not wired"))
    elif role == "pm":
        lines.append("## DoD state")
        if declared_state in VALID_STATES:
            extra = ""
            if declared_state == "scaffolded":
                extra = " — scaffold ≠ product-done"
            lines.append(
                _bullet("issue", f"declared state: {declared_state}{extra}")
            )
        elif declared_state is None:
            lines.append(
                _bullet("issue", "declared state not wired (no change-context)")
            )
        else:
            lines.append(
                _bullet(
                    "issue",
                    f"declared state {declared_state!r} is not one of "
                    f"{'|'.join(VALID_STATES)}; ignoring it",
                )
            )
        if merge_eligible:
            lines.append(
                _bullet(
                    "gate",
                    "mechanical merge-eligible: YES (blocking=0). "
                    "Product-done is a human call, not this signal.",
                )
            )
        else:
            lines.append(
                _bullet(
                    "gate",
                    f"mechanical merge-eligible: NO (blocking={blocking}).",
                )
            )
        if pr_issue:
            lines.append(_bullet("issue", f"issue: {pr_issue}"))
        else:
            lines.append(_bullet("issue", "issue not wired"))
        if pr_milestone:
            lines.append(_bullet("issue", f"milestone: {pr_milestone}"))
        else:
            lines.append(_bullet("issue", "milestone not wired"))
        if pr_number is not None or pr_title:
            draft = ""
            if pr_draft is True:
                draft = " (draft)"
            elif pr_draft is False:
                draft = " (ready-for-review)"
            title = pr_title or "(no title)"
            num = f"#{pr_number} " if pr_number is not None else ""
            lines.append(_bullet("issue", f"PR {num}{title}{draft}".strip()))
        if pr_labels:
            lines.append(_bullet("issue", f"labels: {', '.join(map(str, pr_labels))}"))
        lines.append("")
        lines.append("## PM-owned registry rows (status-view, not an authored gate)")
        lines.append(
            _bullet(
                "gate",
                f"owner=pm rows: {owned_ids}. PM value is live DoD state, "
                "not a second gate.",
            )
        )
        if owned_findings:
            for f, rec in owned_findings:
                lines.append(
                    _bullet(
                        "gate",
                        f"OPEN `{f.get('rule_id')}` — {rec.get('dod', f.get('message'))}",
                    )
                )
        else:
            lines.append(
                _bullet("gate", "no PM-owned findings on this change.")
            )
        lines.append("")
        lines.append("## Call")
        product_done = (
            "NO (scaffold ≠ product-done)"
            if declared_state == "scaffolded"
            else "not asserted (no product-done signal)"
        )
        lines.append(
            _bullet(
                "gate",
                f"mechanical merge-eligible: {'YES' if merge_eligible else 'NO'}.",
            )
        )
        lines.append(_bullet("issue", f"product-done: {product_done}."))
        lines.append(
            _bullet(
                "issue",
                "next human action: review the scaffold; do not treat overlay-green "
                "as a shipped scheduler."
                if declared_state == "scaffolded"
                else "next human action: use DoD + blocking count; no timeline invented.",
            )
        )
    else:  # qa
        lines.append("## Test adequacy (owner=qa)")
        lines.append(
            _bullet("gate", f"registry QA rows: {owned_ids} (presence + assertions).")
        )
        if owned_findings:
            for f, rec in owned_findings:
                lines.append(_bullet("gate", _finding_line(f)))
                if rec.get("dod"):
                    lines.append(_bullet("gate", f"DoD at risk: {rec['dod']}"))
        else:
            lines.append(
                _bullet("gate", "no QA-owned findings in this gate report.")
            )
        lines.append("")
        lines.append("## Residual math risk")
        lines.append(
            _bullet(
                "gate",
                "numerical method vs the paper is outside TEST001/TEST002.",
            )
        )
        lines.append(
            _bullet(
                "gate",
                "overlay-green is not a pass on the sampler.",
            )
        )
        lines.append("")
        lines.append("## Other blocking (not QA-owned; still merge-blockers)")
        others = [
            (f, rec)
            for owner, items in by_owner.items()
            if owner != role
            for f, rec in items
            if f.get("severity") == "block"
        ]
        if not others:
            lines.append(_bullet("gate", "none."))
        for f, rec in others:
            lines.append(_bullet("gate", _finding_line(f, rec)))
        lines.append("")
        lines.append("## Merge call")
        if merge_eligible:
            lines.append(
                _bullet(
                    "gate",
                    "mechanical bar is green; human review of math remains.",
                )
            )
        else:
            lines.append(
                _bullet("gate", f"NOT merge-eligible (blocking={blocking}).")
            )

    lines.append("")
    lines.append("## Cannot see")
    for tag, text in CANNOT_SEE[role]:
        lines.append(_bullet(tag, text))
    lines.append("")
    lines.append(
        "End of simulation. Authoritative merge signal remains "
        "convention_check exit code."
    )
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", required=True, choices=ROLES)
    ap.add_argument(
        "--context",
        metavar="FILE.json",
        help="optional change-context JSON (pr / ci / state)",
    )
    ap.add_argument(
        "--release-json",
        metavar="FILE.json",
        help="JSON from a prior `release_check.py --object <detected> --json` "
        "run on the fork. Reads that report; never runs python -m build.",
    )
    ap.add_argument(
        "gate_json",
        nargs="?",
        help="path to convention_check --json output (default: stdin, "
        "or examples/scaffolded_scheduler when stdin is a TTY)",
    )
    args = ap.parse_args(argv)
    gate = read_gate(args.gate_json)
    context = read_context(args.context)
    packaging = None
    if args.release_json:
        packaging = json.loads(Path(args.release_json).read_text(encoding="utf-8"))
    sys.stdout.write(brief(args.role, gate, load_rules(), context, packaging))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
