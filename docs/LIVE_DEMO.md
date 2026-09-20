# Live contribution demo — run this in the 45-minute screen

Goal: show **how a new engineer makes a first contribution**, not how to use
Diffusers.

**Talk order: kit first, then fork.** Open this repo (`diffuser_agent`) for the
catch-early / registry beat. Only then launch a Cloud Agent on
[`alex-16moro/diffusers`](https://github.com/alex-16moro/diffusers). The kit
clones beside the library as `ramp-kit/`.

Two ways to play the same journey after the kit beat:

| Path | When |
|------|------|
| **A. Cloud Agent on the fork** (`/scaffold scheduler EulerLite`) | Primary. Real `src/diffusers/schedulers/`, real `docs/source/en`. |
| **B. CLI twin in this kit** (`make demo-contribute KEEP=1`) | Rehearsal if the fork VM is slow. Stand-in tree only. |

Do **not** run Path B first if you want Path A to create the files live.

PRs from Path A are **fork-demo only**. Title them
`[fork demo — not for upstream]`. Do not PR huggingface/diffusers. Do not delete
inherited Hugging Face workflow files.

---

## The journey (what you narrate)

```
plan → ground → build → gate → test → review → CI clearance
```

| Step | Role | You show | You say |
|------|------|----------|---------|
| 0. Pre-flight | you | `make doctor` **on the kit** | “Python3, PyYAML, Cursor files present.” |
| 1. Plan | PM + engineer | `.github/ISSUE_TEMPLATE/contribution.md` | “Done is the same checklist CI will run.” |
| 2. Catch-early | QA / engineer | gate on kit `examples/candidate_scheduler` | “8 blocking: moved import, missing mixin, `.cuda()`, no test. That’s a review round-trip. This is the overlay, not the library.” |
| 3. Ground | engineer | `scheduling_euler_discrete.py` + `scheduling_ddpm.py`, then the gate | “Code beats the philosophy doc. MCP is opt-in; default overlay MCP is empty.” |
| 4. Build | engineer | `/scaffold scheduler EulerLite` **on the fork** | “Contract stub. Math is TODO. I will not invent a sampler.” |
| 5. Gate | engineer + CI | check the **new file only** | “0 findings. Same script as the edit hook. Never `--all` on this library.” |
| 6. Test | engineer | unittest on the new test | “Signatures pass; behavioral tests skip without torch — expected.” |
| 7. Review | QA | `projections/qa/review-checklist.md` | “Gate took the mechanical items. Humans judge the paper.” |
| 8. Clearance | DevOps | overlay gate green; HF Actions may be red | “Overlay clearance ≠ upstream CI. I don’t fake deploy, and I don’t disable their workflows.” |
| 9. Maintain | platform | `make demo-maintain` on the **kit** (if time) | “One YAML edit. I’m gone; they still own it. Not a tool per SDLC step.” |

---

## Path A — Cursor on the fork (primary, ~10–12 min)

Pre-flight (before they sit):

- **Kit (this repo):** `make doctor`. Catch-early fixture is here.
- **Cloud Agent:** launch on **`alex-16moro/diffusers`**, branch `main` (not this
  kit). Default overlay `.cursor/mcp.json` is `{ "mcpServers": {} }` — do **not**
  enable Hub HTTP or stdio MCP for the demo. Grounding is Read/Grep on the two
  scheduler files, then the file-scoped gate. Opt-in copy:
  `.cursor/mcp.optional.json` (Desktop only). Catch-early fixture on the fork:
  `ramp-kit/examples/candidate_scheduler`.
- Paste **Prompt A (fork)** from `docs/CURSOR_PROMPTS.md`.

Then type:

```
/scaffold scheduler EulerLite
```

Then have the agent (or you) run:

```bash
python3 ramp-kit/tools/convention_check.py ramp-kit/examples/candidate_scheduler
python3 ramp-kit/tools/convention_check.py src/diffusers/schedulers/scheduling_euler_lite.py
python3 -m unittest tests.schedulers.test_scheduling_euler_lite -v
python3 ramp-kit/tools/convention_check.py --json ramp-kit/examples/candidate_scheduler > /tmp/gate.json || true
python3 ramp-kit/tools/grokbot_sim.py --role qa /tmp/gate.json
python3 ramp-kit/tools/verify_scheduler_contract.py --library .
```

Point at the `TODO(engineer)` in `step`. Stop. Do not fill in Euler math.

GrokBot prints a **QA risk briefing** labelled SIMULATION. It does not gate.
Contract re-verify must say `scheduler contract OK` against this checkout's
`scheduling_ddpm.py` / `scheduling_euler_discrete.py`.

If they ask for a docs search without MCP:

```bash
python3 ramp-kit/tools/docs_mcp_server.py --query "scheduler set_timesteps step"
```

If `/scaffold` does not appear: open `.cursor/commands/scaffold.md` and say “it’s a guided command, not a binary,” then Path B.

Open the PR **on this fork**, draft, title `[fork demo — not for upstream]`.

---

## Path B — CLI twin (rehearsal / fallback)

```bash
make doctor
make demo                    # catch-early, scaffolded 0 findings, MCP, tests, GrokBot QA, contract re-verify
make demo-contribute KEEP=1  # leaves EulerLite on disk
# walk the printed steps with them
make grokbot ROLE=qa         # same sim from candidate_scheduler --json
make drift                   # rebuild projections; git diff --exit-code (must be clean)
make verify-contract         # SCHED001-003 vs fork source
make demo-contribute-clean   # remove when done
```

Default `make demo-contribute` **creates, proves, and deletes** (safe to run in CI / rehearsal). `KEEP=1` is the live “files appear” mode.

---

## Timebox vs the rest of the 45 minutes

- **0–5** problem (distributed conventions → review round-trips)
- **5–8** `rules.yaml` → many surfaces, including `owner:` tags (**not** a tool per SDLC step)
- **8–12** **kit**: catch the bad fixture; `make grokbot ROLE=qa` (simulation)
- **12–22** **fork**: source-ground → scaffold → file-scoped green gate
- **22–30** QA + issue template + overlay CI (drift + contract re-verify) vs inherited HF Actions
- **30–38** judgment (schedulers first, empty default MCP, no embeddings, no auto-fix, stop at CI)
- **38–45** where it breaks + `make demo-maintain` on the kit if not already shown

If time is tight, skip maintain and skip Path A’s agent: run Path B with `KEEP=1` and still open the two files.

---

## Cleanup

```bash
python3 tools/demo_contribute.py --clean-only --name EulerLite
```

Do not commit `scheduling_euler_lite.py` unless you explicitly want it as a fixture. The live point is **creating** it.

---

## Cloud `environment.json` dry-run (no fake deploy)

Two files, two launch targets:

| Launch on | File | What install does |
|-----------|------|-------------------|
| **This kit** | `.cursor/environment.json` | `pip install -r requirements.txt`; optional MCP launcher. Declares the fork as a repo dependency. |
| **The fork** | `overlay/environment.json` (copied to fork `.cursor/environment.json` by `make attach`) | Clones this kit to `ramp-kit/` if missing; `pip install -r ramp-kit/requirements.txt`; `python3 ramp-kit/tools/docs_mcp_server.py --selftest`. Default fork `.cursor/mcp.json` is `{ "mcpServers": {} }`. |

Dry-run locally (does not boot a Cloud VM):

```bash
python3 -c "import json; print(json.dumps(json.load(open('overlay/environment.json')), indent=2))"
python3 -c "import json; print(json.dumps(json.load(open('.cursor/environment.json')), indent=2))"
make attach TARGET=../diffusers   # copies empty mcp.json; does not touch AGENTS.md / .ai/
python3 -c "import json; print(json.load(open('../diffusers/.cursor/mcp.json')))"
# expected: {'mcpServers': {}}
```

If a Cloud Agent is already on the fork, the boot install is that JSON. You do not re-run attach live unless `.cursor/` is missing. Overlay clearance is still the file-scoped gate, not Hugging Face Actions.

