---
name: search-docs
description: Ground answers in this repo's diffusers docs (same corpus as the search_docs MCP tool). Use before scaffolding or answering how the library does X, especially when the search_docs MCP tool is missing.
---

# Search bundled diffusers docs

Cloud Agents often do not load project `.cursor/mcp.json`, so `search_docs` may
be absent until the Cloud MCP dropdown is `diffusers-docs-mcp` (or
`python3 -u .cursor/mcp-diffusers-docs.py`). This skill is the same grounding
path.

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

If the MCP tool `search_docs` **is** in your tool list, call that instead; it is
the same server (`python3 -u .cursor/mcp-diffusers-docs.py` / dashboard stdio).
