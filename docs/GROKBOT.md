# Grok Bots — repo spec wins

Grok Bot does **not** import git. Paste a **short stub** into Edit Profile
once. On every job the Bot `git pull`s this kit and reads
`agents/grokbot-<role>.md`. That file is the real instructions.

| Layer | Where | Changes when |
|-------|--------|----------------|
| Stub | Edit Profile (Name / Title / Description) | Almost never. Re-paste only if standing orders change. |
| Spec | `agents/grokbot-{qa,pm,devops}.md` | Every `make build` / git pull. Briefing shape lives here. |
| Trigger | Desktop routine: GitHub `pull_request` | Created once. iPhone can run it, not edit it. |

Trigger: **PR opened** (including draft), **synchronize**, **ready_for_review**
for QA, PM, and DevOps. Optional **DevOps-only** follow-up: PR **closed as
merged** — a four-line “landed on main?” note. QA and PM stay silent on merge.

They never gate, never fail CI, never merge.

```bash
make grokbot-pack    # print stubs + first messages + routine text
```

---

## Already-created Bots (do this once)

Name/Title stay **Ramp Kit QA / PM / DevOps**. Send each Bot the
**First message** from `agents/grokbot-profiles.md` (or paste the new
short Description over the old long one).

Then on desktop, one routine per Bot: GitHub pull_request opened. Paste
the **Routine** block from the same file. For DevOps only, a second
optional routine: pull_request **closed as merged**.

After that, instruction edits propagate with `git pull`. You do not
re-paste the briefing body.

---

## What each spec asks for

| Bot | Spec | On a first-contribution PR, write |
|-----|------|-----------------------------------|
| Ramp Kit QA | `agents/grokbot-qa.md` | Testing impact, coverage vs residual risk (math, duplication). Overlay-green ≠ tested. |
| Ramp Kit PM | `agents/grokbot-pm.md` | Timeline, dependencies, project risks. Scaffold ≠ product-done. |
| Ramp Kit DevOps | `agents/grokbot-devops.md` | CI/CD impact on open/update. Optional: four-line landed note after merge. Never `--all`. |

Kit repo (specs): `https://github.com/alex-16moro/diffuser_agent`  
Typical PR to brief: `https://github.com/alex-16moro/diffusers` (fork).

---

## After a spec edit

```bash
make build
git push
```

The Bot pulls on the next PR event. If a routine is already running against
a stale clone, tell it `git -C /workspace/diffuser_agent pull` once.
