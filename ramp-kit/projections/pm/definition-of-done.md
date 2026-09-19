<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->

# Definition of Done — a diffusers contribution

_For PMs and tech leads. Generated from the same rules the agent and CI use,
so "done" means the same thing to everyone. Each item is machine-checked
unless marked (manual)._

A change is **Done** when:

## Correctness & conventions (auto-verified by `make check`)
- [ ] **Schedulers inherit SchedulerMixin and ConfigMixin** — New scheduler is loadable via from_config and saveable via save_config. `[SCHED001]`
- [ ] **Schedulers implement the step() / set_timesteps() contract** — Scheduler runs inside a minimal DDPM-style loop without adapter code. `[SCHED002]`
- [ ] **Scheduler __init__ is decorated with @register_to_config** — save_config()/from_config() round-trips all constructor arguments. `[SCHED003]`
- [ ] **Randomness threads through a generator, never global RNG** — Same seed -> identical output, verified by a determinism test. `[REPRO001]`
- [ ] **No hardcoded CUDA/device placement** — Example runs on CPU CI with no code change. `[DEVICE001]`
- [ ] **No deprecated/moved import paths** — No ImportError from moved modules. `[DEPR001]`
- [ ] **No mutable default arguments** — No shared-mutable-default warnings. `[MUT001]`
- [ ] **New schedulers/models ship with a matching test file** — Scheduler has a test that runs in CI (not @slow). `[TEST001]`

## Quality (advisory, reviewer confirms)
- [ ] No removed kwargs for the pinned version. `[DEPR002]`
- [ ] Scheduler imports only torch, config/scheduler mixins, and small utils. `[IMPORT001]`
- [ ] `make fix-copies` produces no diff. `[COPY001]`
- [ ] No print() in src/. `[LOG001]`
- [ ] Public surface is documented. `[DOC001]`
- [ ] No debugger calls in committed code. `[CUST001]`

## Lifecycle (manual)
- [ ] Coordinated on an issue before the PR (per AI-contribution policy)
- [ ] PR description lists the test commands run and their output
- [ ] Green CI (the convention gate + test suite) before merge

> Impact: every item above maps to a specific ramp mistake or review
> round-trip. Shipping this closes the loop between "first commit" and
> "safely deployed" without a human re-teaching the conventions each time.
