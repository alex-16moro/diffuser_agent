<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->

# CI gate — DevOps view

The convention gate is one command with a meaningful exit code, so it drops
into any CI system. Exit code = number of blocking findings (0 = pass).
The same YAML is written to `.github/workflows/convention-gate.yml` so a
clone actually runs it — the projection is the human explanation.

```bash
pip install -r requirements.txt
python tools/convention_check.py --all --json > convention-report.json
python tools/convention_check.py --all   # human-readable, sets exit code
```

- **Blocking** findings fail the job. **Warnings** are reported, never fail.
- `--json` output is stable for dashboards / PR annotations.
- No GPU, no model downloads, no network — runs on the cheapest runner.
- Same script runs in the editor hook and pre-PR, so CI surprises are rare.
- Green gate = merge-eligible. Packaging is a separate BUILD-VERIFIED /
  PACKAGING-ELIGIBLE check (`tools/release_check.py`) that runs only on a
  library checkout: pytest tests/others/test_dependencies.py, `python -m build
  --wheel`, then import the new export from the installed wheel with
  PYTHONPATH stripped (site-packages, not src/). Same spirit as
  overlay_pr_gate.py — invoke the team's tooling; not a new product.
  GrokBot DevOps reads that JSON via `--release-json`; it does not run
  `python -m build`. Stops at build-verified. Handoff: customer index,
  creds, and tag. Not CD. Not a required GitHub check on first-contribution PRs.
- **Projection drift:** `python tools/build_projections.py && git diff --exit-code`
  fails if a generated surface was hand-edited instead of `rules.yaml`.
- **Scheduler contract re-verify:** `python tools/verify_scheduler_contract.py`
  fails if fork reference source drifted from SCHED001–003.
- Rules carry an `owner` tag (`dev` / `architect` / `qa` / `pm` / `devops`).
  GrokBot role-agents brief a first-contribution PR for that owner; they never gate.
  Specs: `agents/grokbot-*.md` (repo wins). Trigger: PR opened/updated.
  Optional DevOps-only: closed-as-merged landed note.
- **This kit** runs `.github/workflows/convention-gate.yml` with `--all`.
  **The library fork** must not. Attach copies `overlay/ramp-kit-overlay.yml`
  → `.github/workflows/ramp-kit-overlay.yml` (file-scoped; never `--all`;
  does not delete inherited Hugging Face workflows).

## Owner-tagged rules (devops)
- `DEVICE001` No hardcoded CUDA/device placement (block)
- `LOG001` Library code logs, it does not print() (warn)
- `CUST001` No debugging leftovers committed (warn)
