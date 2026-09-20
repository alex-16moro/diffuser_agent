# Cursor prompts — running the Ramp Kit live

**Talk order: kit first, then fork.** Show `diffuser_agent` (registry + catch-early)
before launching a Cloud Agent. **Primary live write:** Cloud Agent on
[alex-16moro/diffusers](https://github.com/alex-16moro/diffusers). This kit is
`ramp-kit/` inside that VM.

**Runbook:** `docs/LIVE_DEMO.md`.

Default overlay MCP is **empty**. Do not paste Hub HTTP or stdio MCP into the
Cloud launch for this demo. The engineer copies overlay templates and runs the
file-scoped gate — not library source, not docs search. Opt-in servers live in
`overlay/mcp.optional.json`.

---

## Prompt A — first contribution ON THE FORK (paste this)

Launch a **new** Cloud Agent on `alex-16moro/diffusers`, branch **`main`**. Leave
MCP **off**. The draft PR **base must be `main`** so overlay CI
(`ramp-kit-overlay` / `overlay-gate`) actually runs. Do not stack onto a
`cursor/…` topic branch.

`EulerLiteScheduler` is already on fork `main`. This prompt scaffolds **HeunLite**.

```
You just joined. First contribution on this huggingface/diffusers FORK (alex-16moro/diffusers). Overlay: ramp-kit/ (from alex-16moro/diffuser_agent).

Done is only what ramp-kit/conventions/rules.yaml checks. The templates already pass those checks. Copy them. Do not design a scheduler.

If ramp-kit/ is missing:
  git clone --depth 1 https://github.com/alex-16moro/diffuser_agent.git ramp-kit

Scope — create exactly these two files, then stop:
- src/diffusers/schedulers/scheduling_heun_lite.py
- tests/schedulers/test_scheduling_heun_lite.py

Do this:

1. Read ramp-kit/conventions/rules.yaml. Blocking ids for this change: SCHED001, SCHED002, SCHED003, REPRO001, DEVICE001, DEPR001, MUT001, TEST001, TEST002.

2. Copy ramp-kit/templates/scheduler/scheduling_TEMPLATE.py → src/diffusers/schedulers/scheduling_heun_lite.py
   Rename TemplateScheduler → HeunLiteScheduler. Keep TODO(engineer) in step().

3. Copy ramp-kit/tests/_templates/scheduler_test.py → tests/schedulers/test_scheduling_heun_lite.py
   Set TARGET and CLASS only.

4. python3 ramp-kit/tools/convention_check.py src/diffusers/schedulers/scheduling_heun_lite.py
   Fix blocking findings only. Stop at 0 blocking. Never convention_check.py --all.

5. python3 -m unittest tests.schedulers.test_scheduling_heun_lite -v
   Structural/signature must pass. Skips without torch are success — do not edit step() to make behavioral tests pass.

6. Draft PR on this fork, base main, those two files only.
   Title: [fork demo — not for upstream] Scaffold HeunLiteScheduler contract
   Never PR huggingface/diffusers. Do not overwrite .ai/ or root AGENTS.md. Do not delete inherited workflows.
   Do not copy ramp-kit/examples/candidate_scheduler/. Do not touch scheduling_euler_lite.py.

Then stop. Report the two paths, blocking rule ids, 0 blocking, leftover TODO(engineer), draft PR URL. Do not merge.
```

---

## Kit-only rehearsal (this repo as a stand-in)

Copy-paste prompts if you are opened on **diffuser_agent** instead of the fork.
Open **this repo root** as the Cursor workspace (the folder that contains `.cursor/` and `Makefile`).

**Runbook:** `docs/LIVE_DEMO.md` — kit catch-early first; Cursor on the fork
primary; `make demo-contribute KEEP=1` as fallback.

## Pre-flight (20 seconds, so nothing stalls live)

- **Doctor:** `make doctor` — python3, PyYAML, Cursor files, MCP self-test,
  overlay `mcp.json` empty.
- **Kit Desktop MCP (optional, this repo only):** Cursor → Settings → **MCP** →
  enable `diffusers-docs`. Config is `.cursor/mcp.json`
  (`python3 -u .cursor/mcp-diffusers-docs.py`). It must **not** use
  `${workspaceFolder}`.
- **Fork / Cloud Agents:** overlay `.cursor/mcp.json` is `{ "mcpServers": {} }`.
  Project MCP is **not** auto-loaded anyway. Do not add Hugging Face HTTP MCP
  (Hub search + OAuth, wrong corpus) or stdio with `cwd` /
  `${workspaceFolder}`. If you later opt in on Desktop, copy from
  `.cursor/mcp.optional.json`.
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
- **Correct scaffold:** two files in `src/diffusers/schedulers/` + matching
  test; file-scoped gate 0 blocking; `TODO(engineer)` still in `step()`.
- **File-scoped gate:** never `convention_check.py --all` on the fork.
- **Multi-audience:** open `projections/pm|qa|devops/` and `.github/` — same
  rules, different surface. Note the upstream-vs-customer split. One registry,
  many projections — not a capability per SDLC step.
- **Fork PR hygiene:** draft, **base `main`**, `[fork demo — not for upstream]`.
  Overlay-gate is the customer check-run. Overlay green does not mean Hugging
  Face CI is green; do not delete their workflows. Two files only; math stays TODO.
- **Maintainability:** Prompt B — one edit propagates everywhere.
