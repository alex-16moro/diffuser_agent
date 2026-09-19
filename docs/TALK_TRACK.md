# Talk track — 45-minute session + final-round stakeholder defense

Two parts: (A) the screen session, (B) the final-round role-play. Both assume
you run the artifact **live**.

**Sequence:** show **this kit** first, then switch to the **library fork**
([alex-16moro/diffusers](https://github.com/alex-16moro/diffusers)). Do not
open on the fork until they have seen the registry and the gate.

---

## A. The 45-minute screen (timeboxed)

### 0–5 min · Frame the problem (before touching code)
- "The repository already holds a lot of engineering knowledge — but it's
  *distributed* across the `.ai/` agent guidance, the docs, code patterns, tests,
  and CI. A new engineer has to reassemble it, and learns each rule the slow way:
  a red PR, a review round-trip."
- "So I'm not criticizing the repo or writing conventions it lacks. My goal was to
  turn those scattered signals into **one governed contribution workflow** that
  makes the path from task to review-ready change explicit — and extends it to the
  rest of the team, PM/QA/DevOps, which is the gap the customer named."
- "One decision drives everything: **conventions are data, not prose** — and they
  come from the repository, not model memory."
- "Two repos, one overlay: this kit is the customer layer; the live write lands
  on a **fork**, not on huggingface/diffusers. PRs are titled
  `[fork demo — not for upstream]`."

### 5–8 min · The architecture in one breath
- Show `conventions/rules.yaml`. "Humans edit only this. `make build` projects it
  into the agent's rules, `AGENTS.md`, the PM's Definition of Done, the issue/PR
  templates, the QA checklist, and the CI workflow GitHub actually runs. They
  can't drift, because they're one source rendered several ways."
- **Anti-fragmentation (say this out loud):** "I did not add a tool per SDLC
  step. Plan, build, review, test, and CI clearance are *projections of the same
  YAML*. A sixth capability named 'deploy' would be fragmentation — I stop at
  the gate, because I don't have the customer's deploy env."

### 8–22 min · Live contribution (`docs/LIVE_DEMO.md`) — kit first, then fork

**8–12 min · this kit (overlay).** Do not launch the fork agent yet.

1. **Catch the bad.** `examples/candidate_scheduler` — 8 blocking + 2 warnings.
   Point at `DEPR001` (import moved) and `SCHED003` (no `@register_to_config`).
2. "This is the overlay. It is not the library. The gate is
   `tools/convention_check.py`; the registry is `conventions/rules.yaml`."
3. If the room is cold on Cursor: `make demo-contribute KEEP=1` as rehearsal.
   Otherwise save the files-on-disk beat for the fork.

**12–22 min · the fork (real library).** Launch / paste Prompt A on
`alex-16moro/diffusers`. Overlay is `ramp-kit/` (gitignored clone).

1. **Ground in source, then the gate.** Open
   `src/diffusers/schedulers/scheduling_euler_discrete.py` and
   `scheduling_ddpm.py`. "Code beats the philosophy doc (`set_timesteps`, not
   `set_num_inference_steps`). The gate is still the authority."
2. **Scaffold.** `/scaffold scheduler EulerLite` writes
   `src/diffusers/schedulers/scheduling_euler_lite.py`. Open the
   `TODO(engineer)` in `step`. "Contract, not the algorithm."
3. **File-scoped gate only** — never `--all` on this library. 0 findings on the
   new file; behavioral tests skip without torch.
4. **PR this fork**, draft, title `[fork demo — not for upstream]`. Overlay
   clearance ≠ Hugging Face CI. We do **not** delete inherited workflow files.

Do not run kit `KEEP=1` before the fork agent if you want those files to appear
live on the fork.

MCP is **not** this beat. Default overlay `.cursor/mcp.json` is empty so Cloud
does not hit Hub OAuth or stdio cwd failures. Opt-in: `.cursor/mcp.optional.json`.
If they ask how docs were searched: CLI
`python3 ramp-kit/tools/docs_mcp_server.py --query "..."`.

### 22–30 min · Multi-audience + boundaries
- Open `projections/pm/definition-of-done.md`, `qa/review-checklist.md`,
  `.github/workflows/convention-gate.yml`, and `.github/ISSUE_TEMPLATE/contribution.md`.
  "Same rules. The PM's intake is the author's PR checklist is the CI gate.
  That's the one-solution-many-audiences ask, made literal. Note
  the registry separates upstream conventions from our customer guardrails."
- Open `.cursorignore`. "Requirement 3 — the agent's **context** boundary: Cursor
  won't feed these paths to the agent, shrinking the blast radius of an over-eager
  scaffold. I'm careful here: this is not the *security* boundary — production
  adds filesystem, network, credential, and tool permissions. This just keeps the
  agent's context clean."

### 30–38 min · Judgment: the design that scales, and what I skipped
- "It's five fixed primitives driven by data — registry, gate, scaffold, docs
  search (CLI / optional MCP), projections. Adding a component (model, pipeline)
  is registry rows + a template, not a new command. That's `make build`
  regenerating a `10-<component>.mdc` from a tag — I can show that live in
  under a minute."
- "I did not grow a capability per SDLC step. That is how these kits fragment."
- "The fork overlay ships **empty MCP by default**. Cloud Agents skip project
  `mcp.json`; stdio cannot set `cwd` or expand `${workspaceFolder}`; Hub HTTP
  MCP is Hub search + OAuth, not library source. Grounding is Read/Grep on the
  two scheduler files, then the gate. Keyword MCP/`--query` is opt-in on
  Desktop (`mcp.optional.json`). I skipped *embeddings* inside that search —
  keyword over curated docs first."
- "I went deep on schedulers, not shallow on all three components, because
  schedulers have the crispest enforceable contract — the best proof."
- "No auto-fix: on a numerical library, auto-fix is where you inject silent wrong
  corrections. Report-and-block first; mechanical auto-fix later."
- "I left Hugging Face's inherited Actions alone. Disabling them by deleting
  workflow files would look like I broke their CI; the honest story is overlay
  clearance on a fork demo."

### 38–45 min · Where it breaks (lead with this, don't hide it)
- "It checks structure, not the correctness of the math — by design; that's the
  reviewer's job and the QA checklist says so."
- "`# Copied from` is a well-formedness check, not the full `fix-copies` graph."
- "Deprecation coverage is only as fresh as the maps — import moves *block*
  (deterministic), renamed kwargs only *warn*, because a substring isn't proof of
  deprecation in a version. False positives destroy trust, so blocking rules need
  stronger evidence than warnings."
- "The docs CLI defaults to a bundled snapshot when it isn't sitting on a real
  checkout; every result states provenance, so I never overclaim 'version-correct'."
- "Fork GitHub Actions may go red. That is Hugging Face's CI on a demo branch,
  not a failed overlay gate."
- Close: "If I don't know something — say, whether a convention still holds after
  a refactor — the honest move is to make it a rule and let the gate tell us."

### The grounding story (use it if the contract is questioned)
If a reviewer says "current diffusers schedulers use `set_num_inference_steps`":
> "That's what the *philosophy doc* says — I checked the *code*. `DDPMScheduler`
> and `EulerDiscreteScheduler` on `main` both define `set_timesteps`; the doc is
> stale. My rule cites those source files, not the doc. This is exactly why I
> ground rules in the repository and validate — a doc-grounded or memory-grounded
> system would have shipped the wrong contract."
This turns the single biggest risk to the thesis into its strongest proof.

---

## B. Final round — align with ADM, defend to a skeptical stakeholder, tie to account value

### The account-value one-liner (lead with it)
> "This turns 'ramp' from a people-cost you pay per hire into a repo asset that
> compounds. Every convention we encode is one the customer never re-teaches and
> never re-reviews by hand again."

### Aligning with the ADM (before the room)
- Tie to a metric the ADM already reports: **time-to-first-merged-PR** and
  **review round-trips per PR**. Both are directly attacked by the gate.
- Position it as a **land-and-expand wedge**: schedulers today → models/pipelines
  → the customer's *private* library (same registry, their rules). That's the
  expansion path, and it needs no rebuild.
- Name the champion: the platform team that owns ramp. This makes *them* look good
  to *their* stakeholders — that's who renews.

### Skeptical-stakeholder Q&A (rehearsed answers)

**"We already have `.ai/` / a linter / CONTRIBUTING.md. Why this?"**
> "Those serve the agent and the reviewer. Yours don't reach PM, QA, or DevOps,
> and they can drift from CI. This makes one source drive all five and enforces
> it identically in the editor and in CI. I built *on* your `.ai/` pattern, not
> against it."

**"Isn't this just a wrapper around a linter?"**
> "The linter is one of five projections. The value is that the reviewer's
> checklist, the PM's Definition of Done, and the CI gate are provably the same
> rules — that's what removes review round-trips, which is the expensive step."

**"Our engineers will hate another gate yelling at them."**
> "Correct code passes with zero findings — I'll show you. Warnings never block.
> Every finding ships a fix. And it fires in-editor, so it feels like help, not a
> tribunal at PR time."

**"Who maintains this when you're gone?"** (requirement 4 — the renewal question)
> "The team edits one YAML file. Add a rule, `make build`, done. The build fails
> if a rule isn't enforced, so it can't rot into documentation-only. There's no
> me-shaped dependency."

**"What's the ROI?"**
> "Two levers: fewer review round-trips (senior time, the scarcest resource) and
> faster time-to-first-merge (new-hire productivity). Both are things your ADM
> already measures. We can baseline them in week one and re-measure in a month."

**"Where does it fall down?"**
> "It won't judge whether the math is right — that stays human. I'd rather be
> honest about that boundary than sell you an oracle. 'I don't know, here's how
> I'd find out' is the posture I want on your account too."

**"Why not MCP / embeddings / a tool per step?"**
> "Grounding that survives a skeptical reviewer is the two scheduler source
> files plus the gate. MCP on Cloud failed discovery and Hub OAuth is the wrong
> corpus. Embeddings add a model I don't need for a 45-minute proof. A tool per
> SDLC step is how the kit would fragment the moment you asked for deploy."

### If asked to extend it live (they said you'll reuse this)
- Add a rule to `rules.yaml` (e.g. a new deprecated import), `make build`,
  `make check` — show the new rule enforced across every surface in under a
  minute. That live edit *is* the maintainability proof.
