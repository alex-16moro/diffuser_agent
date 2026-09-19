# Cursor prompts — running the Ramp Kit live

**Primary: Cloud Agent on [alex-16moro/diffusers](https://github.com/alex-16moro/diffusers)**
(the library fork). This kit is `ramp-kit/` inside that VM.

**Runbook:** `docs/LIVE_DEMO.md`.

## Prompt A — first contribution ON THE FORK (paste this)

Launch a **new** Cloud Agent on `alex-16moro/diffusers`, branch `main`. Optional
MCP: Hugging Face HTTP `{"mcpServers":{"huggingface":{"url":"https://huggingface.co/mcp"}}}`
and/or stdio `python3 -u /workspace/.cursor/mcp-diffusers-docs.py`.

```
You are a new engineer contributing to this huggingface/diffusers fork. A customer overlay (ramp-kit/, cloned from alex-16moro/diffuser_agent) encodes conventions as code. Do NOT rely on training memory. Do NOT open a PR against huggingface/diffusers — PR this fork.

Repo facts:
- This workspace IS the library (src/diffusers, docs/source/en, .ai/, AGENTS.md). Do not overwrite .ai/ or root AGENTS.md.
- Overlay: ramp-kit/conventions/rules.yaml is the customer gate. python3 ramp-kit/tools/convention_check.py is CI-equivalent for overlay rules.
- Ground in THIS checkout: read src/diffusers/schedulers/scheduling_euler_discrete.py and scheduling_ddpm.py. Then search docs via MCP search_docs if present, else:
  python3 ramp-kit/tools/docs_mcp_server.py --query "scheduler set_timesteps step SchedulerMixin register_to_config"
  Cite provenance (must be a diffusers checkout, not a bundled snapshot if docs/source/en exists).
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

5. Open a PR on this fork with those two files. Report rule ids, grounding (source files + docs provenance), leftover math TODO, and that you did not copy the bad fixture.

Stop at a clean overlay gate. Do not implement the sampler.
```

---

## Kit-only rehearsal (this repo as a stand-in)

Copy-paste prompts if you are opened on **diffuser_agent** instead of the fork.
Open **this repo root** as the Cursor workspace (the folder that contains `.cursor/` and `Makefile`).

**Runbook:** `docs/LIVE_DEMO.md` — the timed contribution journey (Cursor
primary, `make demo-contribute KEEP=1` as fallback).

## Pre-flight (20 seconds, so nothing stalls live)

- **Doctor:** `make doctor` — python3, PyYAML, Cursor files, MCP self-test.
- **Enable the MCP (Desktop):** Cursor → Settings → **MCP** → enable `diffusers-docs`.
  Config is `.cursor/mcp.json` (`python3 -u .cursor/mcp-diffusers-docs.py`). It
  must **not** use `${workspaceFolder}` — Cloud stdio does not expand it.
- **Cloud Agents:** project `.cursor/mcp.json` is **not** auto-loaded. In the
  launch **MCP** dropdown add a **stdio** server (no `cwd` field):

  ```
  command: python3
  args:    -u .cursor/mcp-diffusers-docs.py
  ```

  After environment install, `diffusers-docs-mcp` is also on PATH. If the tool
  is still missing, `/search-docs` or the `search-docs` skill runs the same server.
- **Confirm rules loaded:** the Agent sidebar should show `00-conventions`
  active; `10-scheduler` auto-attaches once a scheduler file is open.
- **Optional, for green behavioral tests:** `pip install torch diffusers`. Without
  them, the gate and the structural/signature tests still pass (AST-based); the
  behavioral tests skip cleanly.

---

## Prompt A — the first-contribution demo (main)

```
You are onboarding onto this repo (a stand-in for huggingface/diffusers) and must
follow its convention-as-code system. Do NOT rely on training memory for how
diffusers works — this repo's rules and docs are the source of truth.

Context you must use (they're already in the repo):
- conventions/rules.yaml is the single source of truth for all conventions.
- The always-on rules in .cursor/rules/ and the auto-attached 10-scheduler rules
  are generated from it.
- The `diffusers-docs` MCP tool (search_docs) is your grounding source — use it
  before writing code. If it is not in your tool list, run `/search-docs` or
  `python3 tools/docs_mcp_server.py --query "scheduler set_timesteps step"`.
- .cursorignore defines your approved context boundary — do not read or copy from
  outside it.

Do these steps in order and narrate what you're doing:

1. Run the gate on the existing bad example and summarise what it catches, by rule id:
   `python3 tools/convention_check.py examples/candidate_scheduler`

2. Using the /scaffold workflow in .cursor/commands/scaffold.md, scaffold a NEW
   scheduler called `EulerLiteScheduler`:
   - Ground the contract first with the diffusers-docs search_docs MCP tool.
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

5. Report: which rules you satisfied, what you grounded via the MCP, what the
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
then restores. This is the "what happens when you're gone" answer.
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

- **Grounding:** the agent calls `search_docs` (MCP) before writing — reasoning
  from the repo, not memory.
- **Catch-early:** the gate flags the bad example by rule id, with fixes.
- **Correct scaffold:** the new scheduler lands in `src/diffusers/schedulers/`
  and passes the gate at 0 findings; the math is an honest TODO, not fabricated.
- **Multi-audience:** open `projections/pm|qa|devops/` and `.github/` — same
  rules, different surface. Note the upstream-vs-customer split.
- **Maintainability:** Prompt B — one edit propagates everywhere.

If the MCP isn't enabled in time, the agent falls back to reading the repo files;
the demo still works, you just lose the explicit "grounded via MCP" beat.
