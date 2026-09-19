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
- Green gate = merge-eligible (release clearance). This kit does not
  deploy; it is the check that a change is allowed to move toward release.
