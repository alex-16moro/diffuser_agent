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

5. **Grok Bot has no create-from-git API.** The iPhone/desktop app does not
   import `agents/*.md`. The kit generates paste-ready profiles
   (`agents/grokbot-profiles.md`) and Cursor subagents (`.cursor/agents/`).
   `grokbot_sim.py` remains the reproducible briefing. Bots never change
   exit codes and never merge.

6. **TEST002 uses a new check type `test_adequacy`.** Assertion counting is
   structural (AST), not a regex. Determinism and shape/dtype reuse mention
   scans, same family as TEST001.

7. **Fork overlay attach is the demo path, not an upstream PR.** Overlay may
   add `.cursor/` to the fork (empty `mcp.json`). It must not rewrite
   `AGENTS.md` or `.ai/`.

8. **No Euler math.** `step()` stays `TODO(engineer)` in templates and scaffolds.
