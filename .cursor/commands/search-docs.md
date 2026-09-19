# /search-docs — grounded diffusers docs (MCP fallback)

Usage: `/search-docs <query>`

Cloud Agents **do not load** project `.cursor/mcp.json`, and Cloud stdio
**does not expand** `${workspaceFolder}` (that is why the tool goes missing).
If `search_docs` is not in your tool list, this command is the connection.
The Cloud dropdown paste is `python3 -u .cursor/mcp-diffusers-docs.py`.

Run this exactly (do not invent an answer from memory):

```bash
python3 tools/docs_mcp_server.py --query $1
```

If `$1` is empty, use:

```bash
python3 tools/docs_mcp_server.py --query "scheduler set_timesteps step SchedulerMixin register_to_config"
```

Then cite the provenance line (`bundled snapshot` vs a real checkout) and the
matching section. If the snippets miss the contract, also read
`conventions/rules.yaml` — the **gate** is authoritative.

If the `diffusers-docs` / `search_docs` MCP tool **is** available, call that
instead of the CLI; it is the same server.
