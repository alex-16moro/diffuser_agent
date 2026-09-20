# /scaffold — convention-correct first contribution

Usage: `/scaffold <component> <Name>`

- `$1` = component. Today the registry ships `scheduler`. Adding `model` or `pipeline` is a data change (see `templates/README.md`), not a new command.
- `$2` = PascalCase name **without** the type suffix. Example: `EulerLite` → class `EulerLiteScheduler`, file `scheduling_euler_lite.py`. If those files already exist, pick a new unused `$2`.

Done is what `conventions/rules.yaml` checks **and**, on a real library checkout, what the library's own CI checks. Copy the templates. Do not start from a blank file, from library scheduler source, or from a docs search.

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
matches the real library. On the fork, that path is the real library.

## 2. Copy the template, then rename every placeholder

- Start from `templates/scheduler/scheduling_TEMPLATE.py`. Copy it to the implementation path.
- Rename `TemplateScheduler` to `$2Scheduler`.
- Keep `TODO(engineer)` in `step()`. Do not replace that placeholder.
- After the copy, the new files must not contain `TEMPLATE —`, `CHANGE_ME`,
  `ChangeMeScheduler`, or `TemplateScheduler`. Add a `# Copied from` marker only
  when a block is actually copied (malformed markers fail `check_copies`).

## 3. Copy the contract test (TEST001 / TEST002)

Copy `tests/_templates/scheduler_test.py` to the test path. Set `TARGET` and
`CLASS`. Replace every other template token. The test docstring names
`$2Scheduler`, not ChangeMe.

## 4. File-scoped convention gate (never `--all` on the library)

```bash
python3 tools/convention_check.py src/diffusers/schedulers/scheduling_<snake>.py
python3 -m unittest tests.schedulers.test_scheduling_<snake> -v
```

On the fork the checker lives at `ramp-kit/tools/convention_check.py`. Fix every
**blocking** finding. Stop at 0 blocking. Do not edit `step()` math to make
behavioral tests pass.

## 5. On a real library checkout: register, then invoke library CI

If this workspace has the library `Makefile` (`style` / `quality` targets):

1. Register `$2Scheduler` alphabetically in
   `src/diffusers/schedulers/__init__.py` (`_import_structure` + TYPE_CHECKING
   import), `src/diffusers/__init__.py` (schedulers lazy list + TYPE_CHECKING
   import), then run `python utils/check_dummies.py --fix_and_overwrite`.
2. **Invoke** the library's own tooling until each exits 0. Do not reimplement
   them:

```bash
make style
make quality
python utils/check_copies.py && python utils/check_dummies.py && python utils/check_repo.py
python3 -m unittest tests.schedulers.test_scheduling_<snake> -v
```

Only open a PR when those commands pass. Do not disable inherited workflows.
Do not overwrite `AGENTS.md` or `.ai/`.

## 6. Report

- Blocking rule ids the gate checked
- 0 blocking
- `TODO(engineer)` still in `step()`
- No leftover `TEMPLATE —` / `CHANGE_ME` / `ChangeMeScheduler` / `TemplateScheduler`
- On the fork: `make style` / `make quality` / check_copies / check_dummies /
  check_repo exit codes
