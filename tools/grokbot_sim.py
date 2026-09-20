#!/usr/bin/env python3
"""GrokBot role-agent SIMULATION.

Reads convention_check --json and prints a role-tailored summary.
This is NOT a gate. The gate is convention_check.py; CI is the YAML
generated from the same registry. GrokBot only translates.

  python3 tools/grokbot_sim.py --role qa < gate.json
  python3 tools/convention_check.py --json examples/candidate_scheduler \\
    | python3 tools/grokbot_sim.py --role qa

Roles: pm (status digest), qa (risk briefing), devops (health/signal).
Prompt content is loaded from conventions/rules.yaml `owner:` tags.
"""
from __future__ import annotations

import argparse
import json
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


def load_rules() -> dict:
    data = yaml.safe_load((KIT / "conventions" / "rules.yaml").read_text())
    return {r["id"]: r for r in data["rules"]}


def read_gate(path: str | None) -> dict:
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    if not raw.strip():
        sys.stderr.write(
            "grokbot_sim: expected gate JSON on stdin or as a file path\n"
        )
        sys.exit(2)
    return json.loads(raw)


def brief(role: str, gate: dict, rules: dict) -> str:
    findings = gate.get("findings") or []
    blocking = gate.get("blocking", sum(1 for f in findings if f.get("severity") == "block"))
    warnings = gate.get("warnings", sum(1 for f in findings if f.get("severity") == "warn"))
    scanned = gate.get("scanned", "?")

    by_owner = defaultdict(list)
    unknown = []
    for f in findings:
        rid = f.get("rule_id", "")
        rec = rules.get(rid)
        if rec is None:
            unknown.append(f)
            continue
        by_owner[rec.get("owner", "unassigned")].append((f, rec))

    owned_rules = [r for r in rules.values() if r.get("owner") == role]
    owned_findings = by_owner.get(role) or []

    lines = [
        f"=== GrokBot {role.upper()} · {OUTPUT[role]} ===",
        "SIMULATION — translates gate JSON. Does not gate. Does not merge.",
        "",
        f"Change record: {scanned} file(s) scanned, {blocking} blocking, {warnings} warning(s).",
        f"Registry rules owned by `{role}`: "
        + (", ".join(r["id"] for r in owned_rules) or "(none)"),
        "",
    ]

    if role == "qa":
        lines.append("## Risk (QA-owned findings first)")
        if owned_findings:
            for f, rec in owned_findings:
                lines.append(
                    f"- [{f.get('severity', '?').upper()}] {f.get('rule_id')} "
                    f"{f.get('file')}:{f.get('line')} — {f.get('message')}"
                )
                lines.append(f"    DoD at risk: {rec.get('dod', '')}")
        else:
            lines.append("- No QA-owned findings in this gate report.")
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
            lines.append("- None.")
        for f, rec in others:
            lines.append(
                f"- [{f.get('rule_id')}] owner={rec.get('owner')} "
                f"{f.get('file')}:{f.get('line')} — {f.get('message')}"
            )
        lines.append("")
        lines.append("## Residual human risk (gate cannot judge)")
        lines.append("- Numerical method vs the paper.")
        lines.append("- Whether this duplicates an existing scheduler.")
        lines.append(
            "- Merge call: "
            + ("NOT merge-eligible (blocking > 0)." if blocking else "mechanical bar is green; human review remains.")
        )
    elif role == "pm":
        lines.append("## Status")
        lines.append(
            f"- Merge-eligible (mechanical DoD): {'NO' if blocking else 'YES'}."
        )
        lines.append(f"- Blocking items still open: {blocking}.")
        lines.append("")
        lines.append("## PM-owned DoD on this change")
        if owned_findings:
            for f, rec in owned_findings:
                lines.append(f"- OPEN `{f.get('rule_id')}` — {rec.get('dod')}")
        else:
            lines.append("- No PM-owned findings. DOC001/public-docs bar not raised.")
        lines.append("")
        lines.append("## Cross-owner blockers (same registry)")
        if blocking:
            for f in findings:
                if f.get("severity") != "block":
                    continue
                rec = rules.get(f.get("rule_id"), {})
                lines.append(
                    f"- `{f.get('rule_id')}` ({rec.get('owner', '?')}): {f.get('message')}"
                )
        else:
            lines.append("- None. Status: ready for human review / release clearance.")
    else:  # devops
        lines.append("## Signal")
        lines.append(f"- Gate exit code would be {blocking} (blocking findings).")
        lines.append(
            "- CI also runs: projection drift (`build_projections.py && git diff --exit-code`), "
            "scheduler contract re-verify, MCP self-test, unittest."
        )
        lines.append("")
        lines.append("## DevOps-owned findings")
        if owned_findings:
            for f, rec in owned_findings:
                lines.append(
                    f"- [{f.get('severity', '?').upper()}] {f.get('rule_id')} "
                    f"{f.get('file')}:{f.get('line')} — {f.get('message')}"
                )
        else:
            lines.append("- None in this report.")
        lines.append("")
        lines.append("## Health")
        lines.append(
            "- Overlay MCP default is empty (`overlay/mcp.json`); CLI docs query is the fallback."
        )
        lines.append(
            "- Never run convention_check --all on the full library tree; file-scope on the fork."
        )
        if blocking:
            lines.append("- Signal: RED until blocking is 0.")
        else:
            lines.append("- Signal: GREEN (mechanical). Overlay clearance ≠ upstream HF CI.")

    lines.append("")
    lines.append("End of simulation. Authoritative merge signal remains convention_check exit code.")
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--role", required=True, choices=ROLES)
    ap.add_argument(
        "gate_json",
        nargs="?",
        help="path to convention_check --json output (default: stdin)",
    )
    args = ap.parse_args(argv)
    gate = read_gate(args.gate_json)
    sys.stdout.write(brief(args.role, gate, load_rules()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
