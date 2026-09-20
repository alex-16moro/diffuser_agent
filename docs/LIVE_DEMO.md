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
| **A. Cloud Agent on the fork** (`/scaffold scheduler HeunLite`) | Primary. Real `src/diffusers/schedulers/`. Two files the registry checks. |
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
| 3. Ground | engineer | `ramp-kit/conventions/rules.yaml` + overlay templates | “Done is the gate. Templates already pass. I am not copying Euler/DDPM or writing docs.” |
| 4. Build | engineer | `/scaffold scheduler HeunLite` **on the fork** | “Two files. `TODO(engineer)` stays in `step()`.” |
| 5. Gate | engineer + CI | check the **new file only** | “0 blocking. Same script as the edit hook. Never `--all` on this library.” |
| 6. Test | engineer | unittest on the new test | “Signatures pass; behavioral tests skip without torch — expected.” |
| 7. Review | QA | `projections/qa/review-checklist.md` | “Gate took the mechanical items. Humans judge the paper.” |
| 8. Clearance | DevOps | overlay gate green; HF Actions may be red | “Overlay clearance ≠ upstream CI. I don’t fake deploy, and I don’t disable their workflows.” |
| 9. Maintain | platform | `make demo-maintain` on the **kit** (if time) | “One YAML edit. I’m gone; they still own it. Not a tool per SDLC step.” |

---

## Path A — Cursor on the fork (primary, ~10–12 min)

Pre-flight (before they sit):

- **Kit (this repo):** `make doctor`. Catch-early fixture is here.
- **Cloud Agent:** launch on **`alex-16moro/diffusers`**, branch `main` (not this
  kit). Overlay `.cursor/mcp.json` is stdio `diffusers-docs` only. Enable that
  in the Cloud MCP dropdown (`diffusers-docs-mcp` or
  `python3 -u .cursor/mcp-diffusers-docs.py`). Do **not** enable Hub HTTP.
  The paste is Prompt A: copy templates, file-scoped gate. Catch-early stays
  on this kit, not in the paste.
- Paste **Prompt A (fork)** from `docs/CURSOR_PROMPTS.md`.

Then type:

```
/scaffold scheduler HeunLite
```

The agent should only run:

```bash
python3 ramp-kit/tools/convention_check.py src/diffusers/schedulers/scheduling_heun_lite.py
python3 -m unittest tests.schedulers.test_scheduling_heun_lite -v
```

Point at the `TODO(engineer)` in `step`. Stop.

You (not the engineer paste) may still show catch-early, GrokBot, and
contract re-verify from the kit:

```bash
python3 ramp-kit/tools/convention_check.py ramp-kit/examples/candidate_scheduler
python3 ramp-kit/tools/convention_check.py --json ramp-kit/examples/candidate_scheduler > /tmp/gate.json || true
python3 ramp-kit/tools/grokbot_sim.py --role qa /tmp/gate.json
python3 ramp-kit/tools/verify_scheduler_contract.py --library .
```

GrokBot prints a **QA risk briefing** labelled SIMULATION. It does not gate.
Contract re-verify must say `scheduler contract OK` against this checkout's
`scheduling_ddpm.py` / `scheduling_euler_discrete.py` — that proves the YAML,
not the first PR.

Optional 2-minute add-on if Grok Bot is on a phone in the room: open
`docs/GROKBOT.md`, paste the **Ramp Kit QA** block from `make grokbot-pack`
into **Edit Profile**, send the first message. The Bot is a reader of the
same gate JSON you just produced.

If they ask for a docs search without MCP:

```bash
python3 ramp-kit/tools/docs_mcp_server.py --query "scheduler set_timesteps step"
```

If `/scaffold` does not appear: open `.cursor/commands/scaffold.md` and say “it’s a guided command, not a binary,” then Path B.

Open the PR **on this fork**, draft, **base `main`**, title
`[fork demo — not for upstream]`. Overlay CI (`overlay-gate`) only runs when
the base already has `ramp-kit-overlay.yml` — that is `main`, not a stacked
topic branch.

---

## Path B — CLI twin (rehearsal / fallback)

```bash
make doctor
make demo                    # catch-early, scaffolded 0 findings, MCP, tests, GrokBot QA, contract re-verify
make demo-contribute KEEP=1  # leaves EulerLite on disk
# walk the printed steps with them
make grokbot ROLE=qa         # same sim from candidate_scheduler --json
make grokbot-pack            # paste-ready iPhone / desktop Grok Bot profiles
make drift                   # rebuild projections; git diff --exit-code (must be clean)
make verify-contract         # SCHED001-003 vs fork source
make demo-contribute-clean   # remove when done
```

Default `make demo-contribute` **creates, proves, and deletes** (safe to run in CI / rehearsal). `KEEP=1` is the live “files appear” mode.

---

## Timebox vs the rest of the 45 minutes

- **0–5** problem (distributed conventions → review round-trips)
- **5–8** `rules.yaml` → many surfaces, including `owner:` tags (**not** a tool per SDLC step)
- **8–12** **kit**: catch the bad fixture; `make grokbot ROLE=qa` (simulation).
  If a phone is in the room, paste QA from `make grokbot-pack` (see `docs/GROKBOT.md`).
- **12–22** **fork**: templates + `rules.yaml` → scaffold → file-scoped 0 blocking
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

| Launch on | File | What install / start do |
|-----------|------|-------------------|
| **This kit** | `.cursor/environment.json` | `install`: `.cursor/cloud-install.sh` (pyyaml, CPU torch, diffusers, `diffusers-docs-mcp` PATH shim, MCP `--selftest`). `start`: re-run the shim only (snapshot boots skip `install`). Allowlist command: `diffusers-docs-mcp`. Declares the fork as a repo dependency. |
| **The fork** | `overlay/environment.json` (copied to fork `.cursor/environment.json` by `make attach`) | Clones this kit to `ramp-kit/` if missing, then the same `cloud-install.sh`. `start` refreshes `diffusers-docs-mcp`. Fork `.cursor/mcp.json` is stdio `diffusers-docs` only (no Hub HTTP). |

Dry-run locally (does not boot a Cloud VM):

```bash
python3 -c "import json; print(json.dumps(json.load(open('overlay/environment.json')), indent=2))"
python3 -c "import json; print(json.dumps(json.load(open('.cursor/environment.json')), indent=2))"
make attach TARGET=../diffusers   # copies stdio mcp.json; does not touch AGENTS.md / .ai/
python3 -c "import json; print(json.load(open('../diffusers/.cursor/mcp.json')))"
# expected: mcpServers.diffusers-docs stdio, no huggingface
```

If a Cloud Agent is already on the fork, the boot install is that JSON. You do not re-run attach live unless `.cursor/` is missing. Overlay clearance is still the file-scoped gate, not Hugging Face Actions.

