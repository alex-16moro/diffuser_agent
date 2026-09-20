<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->

# Definition of Done — a diffusers contribution

_For PMs and tech leads. Generated from the same rules the agent and CI use,
so "done" means the same thing to everyone. Each item is machine-checked
unless marked (manual)._

A change is **Done** when:

## Correctness & conventions (auto-verified by `make check`)
- [ ] **Schedulers inherit SchedulerMixin and ConfigMixin** — New scheduler is loadable via from_config and saveable via save_config. `[SCHED001]` · owner: `architect`
- [ ] **Schedulers implement the step() / set_timesteps() contract** — Scheduler runs inside a minimal DDPM-style loop without adapter code. `[SCHED002]` · owner: `architect`
- [ ] **Scheduler __init__ is decorated with @register_to_config** — save_config()/from_config() round-trips all constructor arguments. `[SCHED003]` · owner: `architect`
- [ ] **Randomness threads through a generator, never global RNG** — Same seed -> identical output, verified by a determinism test. `[REPRO001]` · owner: `dev`
- [ ] **No hardcoded CUDA/device placement** — Example runs on CPU CI with no code change. `[DEVICE001]` · owner: `devops`
- [ ] **No deprecated/moved import paths** — No ImportError from moved modules. `[DEPR001]` · owner: `architect`
- [ ] **No mutable default arguments** — No shared-mutable-default warnings. `[MUT001]` · owner: `dev`
- [ ] **New schedulers/models ship with a matching test file** — Scheduler has a test that runs in CI (not @slow). `[TEST001]` · owner: `qa`
- [ ] **Scheduler tests assert behaviour, not just presence** — Scheduler tests have assertions, including same-seed determinism and shape/dtype. `[TEST002]` · owner: `qa`

## Quality (advisory, reviewer confirms)
- [ ] No removed kwargs for the pinned version. `[DEPR002]` · owner: `architect`
- [ ] Scheduler imports only torch, config/scheduler mixins, and small utils. `[IMPORT001]` · owner: `architect`
- [ ] `make fix-copies` produces no diff. `[COPY001]` · owner: `architect`
- [ ] No print() in src/. `[LOG001]` · owner: `devops`
- [ ] Public surface is documented. `[DOC001]` · owner: `pm`
- [ ] No debugger calls in committed code. `[CUST001]` · owner: `devops`

## Lifecycle (manual)
- [ ] Coordinated on an issue before the PR (per AI-contribution policy)
- [ ] PR description lists the test commands run and their output
- [ ] Green CI (the convention gate + test suite) before merge

## Owners (same registry, role-filtered view)
Each rule has a single `owner` in `conventions/rules.yaml`. Roles co-author one list; they do not get a second source of truth.

### `dev`
- `REPRO001` Randomness threads through a generator, never global RNG
- `MUT001` No mutable default arguments

### `architect`
- `SCHED001` Schedulers inherit SchedulerMixin and ConfigMixin
- `SCHED002` Schedulers implement the step() / set_timesteps() contract
- `SCHED003` Scheduler __init__ is decorated with @register_to_config
- `DEPR001` No deprecated/moved import paths
- `DEPR002` Avoid deprecated kwargs (verify per release)
- `IMPORT001` Schedulers stay self-contained (no heavy util imports)
- `COPY001` # Copied from markers are well-formed

### `qa`
- `TEST001` New schedulers/models ship with a matching test file
- `TEST002` Scheduler tests assert behaviour, not just presence

### `pm`
- `DOC001` Public methods have docstrings

### `devops`
- `DEVICE001` No hardcoded CUDA/device placement
- `LOG001` Library code logs, it does not print()
- `CUST001` No debugging leftovers committed

> Impact: every item above maps to a specific ramp mistake or review
> round-trip. Shipping this closes the loop between "first commit" and
> "safely deployed" without a human re-teaching the conventions each time.
