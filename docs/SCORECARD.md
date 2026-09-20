# Scorecard — five requirements

Honest mapping. Load-bearing means a reviewer can fail the change if it is
missing. Cosmetic means it only restates the same facts in another file.

| # | Requirement | Verdict | Evidence | Load-bearing or cosmetic |
|---|-------------|---------|----------|--------------------------|
| 1 | Scaffold a correct first contribution without reading the whole library | **MET** | `/scaffold` copies overlay templates; file-scoped gate on the new scheduler + matching test. Prompt A / overlay scaffold stop at `rules.yaml` blocking ids — they do not send the engineer into Euler/DDPM source, docs pages, or public exports. `verify_scheduler_contract.py` still checks fork source when *we* refresh the YAML. | Load-bearing: a scaffold that fails SCHED001–003 cannot ship. |
| 2 | Catch mistakes early; strengthen tests (deprecated APIs, anti-patterns, **missing or weak tests**) | **MET** | Existing gate (DEPR001, DEVICE001, MUT001, TEST001). **TEST002** (`test_adequacy`): empty `test_*` functions, same-seed determinism, shape **and** dtype. Verify: zero-assertion tempfile is flagged; `examples/scaffolded_scheduler` is 0 findings. | Load-bearing: TEST002 is `severity: block`. |
| 3 | Fit CI; stay in approved context boundaries | **MET** | Kit CI: `.github/workflows/convention-gate.yml` (`--all` **in-kit only**) + projection drift + contract re-verify. Fork CI: attach copies **`overlay/ramp-kit-overlay.yml`** (file-scoped `convention_check` on changed scheduler/test files; never `--all`; does not delete inherited HF workflows). Overlay `mcp.json` is stdio `diffusers-docs` only (no Hub HTTP). Cloud dropdown: `diffusers-docs-mcp`. `.cursorignore` hides the known-bad fixture. | Load-bearing: kit drift job is red on hand-edited generated files; fork overlay job is the customer check-run; PATH/workspace launcher is the Cloud-safe stdio spawn. |
| 4 | Maintainable without the author | **MET** | `owner` on every rule; `make build` / `make demo-maintain`; `tools/verify_scheduler_contract.py` checks fork reference source vs SCHED001–003 (passes today; renamed `set_timesteps` reports DRIFT). Adding a component remains registry + template, not new machinery. | Load-bearing: missing `owner` or unimplemented `check` fails `build_projections.py`. |
| 5 | One solution, multiple audiences (PM, QA, DevOps) | **MET** | Same registry, `owner` tags, generated specs. **GrokBot sim fuses a role-native change-context** (`examples/change_context.example.json`) with gate JSON: DevOps leads CI/drift/inherited workflows, PM leads DoD state + merge-eligibility + issue (status-view, not an authored gate), QA leads test-adequacy + residual math risk. Every claim is tagged `[gate]`/`[ci]`/`[issue]`/`[drift]`; each role has a **Cannot see** section. `grokbot_sim.py --role {qa,pm,devops} --context …` never gates. iOS steps: `docs/GROKBOT.md`. | Load-bearing: role-native sim + grounding tags + owner field. Specs without the sim would be cosmetic. |

## Self-score

**4.5 / 5** as a screen artifact. All five requirements have a runnable verify.
I do not claim Bots auto-appear in the iPhone app (no create-from-git API),
Hugging Face CI green on a fork demo, or numerical correctness of `step()`.

## Where it breaks

- **Structure, not math.** A scheduler that matches the interface and computes
  nonsense still passes. QA checklist says so; TEST002 does not change that.
- **Grok Bot app does not import git.** Paste `make grokbot-pack` into Edit
  Profile. `grokbot_sim.py` is still the reproducible briefing; it will not
  page a human or comment on a PR.
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
