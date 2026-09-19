<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->

# CI gate — DevOps view

The convention gate is one command with a meaningful exit code, so it drops
into any CI system. Exit code = number of blocking findings (0 = pass).

```bash
pip install pyyaml --break-system-packages
python tools/convention_check.py --all --json > convention-report.json
python tools/convention_check.py --all   # human-readable, sets exit code
```

- **Blocking** findings fail the job. **Warnings** are reported, never fail.
- `--json` output is stable for dashboards / PR annotations.
- No GPU, no model downloads, no network — runs on the cheapest runner.
- Same script runs in the editor hook and pre-PR, so CI surprises are rare.
