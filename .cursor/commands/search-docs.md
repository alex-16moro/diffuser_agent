# /search-docs — optional keyword search of bundled / checkout docs

Usage: `/search-docs <query>`

Prefer `conventions/rules.yaml` and, on the library, root `AGENTS.md` + `.ai/`
plus the reference source those files name. Default `.cursor/mcp.json` has no
servers.

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
