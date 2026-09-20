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
  agents/grokbot-{pm,qa,devops}.md       (GrokBot specs; read-side)
  agents/grokbot-profiles.md             (paste-ready iPhone / desktop profiles)
  .cursor/agents/grokbot-*.md            (Cursor subagents if Grok Bot spawns a Cloud Agent)

SCALING PROOF: the per-component rule files are generated from each rule's
`component:` tag. Add rules tagged `component: model` and a `10-model.mdc`
appears automatically — no code change here. Humans edit ONLY rules.yaml.

It also validates that every rule's `check` is implemented in convention_check
(and vice-versa), so a rule can't be documented-but-unenforced.
"""
from __future__ import annotations

import json
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
KIT_REPO = "https://github.com/alex-16moro/diffuser_agent"
KIT_DIR = "/workspace/diffuser_agent"
# Paste order for the iPhone pack: QA is the live-demo role.
GROKBOT_PACK_ORDER = ("qa", "pm", "devops")
GROKBOT_TRIGGER = (
    "Primary: GitHub `pull_request` **opened** (including draft), **synchronize** "
    "(new commits), and **ready_for_review**. A first-contribution briefing is a "
    "decision aid while the PR is still reviewable."
)
GROKBOT_TRIGGER_DEVOPS_MERGE = (
    "Optional DevOps-only follow-up: `pull_request` **closed** as merged — a "
    "short 'landed on main, overlay/CI still healthy?' note. QA and PM do not "
    "brief on merge. Merge is never a ship/no-ship or QA risk event."
)
GROKBOT_GROUNDING = (
    "Every briefing claim cites its source signal: `[gate]` (findings / "
    "blocking count / mechanical merge-eligibility), `[ci]` (convention_gate "
    "/ inherited_workflows), `[issue]` (PR number, title, issue, milestone, "
    "labels, draft, declared `state`), or `[drift]` (drift_check). Do not "
    "assert a value with no signal. Never invent dates, velocity, or "
    "deploy-env facts. This bot never gates, never merges, never fails CI."
)
GROKBOT_ROLES = {
    "pm": {
        "bot_name": "Ramp Kit PM",
        "bot_title": "Status digest",
        "title": "PM status digest",
        "job": (
            "When a first-contribution PR is opened or updated, tell PM the "
            "live DoD state and merge-eligibility. PM is a status-view role — "
            "value is the live DoD, not an authored gate. Never invent "
            "timelines or velocity."
        ),
        "reads": (
            "ONE change-context (pr.number/title/issue/milestone/labels/draft, "
            "ci.*, state) fused with file-scoped convention_check JSON. Offline "
            "stand-in: examples/change_context.example.json. Owner=pm rows "
            "(DOC001, warn). projections/pm/definition-of-done.md."
        ),
        "output": (
            "status digest: declared DoD state, mechanical merge-eligibility "
            "from gate blocking, issue/milestone. Scaffold ≠ product-done."
        ),
        "cannot_see": (
            "Team velocity / sprint capacity. Roadmap dependencies beyond this "
            "PR's issue/milestone. Calendar ship dates."
        ),
        "briefing": """\
Write a PM digest a non-engineer can use. Lead with DoD state and
merge-eligibility, then issue/milestone. Fuse the change-context with
the gate — one briefing. Do not dump rule ids without translation.

### DoD state
Lead with context.state (`scaffolded` | `gate-green` | `tests-pass` |
`merge-eligible`). Say plainly: scaffold ≠ product-done.

### Merge-eligibility
YES only if gate blocking count is 0 `[gate]`. Else NO. Product-done is
a human call; a green scaffold is not a shipped scheduler.

### Issue / milestone
From context.pr.issue and context.pr.milestone `[issue]`. If missing,
say you cannot see it — do not guess.

### PM-owned registry rows
DOC001 is warn/docs, not a scope gate. PM does not own a blocking check.
Value is the live DoD view, not an authored gate.

### Call
Mechanical merge-eligible: YES/NO `[gate]`. Product-done: NO on a
scaffold `[issue]`. Next human action in one tagged line. No ETA.""",
    },
    "qa": {
        "bot_name": "Ramp Kit QA",
        "bot_title": "Risk briefing",
        "title": "QA risk briefing",
        "job": (
            "When a first-contribution PR is opened or updated, tell QA — from a "
            "testing point of view — test adequacy (owner=qa) and residual math "
            "risk."
        ),
        "reads": (
            "ONE change-context fused with file-scoped convention_check JSON "
            "(owner=qa rows TEST001/TEST002 first). Offline stand-in: "
            "examples/change_context.example.json. PR diff (scheduler + test), "
            "projections/qa/review-checklist.md."
        ),
        "output": (
            "QA risk briefing: test-adequacy first, then residual human risk "
            "(math, duplication, missing integration)."
        ),
        "cannot_see": (
            "Real numerical correctness vs the paper. Whether the sampler "
            "duplicates EulerDiscrete in meaning. GPU pipeline integration."
        ),
        "briefing": """\
Write a QA & testing summary. Lead with test adequacy (owner=qa rules),
then residual math risk. Fuse the change-context with the gate.

### Test adequacy
TEST001/TEST002: presence, assertions, same-seed determinism,
shape/dtype `[gate]`. Note skipped behavioral tests when torch is absent.

### Residual math risk
Numerical method vs the paper is outside the gate. Overlay-green is not
"tested." Duplication of an existing scheduler (e.g. EulerDiscrete).

### Ask of QA
What a human must still judge before this can be called quality-complete.
Do not treat overlay clearance as a pass on the sampler.""",
    },
    "devops": {
        "bot_name": "Ramp Kit DevOps",
        "bot_title": "Health signal",
        "title": "DevOps health signal",
        "job": (
            "When a first-contribution PR is opened or updated, tell DevOps the "
            "pipeline health: CI conclusion, drift_check, inherited_workflows. "
            "Do not lead with scheduler findings."
        ),
        "reads": (
            "ONE change-context (ci.convention_gate, ci.drift_check, "
            "ci.inherited_workflows) fused with file-scoped convention_check "
            "JSON. Offline stand-in: examples/change_context.example.json. "
            "Owner=devops rows."
        ),
        "output": (
            "CI/CD impact summary: convention_gate, drift, inherited "
            "workflows, then mechanical RED/GREEN. Not a scheduler recap."
        ),
        "cannot_see": (
            "Production deploy environment. Whether inherited Hugging Face CI "
            "will go green on this fork. Secrets and runner-fleet health."
        ),
        "briefing": """\
Write a CI/CD impact note. Lead with pipeline health (CI conclusion,
drift_check, inherited_workflows) — not scheduler findings. Cheap
pipeline first. Do not "fix" red HF jobs by deleting inherited workflows.

### Pipeline health
`[ci]` convention_gate. `[drift]` drift_check. `[ci]` inherited_workflows.
File-scoped overlay gate vs `--all` on the library (forbidden).

### Overlay vs upstream CI
Overlay 0 findings = customer clearance. Inherited Hugging Face Actions
may be red on a fork demo — expected, not a reason to disable them.

### Signal
RED if overlay blocking > 0 `[gate]`. GREEN mechanical ≠ upstream-green.

### Optional: after merge (DevOps only)
If the event is `closed` and merged, write four lines max: landed on
which branch/SHA, overlay MCP still empty / attachable, inherited HF
workflows left alone, signal on main. Do not rewrite the pre-merge
briefing. Do not treat merge as QA or PM clearance.""",
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
        "  GrokBot role-agents brief a first-contribution PR for that owner; they never gate.",
        "  Specs: `agents/grokbot-*.md` (repo wins). Trigger: PR opened/updated.",
        "  Optional DevOps-only: closed-as-merged landed note.",
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


def _owned_ids(role: str) -> str:
    ids = [r["id"] for r in _by_owner(role)]
    return ", ".join(ids) if ids else "(none)"


def _trigger_text(role: str) -> str:
    if role == "devops":
        return GROKBOT_TRIGGER + " " + GROKBOT_TRIGGER_DEVOPS_MERGE
    return GROKBOT_TRIGGER + " QA and PM do not brief on merge."


def _grokbot_profile_description(role: str, spec: dict) -> str:
    """Short Edit Profile stub. The long spec lives in agents/grokbot-<role>.md."""
    if role == "devops":
        trigger = (
            "Trigger: GitHub pull_request opened (including draft), synchronize, "
            "or ready_for_review. Optional follow-up: closed-as-merged, four-line "
            "landed note only. Never treat merge as a ship decision."
        )
    else:
        trigger = (
            "Trigger: GitHub pull_request opened (including draft), synchronize, "
            "or ready_for_review. Do not brief on merge."
        )
    return (
        f"You are {spec['bot_name']}.\n\n"
        "Standing orders — do not violate:\n"
        "- Read-side only. Never gate, never fail CI, never merge, never approve a PR.\n"
        f"- Every job: if {KIT_DIR} is missing, clone {KIT_REPO} there; then "
        f"`git -C {KIT_DIR} pull`.\n"
        f"- Read `{KIT_DIR}/agents/grokbot-{role}.md` and follow THAT file. "
        "It wins over this description and over memory of older instructions.\n"
        f"- {trigger}\n"
        f"- Job: {spec['job']}\n"
        "- Keep iPhone replies short. One briefing per PR event."
    )


def _grokbot_first_message(role: str, spec: dict) -> str:
    merge_line = (
        "3. Confirm: role, PR-opened trigger, optional closed-as-merged "
        "landed note only, never gate/merge.\n"
        if role == "devops"
        else "3. Confirm: role, PR-opened trigger (not merge), never gate/merge.\n"
    )
    wait_line = (
        "4. Wait for a PR URL (kit or alex-16moro/diffusers). On opened/"
        "synchronize/ready_for_review, pull again, re-read the spec, brief."
        + (
            " On merged, four-line landed note only."
            if role == "devops"
            else " On merge, do nothing."
        )
    )
    return (
        f"You are {spec['bot_name']}. From now on the repo spec wins.\n\n"
        f"1. Clone {KIT_REPO} into {KIT_DIR} if missing, then "
        f"`git -C {KIT_DIR} pull`.\n"
        f"2. Read {KIT_DIR}/agents/grokbot-{role}.md. Ignore older instructions.\n"
        + merge_line
        + wait_line
    )


def _grokbot_routine(role: str, spec: dict) -> str:
    extra = (
        "5. If the PR is a merge event, skip this routine (use the optional "
        "landed-on-main routine instead)."
        if role == "devops"
        else "5. If the PR is a merge event, do nothing."
    )
    return (
        f"Trigger: GitHub pull_request opened / synchronize / ready_for_review "
        f"(not merged). You are {spec['bot_name']}.\n\n"
        f"1. git -C {KIT_DIR} pull || git clone {KIT_REPO} {KIT_DIR}\n"
        f"2. Read {KIT_DIR}/agents/grokbot-{role}.md — that file wins.\n"
        "3. Open the PR. File-scoped convention_check on changed scheduler/"
        f"test files only (never --all). Kit tools live in {KIT_DIR}/tools "
        "or ramp-kit/tools on the fork. Fuse PR/CI/state with that JSON "
        "(offline: examples/change_context.example.json).\n"
        "4. Write the role briefing from the spec. Every claim cites "
        "[gate]/[ci]/[issue]/[drift]. Include Cannot see. Optional: one "
        "PR comment with that briefing. Do not approve, "
        "request-changes-as-gate, merge, or fail a job.\n"
        + extra
    )


def _grokbot_merge_routine() -> str:
    return (
        "Trigger: GitHub pull_request closed (merged only). You are Ramp Kit DevOps.\n\n"
        "Optional follow-up, not the primary briefing. QA and PM stay silent.\n"
        f"1. git -C {KIT_DIR} pull || git clone {KIT_REPO} {KIT_DIR}\n"
        f"2. Read {KIT_DIR}/agents/grokbot-devops.md — that file wins.\n"
        "3. If closed without merge, do nothing.\n"
        "4. Four lines max: landed branch/SHA; overlay MCP still empty / "
        "attachable; inherited HF workflows untouched; signal on main.\n"
        "5. Do not re-run the QA/PM digest. Do not approve, merge, or fail a job."
    )


def build_grokbot_specs():
    """READ-side role agents. Repo spec wins; Edit Profile is a short stub."""
    for role, spec in GROKBOT_ROLES.items():
        owned = _by_owner(role)
        lines = [
            BANNER, "",
            f"# GrokBot {role.upper()} — {spec['title']}",
            "",
            "> **This file is the Bot's instructions.** Grok Bot does not import",
            "> git. Edit Profile is a stub that says: `git pull`, then read this",
            "> file. This file wins over memory and over the profile text.",
            "> Read-side only: never gate, never fail CI, never merge.",
            "",
            "## Trigger",
            _trigger_text(role),
            "",
            "## Job",
            spec["job"],
            "",
            "## Every run (do this first)",
            "",
            "```bash",
            f"test -d {KIT_DIR}/.git || git clone {KIT_REPO} {KIT_DIR}",
            f"git -C {KIT_DIR} pull --ff-only",
            f"# then re-read {KIT_DIR}/agents/grokbot-{role}.md",
            "```",
            "",
            "## Reads (inputs)",
            spec["reads"],
            "",
            "## Role-native input",
            "Fuse ONE change-event (PR + CI + declared state) with the gate JSON.",
            "Offline demo: `examples/change_context.example.json` via",
            f"`python3 tools/grokbot_sim.py --role {role} --context examples/change_context.example.json`.",
            "",
            "## Briefing to write",
            spec["briefing"].rstrip(),
            "",
            f"Owner-tagged registry rows (`owner: {role}`): `{_owned_ids(role)}`.",
            "Use them as checklist context, not as the whole briefing.",
            "",
            "## Grounding",
            GROKBOT_GROUNDING,
            "",
            "## Cannot see",
            spec["cannot_see"],
            "",
            "## Owner-tagged rules (appendix)",
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
            "## Gate helper (findings only — not the briefing)",
            "",
            "File-scope on the PR's new scheduler/test. Never `--all` on the",
            "library tree. On the fork, tools are `ramp-kit/tools/`.",
            "",
            "```bash",
            "python3 tools/convention_check.py --json <changed.py> > /tmp/gate.json || true",
            "```",
            "",
            "## Routine (paste into Grok Bot desktop — not iPhone)",
            "",
            "```",
            _grokbot_routine(role, spec),
            "```",
            "",
        ])
        if role == "devops":
            lines.extend([
                "## Optional routine — landed on main (DevOps only)",
                "",
                "```",
                _grokbot_merge_routine(),
                "```",
                "",
            ])
        write(ROOT / "agents" / f"grokbot-{role}.md", "\n".join(lines))
    build_grokbot_profiles()
    build_cursor_grokbot_agents()


def build_grokbot_profiles():
    """Paste-ready Name / Title / stub Description. Long spec is agents/grokbot-*.md."""
    lines = [
        BANNER, "",
        "# Grok Bot profiles (iPhone + desktop)",
        "",
        "Grok Bot does **not** import git. Paste this **short stub** into",
        "**Edit Profile** once. The Bot `git pull`s the kit and reads",
        "`agents/grokbot-<role>.md` on every PR. Re-paste the stub only if",
        "Name/Title/standing orders change. Full briefing text: those spec",
        "files. Steps: `docs/GROKBOT.md`.",
        "",
        "Trigger: **PR opened / synchronize / ready_for_review** for all three.",
        "Optional DevOps-only: **closed as merged** (four-line landed note).",
        "QA and PM do not brief on merge. Never gate. Never merge a PR.",
        "",
        f"Kit: `{KIT_REPO}`",
        "",
    ]
    for role in GROKBOT_PACK_ORDER:
        spec = GROKBOT_ROLES[role]
        lines.extend([
            "---",
            "",
            f"## {spec['bot_name']}",
            "",
            f"**Name:** `{spec['bot_name']}`",
            "",
            f"**Title:** `{spec['bot_title']}`",
            "",
            "**Description** (Edit Profile stub only — keep it short):",
            "",
            "```",
            _grokbot_profile_description(role, spec),
            "```",
            "",
            "**First message** (one-time, existing Bots too):",
            "",
            "```",
            _grokbot_first_message(role, spec),
            "```",
            "",
            "**Routine** (desktop: New routine → GitHub pull_request opened):",
            "",
            "```",
            _grokbot_routine(role, spec),
            "```",
            "",
        ])
        if role == "devops":
            lines.extend([
                "**Optional routine** (desktop: pull_request closed / merged):",
                "",
                "```",
                _grokbot_merge_routine(),
                "```",
                "",
            ])
    lines.extend([
        "---",
        "",
        "Print with `make grokbot-pack`. After a spec change, `make build`",
        "then `git pull` on the Bot computer — do not re-paste the whole stub",
        "unless the standing orders changed.",
        "",
    ])
    write(ROOT / "agents" / "grokbot-profiles.md", "\n".join(lines))


def build_cursor_grokbot_agents():
    """Cursor subagents so a Cloud Agent spawned from Grok Bot can invoke the roles."""
    agents_dir = ROOT / ".cursor" / "agents"
    for role, spec in GROKBOT_ROLES.items():
        desc = (
            f"{spec['bot_name']}. On PR opened/updated, write a {role} briefing "
            f"from agents/grokbot-{role}.md. Read-only; never merge."
        )
        body = "\n".join([
            "---",
            f"name: grokbot-{role}",
            f"description: {json.dumps(desc)}",
            "model: inherit",
            "readonly: true",
            "---",
            "",
            BANNER,
            "",
            f"You are {spec['bot_name']} ({spec['title']}).",
            "",
            f"Authoritative spec: `agents/grokbot-{role}.md` (re-read it).",
            (
                "Trigger: pull_request opened / synchronize / ready_for_review. "
                "Optional: closed-as-merged four-line landed note."
                if role == "devops"
                else "Trigger: pull_request opened / synchronize / ready_for_review — not merge."
            ),
            "Never gate, never fail a job, never merge.",
            "",
            f"Job: {spec['job']}",
            f"Output: {spec['output']}",
            f"Owner-tagged rules: {_owned_ids(role)}",
            "",
        ])
        write(agents_dir / f"grokbot-{role}.md", body)


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
