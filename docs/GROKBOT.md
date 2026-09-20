# Wire Ramp Kit GrokBots to the iPhone Grok Bot app

Cursor **Grok Bot** (iOS App Store id `6794501026`, also desktop) is a
messaging client over a persistent cloud computer. It does **not** import
`agents/*.md` from git. The kit therefore emits paste-ready profiles from the
same registry that feeds the gate.

| Surface | What it is | Gates? |
|---------|------------|--------|
| `agents/grokbot-profiles.md` | Name / Title / Description / first message to paste into the app | No |
| `agents/grokbot-{pm,qa,devops}.md` | Full owner-tagged spec the Bot reads after clone | No |
| `.cursor/agents/grokbot-*.md` | Cursor subagents if Grok Bot spawns a Cloud Agent on this repo | No |
| `tools/grokbot_sim.py` / `make grokbot ROLE=qa` | Reproducible CLI briefing from `convention_check --json` | No |

The gate remains `tools/convention_check.py`. These Bots translate. They never
fail CI and never merge.

Print the paste pack:

```bash
make grokbot-pack
```

---

## On the iPhone (about 3 minutes)

Use **Grok Bot**, not the Cursor for iOS app. Sign in with the **same Cursor
account** that has a paid plan (Pro / Pro+ / Ultra / Teams). Privacy Mode
(Legacy) blocks Grok Bot until you switch to Privacy Mode.

1. Open Grok Bot → **New** → **Create your own** (or Create new Bot).
2. **Bot actions → Edit Profile**. Paste **Name**, **Title**, and **Description**
   from the matching block in `agents/grokbot-profiles.md`.
3. Send the **First iPhone message** from that block as the opening chat.
   Approve clone into `/workspace/diffuser_agent` if the Bot asks.
4. Repeat for the three Bots, in this order (QA is the live-demo role):

   | Name | Title | Spec |
   |------|-------|------|
   | Ramp Kit QA | Risk briefing | `agents/grokbot-qa.md` |
   | Ramp Kit PM | Status digest | `agents/grokbot-pm.md` |
   | Ramp Kit DevOps | Health signal | `agents/grokbot-devops.md` |

5. Optional: swipe a Bot → **Move to** → **New Section** named `Ramp Kit`
   (Grok Bot iOS 1.2.0+). Sections sync with desktop.
6. Optional: start a **group chat** with the three and `@` the role you want.

To brief a change from the phone after the Bot has the repo:

> Run `python3 tools/convention_check.py --json examples/candidate_scheduler || true`
> then `python3 tools/grokbot_sim.py --role qa` and paste the briefing.

Or paste gate JSON into the chat and ask for the role-shaped output.

---

## Desktop-only (not on iPhone)

- **Share → Create template** produces an x.ai preview link. Recipients tap
  **Add to Grok Bot**. Copies identity, description, skills, routines — not
  your computer, logins, or chat history. Strip secrets first.
- **Routines** (schedule / webhook) that POST gate JSON. Save the routine,
  then copy **POST to** + `Authorization: Bearer`. HTTP 200 means a run
  started, not that the briefing finished.
- Teach-by-demonstration, routine edit/history, computer update/reset.

Plugins (GitHub, etc.) are **account-wide**: a login for QA is visible to PM
and DevOps on the same Grok Bot computer.

---

## After a registry edit

```bash
make build          # regenerates specs + iPhone profiles + Cursor subagents
make grokbot-pack   # re-copy Description into Edit Profile if owner-tagged rules changed
```

Do not hand-edit generated files. Humans edit `conventions/rules.yaml`.
