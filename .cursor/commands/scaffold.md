# /scaffold — convention-correct first contribution

Usage: `/scaffold <component> <Name>`

- `$1` = component. Today the registry ships `scheduler`. Adding `model` or `pipeline` is a data change (see `templates/README.md`), not a new command.
- `$2` = PascalCase name **without** the type suffix. Example: `EulerLite` → class `EulerLiteScheduler`, file `scheduling_euler_lite.py`.

Done is only what `conventions/rules.yaml` checks. Copy the templates. Do not
start from a blank file, from library scheduler source, or from a docs search.

## 0. Ground in the registry

Read `conventions/rules.yaml`. Blocking ids for this contribution: SCHED001,
SCHED002, SCHED003, REPRO001, DEVICE001, DEPR001, MUT001, TEST001, TEST002.

The templates already satisfy them. Stay inside `.cursorignore`. Do not read or
copy `examples/candidate_scheduler/` (known-bad fixture).

## 1. Name the files

Convert `$2` to snake_case (`EulerLite` → `euler_lite`). The class is `$2Scheduler`.

- Implementation: `src/diffusers/schedulers/scheduling_<snake>.py`
- Test: `tests/schedulers/test_scheduling_<snake>.py`

This stand-in repo uses a thin `src/diffusers/schedulers/` tree so the path
matches the real library. It is not a full diffusers checkout.

## 2. Copy the template, then rename

- Start from `templates/scheduler/scheduling_TEMPLATE.py`. Copy it to the implementation path.
- Rename `TemplateScheduler` to `$2Scheduler`.
- Keep `TODO(engineer)` in `step()`. Do not replace the placeholder.

## 3. Copy the contract test (TEST001 / TEST002)

Copy `tests/_templates/scheduler_test.py` to the test path. Set `TARGET` and
`CLASS` only.

## 4. File-scoped gate

```bash
python3 tools/convention_check.py src/diffusers/schedulers/scheduling_<snake>.py
python3 -m unittest tests.schedulers.test_scheduling_<snake> -v
```

Fix every **blocking** finding. Stop at 0 blocking. Behavioral tests skip
without torch — do not edit `step()` to make them pass.

## 5. Report

- Blocking rule ids the gate checked
- 0 blocking
- `TODO(engineer)` still in `step()`
- Confirmation you added only those two files
