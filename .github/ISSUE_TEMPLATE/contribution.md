<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->

# Contribution intake

_PM / tech-lead planning surface. Generated from the same rules the
agent, reviewer, and CI use, so "what we're building" matches "done".

## What is changing?
- [ ] Scheduler (`/scaffold scheduler <Name>`)
- [ ] Other (describe)

## Definition of Done (blocking — `make check`)
- [ ] New scheduler is loadable via from_config and saveable via save_config. `SCHED001` _(owner: architect)_
- [ ] Scheduler runs inside a minimal DDPM-style loop without adapter code. `SCHED002` _(owner: architect)_
- [ ] save_config()/from_config() round-trips all constructor arguments. `SCHED003` _(owner: architect)_
- [ ] Same seed -> identical output, verified by a determinism test. `REPRO001` _(owner: dev)_
- [ ] Example runs on CPU CI with no code change. `DEVICE001` _(owner: devops)_
- [ ] No ImportError from moved modules. `DEPR001` _(owner: architect)_
- [ ] No shared-mutable-default warnings. `MUT001` _(owner: dev)_
- [ ] Scheduler has a test that runs in CI (not @slow). `TEST001` _(owner: qa)_
- [ ] Scheduler tests have assertions, including same-seed determinism and shape/dtype. `TEST002` _(owner: qa)_

## Out of scope for the gate (human)
- Numerical correctness vs. the paper
- Whether this abstraction should exist

## First command
`/scaffold scheduler <Name>` then `make check`.
