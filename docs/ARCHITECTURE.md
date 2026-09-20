# Architecture & design choices

One page. The trade-offs a reviewer would actually ask about.

## The one decision everything hangs on

**Conventions are data, not prose.** `conventions/rules.yaml` is the single
source of truth; every other file is generated from it. This is the difference
between "we wrote onboarding docs" (drift within a month) and "onboarding is a
build artifact" (regenerated on every change, verified in sync).

Rules are tagged `source_type: upstream` (verified against the diffusers repo)
or `source_type: customer` (the org's own guardrails), and each upstream rule
cites what it was checked against. The scheduler contract was verified against
actual `scheduling_ddpm.py` / `scheduling_euler_discrete.py` source — the code
uses `set_timesteps`; the philosophy doc's older `set_num_inference_steps` is
stale. Source beats prose: that's why the rules are grounded in the repo and a
validator catches drift, instead of trusting docs or memory.

```
rules.yaml ──build_projections.py──> agent rules, AGENTS.md, PM DoD,
     │                                QA checklist, DevOps CI gate,
     │                                GrokBot specs + iPhone profiles (read-side, never gate)
     │                                Cursor subagents (`.cursor/agents/grokbot-*.md`)
     └────────convention_check.py───> the runnable gate (editor / pre-PR / CI)
```

`build_projections.py` refuses to run if a rule declares a `check` that isn't
implemented in `convention_check.py`, or if a rule is missing a valid `owner`
(`dev` / `architect` / `qa` / `pm` / `devops`). Owner tags are the
multi-audience mechanism: roles co-author one registry; GrokBot translates
gate JSON for a role (CLI sim, or paste-ready profiles in the iPhone Grok Bot
app). CI also rebuilds projections and `git diff --exit-code`
(hand-edits of generated files fail) and re-verifies SCHED001–003 against
fork source (`tools/verify_scheduler_contract.py`).

## Why these tools (reasoning from how they actually work)

| Choice | Why, mechanically |
|--------|-------------------|
| **Cursor rules `.mdc` + `AGENTS.md`** | `diffusers` itself wires agents via root `AGENTS.md` (Cursor reads it natively). `.mdc` frontmatter (`globs`, `alwaysApply`) lets scheduler rules auto-attach only on scheduler files — right context, no prompt bloat. |
| **AST for structural rules** | Class bases, method presence, `@register_to_config`, mutable defaults, docstrings are *structure*. AST doesn't false-positive on a comment or a reformat the way grep does. Regex is used only for line-level lexical patterns. |
| **`.cursorignore` for boundaries** | Requirement 3 says "don't pull in context from outside approved boundaries." `.cursorignore` is exactly that mechanism — it removes paths from the agent's context window, so a scaffold can't copy the known-bad fixture (or, in a customer repo, vendored/secret/generated code) toward prod. |
| **`.cursor/hooks.json` `afterFileEdit`** | Runs the gate on the edited file the moment the agent touches it — the same script CI runs — so feedback is instant and CI surprises are rare. The hook reads Cursor's stdin JSON (`file_path`, `edits`). |
| **Empty default MCP + docs CLI** | `.cursor/mcp.json` is `{"mcpServers":{}}`. Grounding is `.ai/` plus reference source. Optional: `python3 tools/docs_mcp_server.py --query`. `--serve` remains in that file as leftover implementation, not a Cursor default. |
| **One script, `--json` + exit code** | Exit code = number of blocking findings makes it a drop-in CI gate anywhere; `--json` feeds dashboards / PR annotations. No GPU, no downloads, no network → cheapest runner. |
| **Tests in stdlib `unittest`** | Runs on a fresh clone with zero installs (structural contract), and layers in numeric determinism when torch is present. The demo can't fail because a wheel didn't download. |

## Why schedulers first

Three components could be scaffolded (models, pipelines, schedulers). I went
deep on schedulers because they have the **crispest enforceable contract**
(`SchedulerMixin`/`ConfigMixin`, `set_timesteps`/`step`, `register_to_config`) —
the best proof that the approach catches *real* mistakes, not lint trivia. The
registry is component-agnostic; adding a `models.md` rule set is additive.

## SDLC coverage (not just codegen)

| Stage | What the kit does |
|-------|-------------------|
| Plan | PM Definition of Done + `.github/ISSUE_TEMPLATE/contribution.md`, generated from the same rules |
| Design | Conventions + reference scheduler; scaffold command encodes the shape |
| Build | Agent rules + `/scaffold <component> <Name>` produce a correct first cut |
| Review | Gate blocks the machine-checkable items; QA checklist focuses humans on judgment |
| Test | Generated contract test (structural + behavioral); TEST001 requires the file; TEST002 requires assertions, same-seed determinism, and shape/dtype |
| CI / Release gate | Identical gate in `.github/workflows/convention-gate.yml` + docs CLI `--query` + tests; `.cursorignore` keeps changes in the agent's context boundary. Green gate = merge-eligible (release clearance). I stop here — no customer deploy env or auth model, so I don't fake "deploy". |

## Failure modes I designed around

- **"The linter just always yells."** → The correct example passes with 0
  findings; warnings never fail CI; every finding carries a fix hint.
- **"It'll rot."** → Generated surfaces carry a DO-NOT-EDIT banner and are
  regenerated; the sync check prevents documented-but-unenforced rules.
- **"It's tied to Cursor."** → The enforcement (`convention_check.py`) is plain
  Python; `AGENTS.md` is tool-agnostic. Cursor is the nice front-end, not a
  lock-in.
