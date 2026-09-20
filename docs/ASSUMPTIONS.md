# ASSUMPTIONS log

Recorded while taking the kit to submission quality. If an assumption is wrong,
the matching verify still stands; update the registry, not this file, for
contract facts.

1. **Docs vs source.** Bundled/checkout docs do not reliably name `set_timesteps`.
   Fork source (`scheduling_ddpm.py`, `scheduling_euler_discrete.py`) does.
   Source wins. The contract re-verify script encodes that.

2. **`docs/DECISIONS.md` was absent.** Decisions in the screen brief are treated
   as binding: one registry, `owner` tags, GrokBot as read-side only, empty
   default MCP on the fork.

3. **Kit `make check --all` is in-kit only.** It must never be aimed at the
   full huggingface/diffusers tree. On the fork, the gate is file-scoped.

4. **Adjacent fork in this workspace.** `library_paths.resolve_library_root()`
   correctly prefers `/agent/repos/diffusers` when that checkout exists. Kit-only
   CI without the fork SKIPs contract re-verify rather than failing false-red.

5. **Grok Bot loads instructions from git, not from Edit Profile.** The
   iPhone/desktop app does not import `agents/*.md`. Edit Profile is a
   short stub (`git pull`, then read `agents/grokbot-<role>.md`). Spec
   changes propagate on the next PR-opened run. Bots never change exit
   codes and never merge. Trigger is PR opened / synchronize /
   ready_for_review — not merge. Optional DevOps-only: closed-as-merged
   landed note.

6. **TEST002 uses a new check type `test_adequacy`.** Assertion counting is
   structural (AST), not a regex. Determinism and shape/dtype reuse mention
   scans, same family as TEST001.

7. **Fork overlay attach is the demo path, not an upstream PR.** Overlay may
   add `.cursor/` to the fork (empty `mcp.json`). It must not rewrite
   `AGENTS.md` or `.ai/`.

8. **No Euler math.** `step()` stays `TODO(engineer)` in templates and scaffolds.

9. **PM is a status-view role.** A "PR references an issue" regex-on-body
   check cannot be grounded in `convention_check.py` (file scans only). A
   no-op check would be a fake gate. PM keeps DOC001 (warn, docstrings) and
   briefs live DoD state + merge-eligibility from gate blocking count +
   issue/milestone from change-context. No fabricated velocity or dates.

10. **Change-context is the offline stand-in for the PR event.** Schema:
    `examples/change_context.example.json` (`pr`, `ci`, `state`).
    `grokbot_sim.py --context` fuses that with gate JSON. When gate JSON is
    omitted and stdin is a TTY, the sim scans `examples/scaffolded_scheduler`
    (0 findings) so the EulerLite demo is offline-runnable. Source tags on
    every claim: `[gate]` `[ci]` `[issue]` `[drift]`.

11. **Fork overlay CI is file-scoped, not kit `--all`.** The DevOps gap on
    first-contribution PRs was: no GitHub check-run for the overlay gate,
    and the bot recommended enabling kit `convention-gate.yml` (which
    would `--all` the library). Attach now copies
    `overlay/ramp-kit-overlay.yml`. DevOps must not recommend copying the
    kit `--all` workflow onto the fork. Inherited HF Actions idle/red on
    a fork demo stay expected. A new workflow does not run until it exists
    on the PR base (`main`). Merge follow-up reports the **base** branch,
    not the topic head.
