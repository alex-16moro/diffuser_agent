# Scorecard — five requirements

Honest mapping. Load-bearing means a reviewer can fail the change if it is
missing. Cosmetic means it only restates the same facts in another file.

| # | Requirement | Verdict | Evidence | Load-bearing or cosmetic |
|---|-------------|---------|----------|--------------------------|
| 1 | Scaffold a correct first contribution without reading the whole library | **MET** | `/scaffold` in `.cursor/commands/scaffold.md`; templates; `make demo-contribute`; file-scoped gate on the new scheduler. Grounding: fork `scheduling_ddpm.py` / `scheduling_euler_discrete.py` (`set_timesteps`+`step`, `SchedulerMixin`+`ConfigMixin`, `@register_to_config`) plus `python3 tools/docs_mcp_server.py --query`. | Load-bearing: a scaffold that fails SCHED001–003 cannot ship. |
| 2 | Catch mistakes early; strengthen tests (deprecated APIs, anti-patterns, **missing or weak tests**) | **MET** | Existing gate (DEPR001, DEVICE001, MUT001, TEST001). **TEST002** (`test_adequacy`): empty `test_*` functions, same-seed determinism, shape **and** dtype. Verify: zero-assertion tempfile is flagged; `examples/scaffolded_scheduler` is 0 findings. | Load-bearing: TEST002 is `severity: block`. |
| 3 | Fit CI; stay in approved context boundaries | **MET** | `.github/workflows/convention-gate.yml` (generated) now includes **projection drift** (`build_projections.py && git diff --exit-code`) and **contract re-verify**. `.cursorignore` hides the known-bad fixture. Overlay `mcp.json` is `{ "mcpServers": {} }`; attach copies it. Gate on the fork is file-scoped — never `--all` on the library tree. | Load-bearing: drift job is red on hand-edited generated files; empty MCP is the Cloud-safe default. |
| 4 | Maintainable without the author | **MET** | `owner` on every rule; `make build` / `make demo-maintain`; `tools/verify_scheduler_contract.py` checks fork reference source vs SCHED001–003 (passes today; renamed `set_timesteps` reports DRIFT). Adding a component remains registry + template, not new machinery. | Load-bearing: missing `owner` or unimplemented `check` fails `build_projections.py`. |
| 5 | One solution, multiple audiences (PM, QA, DevOps) | **MET** | Not “the same bullets pasted three times.” **`owner` tags** split the registry by role. Projections group/label by owner. **GrokBot** specs (`agents/grokbot-{pm,qa,devops}.md`) are generated from those tags. `tools/grokbot_sim.py --role qa` prints a **risk briefing** from gate JSON and never gates. | Load-bearing for the multi-audience claim: owner field + role sim. Spec files without the sim would have been cosmetic. |

## Self-score

**4.4 / 5** as a screen artifact. All five requirements have a runnable verify.
I do not claim production GrokBot integrations, Hugging Face CI green on a
fork demo, or numerical correctness of `step()`.

## Where it breaks

- **Structure, not math.** A scheduler that matches the interface and computes
  nonsense still passes. QA checklist says so; TEST002 does not change that.
- **GrokBot is a simulation.** It will not page a human or comment on a PR.
- **Contract re-verify SKIPs** if the library fork is not attached (kit-only
  clone). Adjacent checkout or `--library` is required for a real pass.
- **`applies_to` globs are heuristic.** A scheduler in a weird path can miss
  TEST002; filename fallback (`test_scheduling_*.py`) is the mitigation.
- **Fork GitHub Actions may go red.** Overlay clearance ≠ upstream CI. We do
  not delete inherited workflows.
- **Deprecation maps are only as fresh as the YAML.** Kwargs stay `warn` on
  purpose (substring ≠ proof).
- **`.cursorignore` is a context boundary**, not a security sandbox.

## What I would not pretend

I did not open a PR to `huggingface/diffusers`. I did not implement Euler
math. I did not run `convention_check.py --all` on the full library tree.
