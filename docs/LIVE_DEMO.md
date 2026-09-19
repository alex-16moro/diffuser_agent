# Live contribution demo — run this in the 45-minute screen

Goal: show **how a new engineer makes a first contribution**, not how to use
Diffusers. Open **this repo root** as the Cursor workspace.

Two ways to play the same journey:

| Path | When |
|------|------|
| **A. Cursor agent** (`/scaffold scheduler EulerLite`) | Primary. This is the customer motion. |
| **B. CLI twin** (`make demo-contribute KEEP=1`) | Rehearsal, or if slash-command / MCP stalls. Same files, same gate. |

Do **not** run Path B first if you want Path A to create the files live.

---

## The journey (what you narrate)

```
plan → ground → build → gate → test → review → CI clearance
```

| Step | Role | You show | You say |
|------|------|----------|---------|
| 0. Pre-flight | you | `make doctor` | “Python3, PyYAML, Cursor files present.” |
| 1. Plan | PM + engineer | `.github/ISSUE_TEMPLATE/contribution.md` | “Done is the same checklist CI will run.” |
| 2. Catch-early | QA / engineer | gate on `examples/candidate_scheduler` | “8 blocking: moved import, missing mixin, `.cuda()`, no test. That’s a review round-trip.” |
| 3. Ground | engineer | MCP `search_docs` or `make mcp` | “Repo docs, not model memory. Gate is still the authority.” |
| 4. Build | engineer | `/scaffold scheduler EulerLite` | “Contract stub. Math is TODO. I will not invent a sampler.” |
| 5. Gate | engineer + CI | check the new file | “0 findings. Same script as the edit hook and GitHub Actions.” |
| 6. Test | engineer | unittest on the new test | “Signatures pass; behavioral tests skip without torch — expected.” |
| 7. Review | QA | `projections/qa/review-checklist.md` | “Gate took the mechanical items. Humans judge the paper.” |
| 8. Clearance | DevOps | `.github/workflows/convention-gate.yml` | “Green = merge-eligible. I don’t fake deploy.” |
| 9. Maintain | platform | `make demo-maintain` (if time) | “One YAML edit. I’m gone; they still own it.” |

---

## Path A — Cursor (primary, ~10–12 min)

Pre-flight (before they sit): MCP `diffusers-docs` enabled, rules visible.

Paste **Prompt A** from `docs/CURSOR_PROMPTS.md`, or type:

```
/scaffold scheduler EulerLite
```

Then have the agent (or you) run:

```bash
python3 tools/convention_check.py examples/candidate_scheduler
python3 tools/convention_check.py src/diffusers/schedulers/scheduling_euler_lite.py
python3 -m unittest tests.schedulers.test_scheduling_euler_lite -v
```

Point at the `TODO(engineer)` in `step`. Stop. Do not fill in Euler math.

If MCP is off: `python3 tools/docs_mcp_server.py --query "scheduler set_timesteps step"`.

If `/scaffold` does not appear: open `.cursor/commands/scaffold.md` and say “it’s a guided command, not a binary,” then Path B.

---

## Path B — CLI twin (rehearsal / fallback)

```bash
make doctor
make demo-contribute KEEP=1          # leaves EulerLite on disk
# walk the printed steps with them
make demo-contribute-clean           # remove when done
```

Default `make demo-contribute` **creates, proves, and deletes** (safe to run in CI / rehearsal). `KEEP=1` is the live “files appear” mode.

---

## Timebox vs the rest of the 45 minutes

- **0–5** problem (distributed conventions → review round-trips)
- **5–8** `rules.yaml` → many surfaces
- **8–22** this contribution journey (catch bad → scaffold → green gate)
- **22–30** QA + issue template + CI + `.cursorignore`
- **30–38** judgment (schedulers first, no embeddings, no auto-fix, stop at CI)
- **38–45** where it breaks + `make demo-maintain` if not already shown

If time is tight, skip maintain and skip Path A’s agent: run Path B with `KEEP=1` and still open the two files.

---

## Cleanup

```bash
python3 tools/demo_contribute.py --clean-only --name EulerLite
```

Do not commit `scheduling_euler_lite.py` unless you explicitly want it as a fixture. The live point is **creating** it.
