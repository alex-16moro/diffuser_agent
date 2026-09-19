<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->

# Reviewer / QA checklist

_The convention gate already blocks the machine-checkable items; your
attention goes to judgment. Auto-checked items are listed so you can trust
them, not re-verify them by hand._

## Trust the gate (already enforced, do not re-check by hand)
- `SCHED001` Does the scheduler inherit both SchedulerMixin and ConfigMixin?
- `SCHED002` Are step() and set_timesteps() both present and returning the Output dataclass?
- `SCHED003` Is __init__ decorated with @register_to_config?
- `REPRO001` Is every sampling call seeded via an explicit generator?
- `DEVICE001` Any hardcoded cuda placement that ignores the caller's device?
- `DEPR001` Any deprecated/moved import path?
- `MUT001` Any mutable default arguments?
- `TEST001` Is there a test file covering the new scheduler?

## Use your judgment (advisory / not fully automatable)
- `DEPR002` Any renamed kwargs that should use the current name?
- `IMPORT001` Does the scheduler stay self-contained per single-file policy?
- `COPY001` Do all # Copied from markers resolve to a real dotted path?
- `LOG001` Any stray print() in library code?
- `DOC001` Do all public methods have docstrings?
- `CUST001` Any debugger leftovers (breakpoint/pdb)? _(customer guardrail)_

## Beyond the gate (human-only)
- Is the numerical method actually correct vs. the paper?
- Is this the right abstraction, or does it duplicate an existing scheduler?
- Are the tests meaningful (determinism, shape, dtype) or just present?
