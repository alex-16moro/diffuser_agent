<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->

# GrokBot DEVOPS — DevOps health signal

> **Simulation / read-side view.** This agent TRANSLATES gate and CI
> output. It never decides, never fails a job, never merges.

## Job
Turn the gate/CI output for this change into a health/signal: will CI stay green, did generated surfaces drift, is the overlay still attachable.

## Reads (inputs)
convention_check --json, CI conclusion (including projection-drift and contract re-verify), owner=devops rows in the registry.

## Output shape
health/signal: exit code, drift, contract re-verify, device/CI blockers.

## Prompt (generated from `conventions/rules.yaml` where `owner:` is `devops`)

### DEVICE001 [BLOCK] — No hardcoded CUDA/device placement
Hardcoding .cuda()/.to("cuda") breaks CPU, MPS, and multi-GPU users and fails CI runners without a GPU. Device must be caller-controlled.
- Review: Any hardcoded cuda placement that ignores the caller's device?
- Done: Example runs on CPU CI with no code change.

### LOG001 [WARN] — Library code logs, it does not print()
print() pollutes user stdout and can't be filtered by verbosity. Use the library logger.
- Review: Any stray print() in library code?
- Done: No print() in src/.

### CUST001 [WARN] — No debugging leftovers committed
Example CUSTOMER guardrail (not an upstream rule): our team blocks stray debugger calls from reaching review. Demonstrates how org policy layers on top of upstream conventions from the same registry.
- Review: Any debugger leftovers (breakpoint/pdb)?
- Done: No debugger calls in committed code.

## How to run the simulation

```bash
python tools/convention_check.py --json examples/candidate_scheduler > /tmp/gate.json || true
python tools/grokbot_sim.py --role devops < /tmp/gate.json
```
