# Cursor prompts — running the Ramp Kit live

**Talk order: kit first, then fork.** Show `diffuser_agent` (registry + catch-early)
before launching a Cloud Agent. **Primary live write:** Cloud Agent on
[alex-16moro/diffusers](https://github.com/alex-16moro/diffusers). This kit is
`ramp-kit/` inside that VM.

**Runbook:** `docs/LIVE_DEMO.md`.

Default overlay MCP is **stdio `diffusers-docs`**, not Hub HTTP. Cloud dropdown:
`diffusers-docs-mcp` or `python3 -u .cursor/mcp-diffusers-docs.py`. The first
PR still copies templates and runs the file-scoped gate; `search_docs` is
available, not a deliverable. Extra servers live in `overlay/mcp.optional.json`.

---

## Prompt A — first contribution ON THE FORK (paste this)

Launch a **new** Cloud Agent on `alex-16moro/diffusers`, branch **`main`**. Enable
stdio MCP (`diffusers-docs-mcp` or `python3 -u .cursor/mcp-diffusers-docs.py`).
Do **not** enable Hub HTTP MCP. The draft PR **base must be `main`** so overlay
CI (`ramp-kit-overlay` / `overlay-gate`) actually runs. Do not stack onto a
`cursor/…` topic branch.

`EulerLiteScheduler` and `HeunLiteScheduler` files are already on fork `main`.
This prompt scaffolds a **new unused** name (example: **PNDMLite**) and runs the
library's own CI tools until they pass. Do not overwrite existing lite files.

```
You just joined. First contribution on this huggingface/diffusers FORK (alex-16moro/diffusers). Overlay: ramp-kit/ (from alex-16moro/diffuser_agent).

Copy the overlay templates. Do not design a scheduler. Keep TODO(engineer) in step(). Do not disable inherited workflows. Do not overwrite .ai/ or root AGENTS.md.

If ramp-kit/ is missing:
  git clone --depth 1 https://github.com/alex-16moro/diffuser_agent.git ramp-kit

Pick an unused PascalCase name. If scheduling_euler_lite.py / scheduling_heun_lite.py / scheduling_pndm_lite.py already exist, pick a different unused $2. Example when those three are free: PNDMLite → PNDMLiteScheduler.

Follow ramp-kit overlay /scaffold (.cursor/commands/scaffold.md):

1. Read ramp-kit/conventions/rules.yaml. Blocking ids: SCHED001, SCHED002, SCHED003, REPRO001, DEVICE001, DEPR001, MUT001, TEST001, TEST002.

2. Copy ramp-kit/templates/scheduler/scheduling_TEMPLATE.py → src/diffusers/schedulers/scheduling_<snake>.py
   Rename TemplateScheduler → $2Scheduler. Keep TODO(engineer) in step().
   After the copy, no TEMPLATE —, CHANGE_ME, ChangeMeScheduler, or TemplateScheduler may remain.

3. Copy ramp-kit/tests/_templates/scheduler_test.py → tests/schedulers/test_scheduling_<snake>.py
   Set TARGET and CLASS. Replace every other template token.

4. Register $2Scheduler alphabetically in src/diffusers/schedulers/__init__.py, src/diffusers/__init__.py, then: python utils/check_dummies.py --fix_and_overwrite

5. python3 ramp-kit/tools/convention_check.py src/diffusers/schedulers/scheduling_<snake>.py
   Fix blocking findings only. Stop at 0 blocking. Never convention_check.py --all.

6. Invoke the library's own tooling until each exits 0 (do not reimplement them):
   make style
   make quality
   python utils/check_copies.py && python utils/check_dummies.py && python utils/check_repo.py
   python3 -m unittest tests.schedulers.test_scheduling_<snake> -v
   Do not edit step() math. Behavioral tests with torch must pass.

7. Draft PR on this fork, base main, only after those commands pass.
   Title: [fork demo — not for upstream] Add $2Scheduler scaffold
   Never PR huggingface/diffusers. Do not copy ramp-kit/examples/candidate_scheduler/.

Then stop. Report paths, blocking rule ids, 0 blocking, leftover TODO(engineer), library-gate exit codes, draft PR URL. Do not merge.
```

---

## Kit-only rehearsal (this repo as a stand-in)

Copy-paste prompts if you are opened on **diffuser_agent** instead of the fork.
Open **this repo root** as the Cursor workspace (the folder that contains `.cursor/` and `Makefile`).

**Runbook:** `docs/LIVE_DEMO.md` — kit catch-early first; Cursor on the fork
primary; `make demo-contribute KEEP=1` as fallback.

## Pre-flight (20 seconds, so nothing stalls live)

- **Doctor:** `make doctor` — python3, PyYAML, Cursor files, MCP self-test,
  overlay stdio `diffusers-docs` (no Hub HTTP).
- **Kit Desktop MCP:** Cursor → Settings → **MCP** → enable `diffusers-docs`.
  Config is `.cursor/mcp.json` (`python3 -u .cursor/mcp-diffusers-docs.py`).
  It must **not** use `${workspaceFolder}`. Cloud dropdown: `diffusers-docs-mcp`.
- **Fork / Cloud Agents:** overlay `.cursor/mcp.json` is stdio `diffusers-docs`
  only. Project MCP is **not** auto-loaded on Cloud — paste
  `diffusers-docs-mcp` (or `python3 -u .cursor/mcp-diffusers-docs.py`) in the
  MCP dropdown. Do **not** add Hugging Face HTTP MCP (Hub search + OAuth).
- **Confirm rules loaded:** the Agent sidebar should show `00-conventions`
  active; `10-scheduler` auto-attaches once a scheduler file is open.
- **Torch is optional.** The gate and the structural/signature tests still pass
  without it (AST-based). Behavioral tests skip; that is success, not a prompt
  to implement `step()`.

---

## Prompt A (kit stand-in) — rehearsal only

```
You are onboarding onto this repo (a stand-in for huggingface/diffusers).
Done is only what conventions/rules.yaml checks. Copy the templates. Do not
design a scheduler.

Create exactly these two files:
- src/diffusers/schedulers/scheduling_euler_lite.py
- tests/schedulers/test_scheduling_euler_lite.py

1. Read conventions/rules.yaml. Blocking ids: SCHED001, SCHED002, SCHED003,
   REPRO001, DEVICE001, DEPR001, MUT001, TEST001, TEST002.

2. Follow .cursor/commands/scaffold.md for EulerLite: copy
   templates/scheduler/scheduling_TEMPLATE.py and
   tests/_templates/scheduler_test.py. Rename TemplateScheduler →
   EulerLiteScheduler. Keep TODO(engineer) in step(). Set TARGET and CLASS only.

3. python3 tools/convention_check.py src/diffusers/schedulers/scheduling_euler_lite.py
   Fix blocking findings only. Stop at 0 blocking.

4. python3 -m unittest tests.schedulers.test_scheduling_euler_lite -v
   Skips without torch are success — do not edit step() to make behavioral tests pass.

5. Report the two paths, blocking rule ids, 0 blocking, leftover TODO(engineer).
   Stay inside .cursorignore. Do not copy examples/candidate_scheduler/.
```

## Prompt B — prove maintainability (requirement #4, ~30s)

```
Now demonstrate maintainability: run `make demo-maintain`. Explain what it shows —
that one edit to conventions/rules.yaml regenerates the agent rules, AGENTS.md,
the PM Definition of Done, the QA checklist, the issue/PR templates, and CI,
then restores. This is the "what happens when you're gone" answer. It is one
registry projected many ways — not a new tool per SDLC step.
```

## Prompt C — prove it scales to a new component (optional, advanced)

Use this only if asked how it extends beyond schedulers. It shows a new component
is a DATA change, not new machinery (see `templates/README.md`).

```
Show how this scales to a new component without new machinery. Following
templates/README.md, add a `model` component: declare it under meta.components in
conventions/rules.yaml, add 1-2 rules tagged `component: model` (reuse existing
check types), and drop a minimal templates/model/modeling_TEMPLATE.py. Then run
`python3 tools/build_projections.py` and show that a new .cursor/rules/10-model.mdc
was generated and AGENTS.md now lists the model rules — with zero code changes to
the tooling. Keep it minimal; do not implement a real model.
```

---

## What the interviewer should see

- **Kit first, then fork:** catch-early on this repo; the write lands on the
  real library tree.
- **Grounding:** the agent reads `ramp-kit/conventions/rules.yaml` and copies
  the overlay templates. Euler/DDPM source is how *we* verified the YAML, not
  the first-PR recipe. MCP is opt-in, not the demo.
- **Catch-early:** you run this on the **kit**, not inside Prompt A.
- **Correct scaffold:** scheduler + matching test with no leftover placeholders;
  registered in inits/dummies; file-scoped gate 0 blocking; `TODO(engineer)`
  still in `step()`; library `make style` / `make quality` / check_* green.
- **File-scoped gate:** never `convention_check.py --all` on the fork.
- **Multi-audience:** open `projections/pm|qa|devops/` and `.github/` — same
  rules, different surface. Note the upstream-vs-customer split. One registry,
  many projections — not a capability per SDLC step.
- **Fork PR hygiene:** draft, **base `main`**, `[fork demo — not for upstream]`.
  Overlay-gate is the customer check-run. Overlay green does not mean Hugging
  Face CI is green; do not delete their workflows. Math stays TODO.
- **Maintainability:** Prompt B — one edit propagates everywhere.
