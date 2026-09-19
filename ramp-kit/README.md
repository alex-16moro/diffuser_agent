# diffusers Ramp Kit

**A convention-as-code onboarding layer for a large, convention-heavy library
(`huggingface/diffusers`), built so one solution serves the whole team — the
coding agent, the reviewer, PM, QA, and DevOps — across the full path a change
takes: plan → design → build → review → test → deploy.**

Built for the Solutions Architect technical screen. Everything here runs; there
are no screenshots standing in for working software.

---

## The problem I chose to solve (and why it's the right one)

A convention-heavy library like `diffusers` already contains a lot of valuable
engineering knowledge — but it's *distributed*: across the `.ai/` agent guidance,
the docs, the code patterns, the tests, and CI. A new engineer has to reassemble
it before they can ship a safe change (how a scheduler must be structured, which
imports moved last release, what the reviewer will bounce), and they usually
discover each rule the slow way: a red PR, a review round-trip, a broken build.

So the goal isn't to write conventions the library lacks — it already ships an
`.ai/` directory (`AGENTS.md`, `review-rules.md`, on-demand skills) for the agent
and the reviewer. **The goal is to turn those scattered signals into one governed
contribution workflow** that makes the path from task to review-ready change
explicit, enforces it identically everywhere, and extends the value to the rest
of the team — PM, QA, DevOps — which is the gap the customer named.

So I didn't invent a parallel system. **I extended the maintainers' own pattern**
with the one thing that makes conventions trustworthy end-to-end: a single
machine-readable registry that every audience is *projected* from, plus a
runnable gate that enforces it identically in the editor, before the PR, and in
CI. The registry separates **upstream conventions** ("what diffusers requires,"
verified against source) from **customer guardrails** ("what our org adds"), so
nobody confuses the two.

**The business impact:** fewer review round-trips (the highest-cost, highest-
latency step), consistent code from day one, and — because the rules are code,
not tribal knowledge — the team owns and extends it without me (requirement 4).

## The core idea: one source of truth, many audiences

```
                    conventions/rules.yaml   ← humans edit ONLY this
                              │
            ┌─────────────────┼──────────────────────────────┐
   make build │               │ reads                         │ reads
            ▼                 ▼                                ▼
  .cursor/rules/*.mdc   tools/convention_check.py     projections/
  AGENTS.md             (the runnable gate)             pm/definition-of-done.md
  (the coding agent)          │                          qa/review-checklist.md
                              │ same script runs at      devops/ci-gate.yml
                              ▼ three points in the SDLC
                    editor hook → pre-PR (make check) → CI
```

If the rule changes, `make build` regenerates every surface. The agent's
instructions, the reviewer's checklist, the PM's Definition of Done, and the CI
gate **cannot disagree**, because they're the same source rendered five ways.

## The scaling model: fixed primitives, data-driven components

The kit is a **small, fixed set of primitives** — it does *not* grow a bespoke
approach per task type. New components (a model, a pipeline) and new mistakes are
added as **data** (registry rows + a template file + docs), never as new
machinery.

| Primitive | SDLC lane | Audience | Scales by |
|-----------|-----------|----------|-----------|
| Convention registry | correctness / consistency | agent + reviewer | adding rows tagged `component:` |
| Gate (`convention_check.py`) | catch-early + CI | QA + DevOps | reusing existing check types |
| `/scaffold <component> <Name>` | build (first contribution) | engineer | dropping a template file |
| Doc-search **MCP** (`docs_mcp_server.py`) | discovery / grounding | engineer + PM | pointing at more docs |
| Projections | plan / review / deploy | PM / QA / DevOps | fixed audience set |

Concretely: each rule carries a `component:` tag, and `make build` emits one
auto-attached `.cursor/rules/10-<component>.mdc` per component from that tag. Add
rules tagged `component: model` + a template and `/scaffold model X` works with
**zero code changes** (see `templates/README.md`). That's what keeps it reliable
as it grows.

## What maps to which requirement

| # | Requirement | How this kit meets it |
|---|-------------|-----------------------|
| 1 | Scaffold a correct first contribution | `/scaffold <component> <Name>` command + per-component `.cursor/rules/10-*.mdc` + a correct reference (`examples/scaffolded_scheduler/`) + the `diffusers-docs` MCP for grounding |
| 2 | Catch mistakes early, strengthen tests | `tools/convention_check.py` (AST + regex, 14 rules: 13 upstream + 1 example customer guardrail) + generated test scaffold with behavioral contracts; runs in-editor via `.cursor/hooks.json` |
| 3 | Fit CI, stay in approved boundaries | `projections/devops/ci-gate.yml` runs the *same* gate + MCP self-test + tests; `.cursorignore` defines the boundaries the agent can't cross |
| 4 | Stay maintainable as the library evolves | One `rules.yaml` the team edits; add a rule → every surface updates. `build_projections.py` fails if a rule isn't enforced |
| 5 | Work for PM, QA, DevOps too | `projections/pm`, `projections/qa`, `projections/devops` are generated from the same rules |

Built for **Cursor**: rules (`.cursor/rules/*.mdc`), a command
(`.cursor/commands/scaffold.md`), an edit hook (`.cursor/hooks.json`), an MCP
server (`.cursor/mcp.json` → `tools/docs_mcp_server.py`), and boundaries
(`.cursorignore`) — all native Cursor primitives. The enforcement itself is plain
Python, so nothing is locked to Cursor.

## Quickstart (all of this runs)

```bash
pip install pyyaml --break-system-packages     # the only dependency

make build      # regenerate every audience surface from the registry
make demo       # catch the bad scheduler, pass the good one, MCP, run the tests
make check      # run the gate on the whole repo (exit code = # blocking)
make test       # contract tests — zero third-party installs needed
make mcp        # self-test the diffusers-docs MCP server (the Cursor handshake)
make demo-maintain  # add a rule, rebuild, watch it propagate to every surface (req #4)
```

The 90-second demo (`make demo`) shows the whole arc:

1. A new engineer's first-cut scheduler (`examples/candidate_scheduler/`) — the
   gate catches **8 blocking + 2 warnings**, each with a rule id and a fix.
2. The scaffolded, convention-correct version (`examples/scaffolded_scheduler/`) —
   **0 findings**.
3. The `diffusers-docs` MCP server answers a grounded query over the library's
   docs (the same `initialize → tools/list → tools/call` handshake Cursor uses).
4. Contract tests — green, with numeric determinism skipped cleanly when torch
   isn't installed.

## What I deliberately scoped OUT (and why)

- **Embeddings-based ranking for the MCP.** The doc-search MCP server is real and
  Cursor-connectable (`tools/docs_mcp_server.py`, stdlib stdio JSON-RPC), but it
  ranks by keyword TF over a curated corpus, not embeddings. Keyword search over
  good docs is a strong, debuggable baseline with no model download; embeddings
  are the upgrade if recall proves weak.
- **Model/pipeline scaffolds.** I built the scheduler path end-to-end rather than
  a shallow version of all three. Schedulers have the crispest, most enforceable
  contract, so it's the best proof. Adding a component is now a documented
  data change (`templates/README.md`), not a rewrite.
- **Auto-fix.** The gate reports and blocks; it doesn't rewrite code. Auto-fix on
  a numerical library is where you introduce silent, wrong "corrections." I'd add
  it only for mechanical rules (imports, print→logger) later.

## Where it breaks (honest limitations)

- The gate checks **structure and conventions, not correctness of the math.** It
  will happily pass a scheduler that satisfies the interface and computes
  nonsense. That's by design — that's the reviewer's job, and the QA checklist
  says so explicitly.
- `applies_to` globs are heuristic; a scheduler in a non-standard path could be
  missed. Mitigation: the filename-convention fallback (`scheduling_*.py`).
- `# Copied from` sync (COPY001) is a well-formedness check, not the full
  `make fix-copies` graph. Real sync needs the library's own tooling.
- Deprecation coverage is only as current as the `DEPR001/002` maps — which is the
  point: it's a one-line edit in `rules.yaml` when the library moves an API.
  Import-path moves block (deterministic failure); renamed *kwargs* only warn,
  because a bare substring isn't proof of deprecation in a given version.
- **I stop at the CI / release gate, not deployment.** I don't have the customer's
  deploy environment or authorization model, so faking "deploy" would be theatre.
  The gate is where a change is *cleared* to move toward release.
- `.cursorignore` is the agent's **context** boundary, not a security boundary —
  real isolation is filesystem/network/credential/tool permissions in production.

## A note on grounding (why this survives a skeptical reviewer)

The scheduler contract (`set_timesteps` / `step`) was verified on 2026-09-19
against **actual current source** — `scheduling_ddpm.py` and
`scheduling_euler_discrete.py` on `main` — not the philosophy doc, which still
uses the older `set_num_inference_steps` name. When the doc and the code
disagree, the code wins. That's the whole thesis: ground rules in the repository
and let a validator catch staleness, rather than trusting prose or model memory.
Each upstream rule cites what it was checked against in its `source:` field.

## Repo map

```
conventions/rules.yaml          the single source of truth (12 rules, component-tagged)
tools/convention_check.py       the runnable gate (AST + regex)
tools/build_projections.py      renders every audience surface (per-component .mdc)
tools/docs_mcp_server.py        the diffusers-docs MCP server (real stdio JSON-RPC)
knowledge/diffusers-docs/       seed doc corpus for the MCP (override with a real checkout)
templates/                      scaffold templates + "add a component" guide
.cursor/rules/*.mdc             agent conventions (generated; 00-core + 10-<component>)
.cursor/commands/scaffold.md    /scaffold <component> <Name> guided first task
.cursor/hooks.json              run the gate after each edit
.cursor/mcp.json                doc-search MCP wiring
.cursorignore                   approved boundaries (req. 3)
AGENTS.md                       tool-agnostic mirror (generated)
examples/candidate_scheduler/   the "from memory" first cut (fails the gate)
examples/scaffolded_scheduler/     what the scaffold emits (passes)
tests/                          contract tests + template
projections/{pm,qa,devops}/     the multi-audience surfaces (generated)
docs/ARCHITECTURE.md            design choices + trade-offs
docs/TALK_TRACK.md              the 45-min session + stakeholder defense
```
