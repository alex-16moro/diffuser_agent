# /scaffold — convention-correct first contribution

Usage: `/scaffold <component> <Name>`

- `$1` = component. Today the registry ships `scheduler`. Adding `model` or `pipeline` is a data change (see `templates/README.md`), not a new command.
- `$2` = PascalCase name **without** the type suffix. Example: `EulerLite` → class `EulerLiteScheduler`, file `scheduling_euler_lite.py`.

Follow this workflow in order. Do **not** rely on training memory for how diffusers works — this repo's registry and docs are the source of truth.

## 0. Ground first

Call the `diffusers-docs` MCP tool `search_docs` for the component contract (for a scheduler: `set_timesteps`, `step`, `SchedulerMixin`, `@register_to_config`). If MCP is unavailable, read `knowledge/diffusers-docs/` and `conventions/rules.yaml`. Cite what you grounded.

Stay inside `.cursorignore`. Do not read or copy `examples/candidate_scheduler/` (it is the known-bad fixture).

## 1. Name the files

For `scheduler` + `$2` = `EulerLite`:

- Implementation: `src/diffusers/schedulers/scheduling_euler_lite.py`
- Test: `tests/schedulers/test_scheduling_euler_lite.py`

Convert `$2` to snake_case for the filename (`EulerLite` → `euler_lite`). The class is `$2Scheduler`.

This stand-in repo uses a thin `src/diffusers/schedulers/` tree so the path matches the real library. It is not a full diffusers checkout.

## 2. Copy the template, then rename

- Start from `templates/scheduler/scheduling_TEMPLATE.py`. Copy it to the implementation path.
- Rename `TemplateScheduler` to `$2Scheduler`.
- Leave the numerical update in `step` as a clearly marked `TODO(engineer)`. Scaffold the **contract**, not the algorithm. Do not invent a sampler.

## 3. Add the contract test (TEST001)

Copy `tests/_templates/scheduler_test.py` to the test path. Set:

- `TARGET` to the new implementation file
- `CLASS` to `$2Scheduler`

Do not delete the signature or behavioral test classes — presence of a file is not enough; the test must mention `set_timesteps` and `step`.

## 4. Satisfy every `component: scheduler` (and `component: any`) rule

Read `conventions/rules.yaml`. Blocking rules must pass:

- SCHED001 SchedulerMixin + ConfigMixin
- SCHED002 `set_timesteps` and `step`
- SCHED003 `@register_to_config` on `__init__`
- REPRO001 thread `generator=` through sampling
- DEVICE001 no hardcoded `.cuda()`
- DEPR001 current import paths
- MUT001 no mutable defaults
- TEST001 matching test that exercises the contract

## 5. Run the gate until clean

```bash
python3 tools/convention_check.py src/diffusers/schedulers/scheduling_<snake>.py
python3 -m unittest discover -s tests -t . -v
```

Fix every **blocking** finding. Stop at 0 blocking. Do not fabricate numerical behaviour to make behavioral tests pass — those skip without torch, which is expected.

## 6. Report

- Rule ids satisfied
- What you grounded via MCP (or the fallback docs)
- What the engineer still implements (the math)
- Confirmation you did not read paths in `.cursorignore`
