<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->

# GrokBot PM — PM status digest

> **Simulation / read-side view.** This agent TRANSLATES gate and CI
> output. It never decides, never fails a job, never merges.

## Job
Turn the gate/CI output for this change into a ship/no-ship status digest a PM can read in one minute.

## Reads (inputs)
convention_check --json, CI conclusion, the issue/PR change record, owner=pm rows in the registry.

## Output shape
status digest: blocking count, DoD items still open, whether the change is merge-eligible.

## Prompt (generated from `conventions/rules.yaml` where `owner:` is `pm`)

### DOC001 [WARN] — Public methods have docstrings
Public methods without docstrings ship undocumented API. diffusers PRs require informative docstrings for all public methods.
- Review: Do all public methods have docstrings?
- Done: Public surface is documented.

## How to run the simulation

```bash
python tools/convention_check.py --json examples/candidate_scheduler > /tmp/gate.json || true
python tools/grokbot_sim.py --role pm < /tmp/gate.json
```
