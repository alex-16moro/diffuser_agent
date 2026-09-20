---
name: search-docs
description: Optional keyword search of this repo's diffusers docs via docs_mcp_server.py --query. Prefer the registry, .ai/, and reference source. Use before scaffolding or answering how the library does X.
---

# Search bundled diffusers docs

Default `.cursor/mcp.json` has no servers. Ground first in
`conventions/rules.yaml` and, on the library, `AGENTS.md` + `.ai/` plus
reference source. This skill is an optional CLI fallback.

Run (do not invent the contract from memory):

```bash
python3 tools/docs_mcp_server.py --query "<the question>"
```

If the query is empty, use:

```bash
python3 tools/docs_mcp_server.py --query "scheduler set_timesteps step SchedulerMixin register_to_config"
```

Cite the provenance line (`bundled snapshot` vs a real checkout). If snippets
miss the contract, read `conventions/rules.yaml` — the **gate** is authoritative.
