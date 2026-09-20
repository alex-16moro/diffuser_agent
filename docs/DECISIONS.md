# Decisions (binding)

These were made before this submission pass. Do not silently reopen them.

1. **One registry, many views.** `conventions/rules.yaml` is the only source of
   truth. Agent rules, AGENTS.md, PM/QA/DevOps projections, CI YAML, issue/PR
   templates, GrokBot specs, iPhone/desktop profiles, and Cursor subagents
   are generated. Humans edit the YAML.

2. **The unit is the change.** Rules are tagged `owner: dev | architect | qa |
   pm | devops` so roles co-author one list. Multiplicity of workers is fine;
   multiplicity of sources of truth is not.

3. **GrokBot is read-side.** Per-audience agents brief a first-contribution
   PR (QA testing risk, PM timeline/dependencies, DevOps CI/CD). They never
   gate. The **repo spec** (`agents/grokbot-*.md`) wins; Edit Profile is a
   stub. Trigger: PR opened / updated, not merge. Optional DevOps-only
   follow-up on merge (landed-on-main note).

4. **Gate is file-scoped on the library fork.** Never `convention_check.py --all`
   on the full diffusers tree.

5. **Default fork MCP is empty.** Cloud launches must not prompt for Hub OAuth
   or broken stdio cwd. CLI `docs_mcp_server.py --query` is the fallback.

6. **Scaffold the contract, not the sampler.** Leave `TODO(engineer)` in `step()`.
