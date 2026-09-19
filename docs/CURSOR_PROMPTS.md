# Cursor prompts — running the Ramp Kit live

**Talk order: kit first, then fork.** Show `diffuser_agent` (registry + catch-early)
before launching a Cloud Agent. **Primary live write:** Cloud Agent on
[alex-16moro/diffusers](https://github.com/alex-16moro/diffusers). This kit is
`ramp-kit/` inside that VM.

**Runbook:** `docs/LIVE_DEMO.md`.

Default overlay MCP is **empty**. Do not paste Hub HTTP or stdio MCP into the
Cloud launch for this demo. Grounding is the two scheduler source files, then
the file-scoped gate. Opt-in servers live in `overlay/mcp.optional.json`.

---

## Prompt A — first contribution ON THE FORK (paste this)

Launch a **new** Cloud Agent on `alex-16moro/diffusers`, branch `main`. Leave
MCP **off**.

```
You are a new engineer contributing to this huggingface/diffusers fork. A customer overlay (ramp-kit/, cloned from alex-16moro/diffuser_agent) encodes conventions as code. Do NOT rely on training memory. Do NOT open a PR against huggingface/diffusers — PR this fork, draft, title "[fork demo — not for upstream]".

Repo facts:
- This workspace IS the library (src/diffusers, docs/source/en, .ai/, AGENTS.md). Do not overwrite .ai/ or root AGENTS.md. Do not delete .github/workflows from Hugging Face.
- Overlay: ramp-kit/conventions/rules.yaml is the customer gate. python3 ramp-kit/tools/convention_check.py is CI-equivalent for overlay rules.
- Ground in THIS checkout, in this order:
  1. Read src/diffusers/schedulers/scheduling_euler_discrete.py and scheduling_ddpm.py (code beats the philosophy doc).
  2. Treat ramp-kit/conventions/rules.yaml / the gate as authoritative if anything disagrees.
  3. Optional, only if asked: python3 ramp-kit/tools/docs_mcp_server.py --query "scheduler set_timesteps step SchedulerMixin register_to_config"
  Do not wait for an MCP tool. Cite source file paths.
- Do not read or copy ramp-kit/examples/candidate_scheduler/ into the new files.

Do these steps in order and narrate them:

1. Catch-early:
   python3 ramp-kit/tools/convention_check.py ramp-kit/examples/candidate_scheduler

2. Scaffold EulerLiteScheduler:
   - Copy ramp-kit/templates/scheduler/scheduling_TEMPLATE.py → src/diffusers/schedulers/scheduling_euler_lite.py
   - Copy ramp-kit/tests/_templates/scheduler_test.py → tests/schedulers/test_scheduling_euler_lite.py (mention set_timesteps and step)
   - Leave TODO(engineer) in step. Do not invent Euler math.

3. Gate the NEW file only (never --all on this library):
   python3 ramp-kit/tools/convention_check.py src/diffusers/schedulers/scheduling_euler_lite.py

4. python3 -m unittest tests.schedulers.test_scheduling_euler_lite -v
   Behavioral skips without torch are expected.

5. Open a draft PR on this fork with those two files, titled "[fork demo — not for upstream]". Report rule ids, grounding (the two source files + gate), leftover math TODO, and that you did not copy the bad fixture.

Stop at a clean overlay gate. Do not implement the sampler.
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
- **Optional, for green behavioral tests:** `pip install torch diffusers`. Without
  them, the gate and the structural/signature tests still pass (AST-based); the
  behavioral tests skip cleanly.

---

## Prompt A (kit stand-in) — rehearsal only

```
You are onboarding onto this repo (a stand-in for huggingface/diffusers) and must
follow its convention-as-code system. Do NOT rely on training memory for how
diffusers works — this repo's rules are the source of truth.

Context you must use (they're already in the repo):
- conventions/rules.yaml is the single source of truth for all conventions.
- The always-on rules in .cursor/rules/ and the auto-attached 10-scheduler rules
  are generated from it.
- Ground the scheduler contract by reading examples/scaffolded_scheduler and the
  rules tagged component: scheduler. Optional docs CLI (MCP is not required):
  `python3 tools/docs_mcp_server.py --query "scheduler set_timesteps step"`.
- .cursorignore defines your approved context boundary — do not read or copy from
  outside it.

Do these steps in order and narrate what you're doing:

1. Run the gate on the existing bad example and summarise what it catches, by rule id:
   `python3 tools/convention_check.py examples/candidate_scheduler`

2. Using the /scaffold workflow in .cursor/commands/scaffold.md, scaffold a NEW
   scheduler called `EulerLiteScheduler`:
   - Ground the contract from the registry and the scaffolded reference, not from memory.
   - Create src/diffusers/schedulers/scheduling_euler_lite.py, satisfying every
     rule tagged `component: scheduler` in the registry.
   - Leave the numerical update rule as a clearly marked TODO — do NOT fabricate
     the math. Scaffold the contract, not the algorithm.
   - Create tests/schedulers/test_scheduling_euler_lite.py from
     tests/_templates/scheduler_test.py (satisfies TEST001; the test must mention
     set_timesteps and step).

3. Run the gate on your new file and fix every BLOCKING finding until it's clean:
   `python3 tools/convention_check.py src/diffusers/schedulers/scheduling_euler_lite.py`

4. Run the tests: `python3 -m unittest discover -s tests -t .`

5. Report: which rules you satisfied, which files you grounded in, what the
   engineer still needs to implement (the math), and confirm you stayed within
   the .cursorignore boundary.

Constraints: stay in bounds, cite rule ids in your summary, and stop with a clean
gate — don't invent numerical behaviour to make tests pass.
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
- **Grounding:** the agent reads `scheduling_euler_discrete.py` and
  `scheduling_ddpm.py`, then the gate — reasoning from the repo, not memory.
  MCP is opt-in, not the demo.
- **Catch-early:** the gate flags the bad example by rule id, with fixes.
- **Correct scaffold:** the new scheduler lands in `src/diffusers/schedulers/`
  and passes the gate at 0 findings; the math is an honest TODO, not fabricated.
- **File-scoped gate:** never `convention_check.py --all` on the fork.
- **Multi-audience:** open `projections/pm|qa|devops/` and `.github/` — same
  rules, different surface. Note the upstream-vs-customer split. One registry,
  many projections — not a capability per SDLC step.
- **Fork PR hygiene:** draft, `[fork demo — not for upstream]`. Overlay green
  does not mean Hugging Face CI is green; do not delete their workflows.
- **Maintainability:** Prompt B — one edit propagates everywhere.
