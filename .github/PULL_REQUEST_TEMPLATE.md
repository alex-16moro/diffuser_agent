<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->

## Summary

## Convention gate
Run `make check` and `make test` before requesting review.
Blocking items (auto-verified; still confirm you ran the commands):

- [ ] `SCHED001` Schedulers inherit SchedulerMixin and ConfigMixin — New scheduler is loadable via from_config and saveable via save_config. _(owner: architect)_
- [ ] `SCHED002` Schedulers implement the step() / set_timesteps() contract — Scheduler runs inside a minimal DDPM-style loop without adapter code. _(owner: architect)_
- [ ] `SCHED003` Scheduler __init__ is decorated with @register_to_config — save_config()/from_config() round-trips all constructor arguments. _(owner: architect)_
- [ ] `REPRO001` Randomness threads through a generator, never global RNG — Same seed -> identical output, verified by a determinism test. _(owner: dev)_
- [ ] `DEVICE001` No hardcoded CUDA/device placement — Example runs on CPU CI with no code change. _(owner: devops)_
- [ ] `DEPR001` No deprecated/moved import paths — No ImportError from moved modules. _(owner: architect)_
- [ ] `MUT001` No mutable default arguments — No shared-mutable-default warnings. _(owner: dev)_
- [ ] `TEST001` New schedulers/models ship with a matching test file — Scheduler has a test that runs in CI (not @slow). _(owner: qa)_
- [ ] `TEST002` Scheduler tests assert behaviour, not just presence — Scheduler tests have assertions, including same-seed determinism and shape/dtype. _(owner: qa)_

## Tests run
```
make check
make test
```

## Human judgment (not the gate)
- [ ] Numerical method is correct vs. the paper / spec (QA)
- [ ] This does not duplicate an existing scheduler/model/pipeline
