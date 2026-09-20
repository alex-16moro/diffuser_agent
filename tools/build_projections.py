#!/usr/bin/env python3
"""
build_projections.py — render every audience surface from conventions/rules.yaml.

`make build` runs this. It regenerates:
  .cursor/rules/00-conventions.mdc      (agent, always-on: component=any rules)
  .cursor/rules/10-<component>.mdc       (agent, auto-attached, ONE PER COMPONENT)
  AGENTS.md                              (tool-agnostic: Codex/Claude Code/etc.)
  projections/pm/definition-of-done.md   (PM)
  projections/qa/review-checklist.md     (QA / reviewer)
  projections/devops/ci-gate.md          (DevOps, human)
  projections/devops/ci-gate.yml         (DevOps, copy of the workflow)
  .github/workflows/convention-gate.yml  (the workflow GitHub actually runs)
  .github/PULL_REQUEST_TEMPLATE.md       (author / reviewer)
  .github/ISSUE_TEMPLATE/contribution.md (PM planning)

SCALING PROOF: the per-component rule files are generated from each rule's
`component:` tag. Add rules tagged `component: model` and a `10-model.mdc`
appears automatically — no code change here. Humans edit ONLY rules.yaml.

It also validates that every rule's `check` is implemented in convention_check
(and vice-versa), so a rule can't be documented-but-unenforced.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("build_projections needs PyYAML: pip install pyyaml --break-system-packages\n")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
RULES = yaml.safe_load((ROOT / "conventions" / "rules.yaml").read_text())
META = RULES["meta"]
R = RULES["rules"]
COMPONENTS = META.get("components", {})

BANNER = "<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->"
BANNER_HASH = "# GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`."
ALLOWED_OWNERS = ("dev", "architect", "qa", "pm", "devops")
GROKBOT_ROLES = {
    "pm": {
        "title": "PM status digest",
        "job": "Turn the gate/CI output for this change into a ship/no-ship status digest a PM can read in one minute.",
        "reads": "convention_check --json, CI conclusion, the issue/PR change record, owner=pm rows in the registry.",
        "output": "status digest: blocking count, DoD items still open, whether the change is merge-eligible.",
    },
    "qa": {
        "title": "QA risk briefing",
        "job": "Turn the gate/CI output for this change into a risk briefing: what is machine-blocked, what tests are weak, what still needs a human.",
        "reads": "convention_check --json, CI conclusion, the change record, owner=qa rows in the registry.",
        "output": "risk briefing: QA-owned blocking findings first, other blocks, residual human-only risk (math, duplication).",
    },
    "devops": {
        "title": "DevOps health signal",
        "job": "Turn the gate/CI output for this change into a health/signal: will CI stay green, did generated surfaces drift, is the overlay still attachable.",
        "reads": "convention_check --json, CI conclusion (including projection-drift and contract re-verify), owner=devops rows in the registry.",
        "output": "health/signal: exit code, drift, contract re-verify, device/CI blockers.",
    },
}


def _by_sev(sev, rules=None):
    return [r for r in (rules or R) if r["severity"] == sev]


def _upstream():
    return [r for r in R if r.get("source_type", "upstream") == "upstream"]


def _customer():
    return [r for r in R if r.get("source_type") == "customer"]


def _by_component(comp):
    return [r for r in R if r.get("component", "any") == comp]


def _by_owner(owner):
    return [r for r in R if r.get("owner") == owner]


def _owner_tag(r):
    return r.get("owner", "unassigned")


def _component_globs(comp):
    globs = []
    for r in _by_component(comp):
        for g in r.get("applies_to", []):
            if g not in globs:
                globs.append(g)
    return globs


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"  wrote {path.relative_to(ROOT)}")


# --------------------------------------------------------------------------- #
def build_cursor_core():
    """Always-on agent rules = the component-agnostic (component: any) rules."""
    core = _by_component("any")
    lines = [
        "---",
        'description: diffusers contribution conventions enforced by the Ramp Kit. Applied to all edits.',
        "alwaysApply: true",
        "---",
        BANNER,
        "",
        f"# diffusers conventions (registry v{META['registry_version']})",
        "",
        "You are contributing to `huggingface/diffusers`. Follow these conventions.",
        "They mirror the project's own `.ai/` rules and are enforced by",
        "`tools/convention_check.py` — the same gate that runs in CI, so producing",
        "code that violates a **block** rule will fail the build.",
        "",
        "Use the `diffusers-docs` MCP tool (`search_docs`) to ground answers in the",
        "library's current docs before scaffolding. If that tool is **not** in your",
        "tool list (Cloud Agents skip project `.cursor/mcp.json` unless the launch",
        "MCP dropdown has stdio `python3 -u .cursor/mcp-diffusers-docs.py`), run",
        "`/search-docs <query>`, the `search-docs` skill, or",
        "`python3 tools/docs_mcp_server.py --query \"...\"` — same server.",
        "Do not pull in code or context from outside this repo's approved",
        "boundaries (see `.cursorignore`).",
        "",
        "## Blocking conventions (must satisfy)",
    ]
    for r in _by_sev("block", core):
        lines.append(f"- **{r['id']} — {r['title']}.** {r['agent_hint']}")
    lines.append("")
    lines.append("## Advisory conventions (should satisfy)")
    for r in _by_sev("warn", core):
        lines.append(f"- **{r['id']} — {r['title']}.** {r['agent_hint']}")
    lines.append("")
    lines.append("Component-specific rules auto-attach when you open a matching file")
    lines.append("(e.g. a scheduler). Prefer copying an existing in-repo example with a")
    lines.append("`# Copied from` marker over inventing a new pattern.")
    lines.append("")
    write(ROOT / ".cursor" / "rules" / "00-conventions.mdc", "\n".join(lines))


def build_cursor_component(comp: str):
    """One auto-attached .mdc per component, generated from its tagged rules."""
    rules = _by_component(comp)
    if not rules:
        return
    label = COMPONENTS.get(comp, {}).get("label", comp.capitalize())
    globs = _component_globs(comp)
    ref = COMPONENTS.get(comp, {}).get("reference")
    lines = [
        "---",
        f"description: Extra diffusers conventions for {comp}s.",
        "globs: [" + ", ".join(f'"{g}"' for g in globs) + "]",
        "alwaysApply: false",
        "---",
        BANNER,
        "",
        f"# {label} conventions (auto-attached to {comp} files)",
        "",
    ]
    for r in rules:
        lines.append(f"### {r['id']} — {r['title']}  ({r['severity']}, owner: {_owner_tag(r)})")
        lines.append(r["rationale"].strip())
        lines.append(f"*How:* {r['agent_hint']}")
        lines.append("")
    if ref:
        lines.append(f"Reference implementation: `{ref}`.")
    lines.append(f"Start from the scaffold: `/scaffold {comp} <Name>` — do not start from a blank file.")
    lines.append("")
    write(ROOT / ".cursor" / "rules" / f"10-{comp}.mdc", "\n".join(lines))


def build_agents_md():
    lines = [
        "<!-- Root AGENTS.md — read natively by Cursor, Codex, Claude Code, and others. -->",
        BANNER,
        "",
        f"# Contributing to {META['library']} (Ramp Kit)",
        "",
        "This repo uses convention-as-code. The authoritative rules live in",
        "`conventions/rules.yaml` and are enforced by `tools/convention_check.py`.",
        "Before opening a PR, run `make check` and fix every blocking finding.",
        "Ground your work with the `diffusers-docs` MCP tool (`search_docs`).",
        "If that tool is missing (Cloud Agents skip project `.cursor/mcp.json`",
        "unless the MCP dropdown is `python3 -u .cursor/mcp-diffusers-docs.py`),",
        "run `/search-docs <query>`, the `search-docs` skill, or",
        "`python3 tools/docs_mcp_server.py --query \"...\"` — same server.",
        "",
        "## Conventions",
    ]
    lines.append("")
    lines.append("### Upstream conventions (what diffusers itself requires)")
    for r in _upstream():
        tag = "MUST" if r["severity"] == "block" else "SHOULD"
        comp = r.get("component", "any")
        lines.append(
            f"- **[{tag}] {r['id']} {r['title']}** ({comp}, owner: {r.get('owner', '?')}) — {r['agent_hint']} (source: {r['source']})"
        )
    cust = _customer()
    if cust:
        lines.append("")
        lines.append("### Customer guardrails (what OUR org additionally requires)")
        for r in cust:
            tag = "MUST" if r["severity"] == "block" else "SHOULD"
            comp = r.get("component", "any")
            lines.append(f"- **[{tag}] {r['id']} {r['title']}** ({comp}, owner: {r.get('owner', '?')}) — {r['agent_hint']} (source: {r['source']})")
    comp_list = ", ".join(f"`/scaffold {c} <Name>`" for c in COMPONENTS) or "(none configured)"
    lines.extend([
        "",
        "## Boundaries",
        "Do not import or copy code from outside this repository. `.cursorignore`",
        "marks paths that are off-limits as agent context.",
        "",
        "## First task",
        "Ground first (`/search-docs` or MCP `search_docs`), then scaffold:",
        f"{comp_list}. See `.cursor/commands/scaffold.md`.",
        "",
    ])
    write(ROOT / "AGENTS.md", "\n".join(lines))


def build_pm_dod():
    lines = [
        BANNER, "",
        "# Definition of Done — a diffusers contribution", "",
        "_For PMs and tech leads. Generated from the same rules the agent and CI use,",
        "so \"done\" means the same thing to everyone. Each item is machine-checked",
        "unless marked (manual)._", "",
        "A change is **Done** when:", "",
        "## Correctness & conventions (auto-verified by `make check`)",
    ]
    for r in _by_sev("block"):
        lines.append(f"- [ ] **{r['title']}** — {r['dod']} `[{r['id']}]` · owner: `{_owner_tag(r)}`")
    lines.append("")
    lines.append("## Quality (advisory, reviewer confirms)")
    for r in _by_sev("warn"):
        lines.append(f"- [ ] {r['dod']} `[{r['id']}]` · owner: `{_owner_tag(r)}`")
    lines.extend([
        "", "## Lifecycle (manual)",
        "- [ ] Coordinated on an issue before the PR (per AI-contribution policy)",
        "- [ ] PR description lists the test commands run and their output",
        "- [ ] Green CI (the convention gate + test suite) before merge", "",
        "## Owners (same registry, role-filtered view)",
        "Each rule has a single `owner` in `conventions/rules.yaml`. Roles co-author one list; they do not get a second source of truth.",
        "",
    ])
    for owner in ALLOWED_OWNERS:
        owned = _by_owner(owner)
        if not owned:
            continue
        lines.append(f"### `{owner}`")
        for r in owned:
            lines.append(f"- `{r['id']}` {r['title']}")
        lines.append("")
    lines.extend([
        "> Impact: every item above maps to a specific ramp mistake or review",
        "> round-trip. Shipping this closes the loop between \"first commit\" and",
        "> \"safely deployed\" without a human re-teaching the conventions each time.", "",
    ])
    write(ROOT / "projections" / "pm" / "definition-of-done.md", "\n".join(lines))


def build_qa_checklist():
    lines = [
        BANNER, "",
        "# Reviewer / QA checklist", "",
        "_The convention gate already blocks the machine-checkable items; your",
        "attention goes to judgment. Auto-checked items are listed so you can trust",
        "them, not re-verify them by hand._", "",
        "## Trust the gate (already enforced, do not re-check by hand)",
    ]
    for r in _by_sev("block"):
        lines.append(f"- `{r['id']}` {r['review_prompt']} _(owner: {_owner_tag(r)})_")
    lines.append("")
    lines.append("## Use your judgment (advisory / not fully automatable)")
    for r in _by_sev("warn"):
        tier = " _(customer guardrail)_" if r.get("source_type") == "customer" else ""
        lines.append(f"- `{r['id']}` {r['review_prompt']}{tier} _(owner: {_owner_tag(r)})_")
    lines.extend([
        "", "## Beyond the gate (human-only)",
        "- Is the numerical method actually correct vs. the paper?",
        "- Is this the right abstraction, or does it duplicate an existing scheduler?",
        "- Are the tests meaningful (determinism, shape, dtype) or just present?", "",
    ])
    write(ROOT / "projections" / "qa" / "review-checklist.md", "\n".join(lines))


def _ci_gate_yml():
    """Same workflow text for the DevOps projection and the real GitHub Action."""
    return "\n".join([
        BANNER_HASH,
        "name: convention-gate",
        "on:",
        "  pull_request:",
        "  push:",
        "    branches: [main]",
        "jobs:",
        "  convention-gate:",
        "    runs-on: ubuntu-latest  # no GPU needed",
        "    steps:",
        "      - uses: actions/checkout@v4",
        "      - uses: actions/setup-python@v5",
        "        with:",
        '          python-version: "3.11"',
        "      - run: pip install -r requirements.txt",
        "      - name: Convention gate",
        "        run: python tools/convention_check.py --all",
        "      - name: Projection drift",
        "        run: python tools/build_projections.py && git diff --exit-code",
        "      - name: Scheduler contract re-verify",
        "        run: python tools/verify_scheduler_contract.py",
        "      - name: MCP doc-server self-test",
        "        run: python tools/docs_mcp_server.py --selftest",
        "      - name: Contract tests",
        "        run: python -m unittest discover -s tests -t .",
        "      - name: Machine-readable report",
        "        if: always()",
        "        run: python tools/convention_check.py --all --json > convention-report.json",
        "      - uses: actions/upload-artifact@v4",
        "        if: always()",
        "        with:",
        "          name: convention-report",
        "          path: convention-report.json",
        "",
    ])


def build_devops():
    md = [
        BANNER, "",
        "# CI gate — DevOps view", "",
        "The convention gate is one command with a meaningful exit code, so it drops",
        "into any CI system. Exit code = number of blocking findings (0 = pass).",
        "The same YAML is written to `.github/workflows/convention-gate.yml` so a",
        "clone actually runs it — the projection is the human explanation.", "",
        "```bash",
        "pip install -r requirements.txt",
        "python tools/convention_check.py --all --json > convention-report.json",
        "python tools/convention_check.py --all   # human-readable, sets exit code",
        "```", "",
        "- **Blocking** findings fail the job. **Warnings** are reported, never fail.",
        "- `--json` output is stable for dashboards / PR annotations.",
        "- No GPU, no model downloads, no network — runs on the cheapest runner.",
        "- Same script runs in the editor hook and pre-PR, so CI surprises are rare.",
        "- Green gate = merge-eligible (release clearance). This kit does not",
        "  deploy; it is the check that a change is allowed to move toward release.",
        "- **Projection drift:** `python tools/build_projections.py && git diff --exit-code`",
        "  fails if a generated surface was hand-edited instead of `rules.yaml`.",
        "- **Scheduler contract re-verify:** `python tools/verify_scheduler_contract.py`",
        "  fails if fork reference source drifted from SCHED001–003.",
        "- Rules carry an `owner` tag (`dev` / `architect` / `qa` / `pm` / `devops`).",
        "  GrokBot role-agents translate gate JSON for that owner; they never gate.",
        "",
        "## Owner-tagged rules (devops)",
    ]
    for r in _by_owner("devops"):
        md.append(f"- `{r['id']}` {r['title']} ({r['severity']})")
    md.append("")
    write(ROOT / "projections" / "devops" / "ci-gate.md", "\n".join(md))
    yml = _ci_gate_yml()
    write(ROOT / "projections" / "devops" / "ci-gate.yml", yml)
    write(ROOT / ".github" / "workflows" / "convention-gate.yml", yml)


def build_github_templates():
    """Planning / review surfaces for PM and the author — same blocking rules."""
    pr = [
        BANNER, "",
        "## Summary",
        "",
        "## Convention gate",
        "Run `make check` and `make test` before requesting review.",
        "Blocking items (auto-verified; still confirm you ran the commands):",
        "",
    ]
    for r in _by_sev("block"):
        pr.append(f"- [ ] `{r['id']}` {r['title']} — {r['dod']} _(owner: {_owner_tag(r)})_")
    pr.extend([
        "",
        "## Tests run",
        "```",
        "make check",
        "make test",
        "```",
        "",
        "## Human judgment (not the gate)",
        "- [ ] Numerical method is correct vs. the paper / spec (QA)",
        "- [ ] This does not duplicate an existing scheduler/model/pipeline",
        "",
    ])
    write(ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md", "\n".join(pr))

    issue = [
        BANNER, "",
        "# Contribution intake", "",
        "_PM / tech-lead planning surface. Generated from the same rules the",
        "agent, reviewer, and CI use, so \"what we're building\" matches \"done\".",
        "",
        "## What is changing?",
        "- [ ] Scheduler (`/scaffold scheduler <Name>`)",
        "- [ ] Other (describe)",
        "",
        "## Definition of Done (blocking — `make check`)",
    ]
    for r in _by_sev("block"):
        issue.append(f"- [ ] {r['dod']} `{r['id']}` _(owner: {_owner_tag(r)})_")
    issue.extend([
        "",
        "## Out of scope for the gate (human)",
        "- Numerical correctness vs. the paper",
        "- Whether this abstraction should exist",
        "",
        "## First command",
        "`/scaffold scheduler <Name>` then `make check`.",
        "",
    ])
    write(ROOT / ".github" / "ISSUE_TEMPLATE" / "contribution.md", "\n".join(issue))


def build_grokbot_specs():
    """READ-side role agents. Prompt body is the owner-tagged rules; they never gate."""
    for role, spec in GROKBOT_ROLES.items():
        owned = _by_owner(role)
        lines = [
            BANNER, "",
            f"# GrokBot {role.upper()} — {spec['title']}",
            "",
            "> **Simulation / read-side view.** This agent TRANSLATES gate and CI",
            "> output. It never decides, never fails a job, never merges.",
            "",
            "## Job",
            spec["job"],
            "",
            "## Reads (inputs)",
            spec["reads"],
            "",
            "## Output shape",
            spec["output"],
            "",
            "## Prompt (generated from `conventions/rules.yaml` where `owner:` is "
            f"`{role}`)",
            "",
        ]
        if not owned:
            lines.append("_No rules tagged for this owner in the registry._")
            lines.append("")
        for r in owned:
            tag = r["severity"].upper()
            lines.append(f"### {r['id']} [{tag}] — {r['title']}")
            lines.append(r["rationale"].strip())
            lines.append(f"- Review: {r['review_prompt']}")
            lines.append(f"- Done: {r['dod']}")
            lines.append("")
        lines.extend([
            "## How to run the simulation",
            "",
            "```bash",
            f"python tools/convention_check.py --json examples/candidate_scheduler "
            f"> /tmp/gate.json || true",
            f"python tools/grokbot_sim.py --role {role} < /tmp/gate.json",
            "```",
            "",
        ])
        write(ROOT / "agents" / f"grokbot-{role}.md", "\n".join(lines))


def validate_sync():
    """Fail loudly if a rule references a check that isn't implemented."""
    sys.path.insert(0, str(ROOT / "tools"))
    import convention_check as cc  # noqa
    declared = {r["check"] for r in R}
    implemented = set(cc.CHECKS.keys())
    missing = declared - implemented
    if missing:
        sys.stderr.write(f"ERROR: rules reference unimplemented checks: {missing}\n")
        sys.exit(1)
    # every configured component should have at least one rule
    tagged = {r.get("component", "any") for r in R}
    for c in COMPONENTS:
        if c not in tagged:
            sys.stderr.write(f"WARNING: component '{c}' has no rules tagged for it\n")
    missing_owner = [r["id"] for r in R if r.get("owner") not in ALLOWED_OWNERS]
    if missing_owner:
        sys.stderr.write(
            f"ERROR: rules missing valid owner {ALLOWED_OWNERS}: {missing_owner}\n"
        )
        sys.exit(1)
    print(
        f"  sync OK: {len(R)} rules, all checks implemented, all owners set; "
        f"components: {sorted(tagged)}"
    )


def main():
    print("Building audience projections from conventions/rules.yaml ...")
    validate_sync()
    build_cursor_core()
    for comp in sorted({r.get("component", "any") for r in R} - {"any"}):
        build_cursor_component(comp)
    build_agents_md()
    build_pm_dod()
    build_qa_checklist()
    build_devops()
    build_github_templates()
    build_grokbot_specs()
    print("Done. Humans edit ONLY conventions/rules.yaml; everything above is generated.")


if __name__ == "__main__":
    main()
