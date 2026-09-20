# Decisions (binding)

These were made before this submission pass. Do not silently reopen them.

1. **One registry, many views.** `conventions/rules.yaml` is the only source of
   truth. Agent rules, AGENTS.md, PM/QA/DevOps projections, CI YAML, issue/PR
   templates, GrokBot specs, iPhone/desktop profiles, and Cursor subagents
   are generated. Humans edit the YAML.

2. **The unit is the change.** Rules are tagged `owner: dev | architect | qa |
   pm | devops` so roles co-author one list. Multiplicity of workers is fine;
   multiplicity of sources of truth is not.

3. **GrokBot is read-side.** Per-audience agents translate `convention_check
   --json` and CI. They never gate. `tools/grokbot_sim.py` is the reproducible
   CLI briefing. The Grok Bot iPhone/desktop app is wired by pasting
   generated profiles (`make grokbot-pack`); there is no Bot-from-git API.

4. **Gate is file-scoped on the library fork.** Never `convention_check.py --all`
   on the full diffusers tree.

5. **Default fork MCP is empty.** Cloud launches must not prompt for Hub OAuth
   or broken stdio cwd. CLI `docs_mcp_server.py --query` is the fallback.

6. **Scaffold the contract, not the sampler.** Leave `TODO(engineer)` in `step()`.
