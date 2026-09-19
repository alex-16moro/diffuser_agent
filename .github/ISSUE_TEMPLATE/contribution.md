<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->

# Contribution intake

_PM / tech-lead planning surface. Generated from the same rules the
agent, reviewer, and CI use, so "what we're building" matches "done".

## What is changing?
- [ ] Scheduler (`/scaffold scheduler <Name>`)
- [ ] Other (describe)

## Definition of Done (blocking — `make check`)
- [ ] New scheduler is loadable via from_config and saveable via save_config. `SCHED001`
- [ ] Scheduler runs inside a minimal DDPM-style loop without adapter code. `SCHED002`
- [ ] save_config()/from_config() round-trips all constructor arguments. `SCHED003`
- [ ] Same seed -> identical output, verified by a determinism test. `REPRO001`
- [ ] Example runs on CPU CI with no code change. `DEVICE001`
- [ ] No ImportError from moved modules. `DEPR001`
- [ ] No shared-mutable-default warnings. `MUT001`
- [ ] Scheduler has a test that runs in CI (not @slow). `TEST001`

## Out of scope for the gate (human)
- Numerical correctness vs. the paper
- Whether this abstraction should exist

## First command
`/scaffold scheduler <Name>` then `make check`.
