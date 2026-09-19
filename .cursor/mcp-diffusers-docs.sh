#!/usr/bin/env bash
# Launch the diffusers-docs MCP server for Cursor (IDE + Cloud Agent stdio).
# Always chdir to the repo root so it works whether cwd is the workspace
# or .cursor/. Cloud stdio cannot set cwd in the MCP config.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec python3 -u "$ROOT/tools/docs_mcp_server.py" --serve
