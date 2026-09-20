<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->

# Reviewer / QA checklist

_The convention gate already blocks the machine-checkable items; your
attention goes to judgment. Auto-checked items are listed so you can trust
them, not re-verify them by hand._

## Trust the gate (already enforced, do not re-check by hand)
- `SCHED001` Does the scheduler inherit both SchedulerMixin and ConfigMixin? _(owner: architect)_
- `SCHED002` Are step() and set_timesteps() both present and returning the Output dataclass? _(owner: architect)_
- `SCHED003` Is __init__ decorated with @register_to_config? _(owner: architect)_
- `REPRO001` Is every sampling call seeded via an explicit generator? _(owner: dev)_
- `DEVICE001` Any hardcoded cuda placement that ignores the caller's device? _(owner: devops)_
- `DEPR001` Any deprecated/moved import path? _(owner: architect)_
- `MUT001` Any mutable default arguments? _(owner: dev)_
- `TEST001` Is there a test file covering the new scheduler? _(owner: qa)_
- `TEST002` Does the scheduler test assert determinism and shape/dtype, with no empty test functions? _(owner: qa)_

## Use your judgment (advisory / not fully automatable)
- `DEPR002` Any renamed kwargs that should use the current name? _(owner: architect)_
- `IMPORT001` Does the scheduler stay self-contained per single-file policy? _(owner: architect)_
- `COPY001` Do all # Copied from markers resolve to a real dotted path? _(owner: architect)_
- `LOG001` Any stray print() in library code? _(owner: devops)_
- `DOC001` Do all public methods have docstrings? _(owner: pm)_
- `CUST001` Any debugger leftovers (breakpoint/pdb)? _(customer guardrail)_ _(owner: devops)_

## Beyond the gate (human-only)
- Is the numerical method actually correct vs. the paper?
- Is this the right abstraction, or does it duplicate an existing scheduler?
- Are the tests meaningful (determinism, shape, dtype) or just present?
