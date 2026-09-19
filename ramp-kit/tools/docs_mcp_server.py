#!/usr/bin/env python3
"""
docs_mcp_server.py — a real MCP server that gives the agent GROUNDED search over
the library's own docs, so "how does diffusers do X" is answered from THIS repo
at THIS version, not from stale training memory.

WHY THIS IS A PRIMITIVE (not per-task tooling): discovery is component-agnostic.
The same server serves scheduler, model, and pipeline questions — you scale it
by pointing it at more docs, never by adding new machinery. It complements the
convention gate: the gate stops WRONG code; doc-search improves DISCOVERY.

TRANSPORT: MCP stdio — newline-delimited JSON-RPC 2.0 on stdin/stdout. Cursor
launches it from .cursor/mcp.json. Implemented with the standard library only,
so it runs on a fresh clone / GPU-less CI with zero installs (a hard PyPI-free
constraint we actually hit while building this).

Methods implemented: initialize, notifications/initialized, ping, tools/list,
tools/call (tool: search_docs).

Run modes:
  python tools/docs_mcp_server.py --serve            # MCP stdio (what Cursor uses)
  python tools/docs_mcp_server.py --query "..."      # CLI, for offline testing
  python tools/docs_mcp_server.py --selftest         # simulate the MCP handshake
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUNDLED = REPO_ROOT / "knowledge" / "diffusers-docs"


def resolve_docs_root() -> tuple[Path, str]:
    """Prefer a REAL diffusers checkout; fall back to the bundled snapshot.

    Resolution order (first that exists wins):
      1. $DIFFUSERS_DOCS_ROOT (explicit override)
      2. a sibling/nested diffusers checkout's docs (./diffusers, ../diffusers)
      3. the bundled seed corpus (reproducible offline demo fallback)

    Returns (path, provenance) so callers can label results honestly instead of
    claiming "version-correct" unconditionally.
    """
    env = os.environ.get("DIFFUSERS_DOCS_ROOT")
    if env and Path(env).exists():
        return Path(env), "configured checkout ($DIFFUSERS_DOCS_ROOT)"
    for cand in (REPO_ROOT / "diffusers" / "docs" / "source" / "en",
                 REPO_ROOT.parent / "diffusers" / "docs" / "source" / "en"):
        if cand.exists():
            return cand, "detected diffusers checkout"
    return BUNDLED, "bundled snapshot (offline fallback — may lag upstream)"


DOCS_ROOT, DOCS_PROVENANCE = resolve_docs_root()

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "diffusers-docs", "version": "0.4.0"}

SEARCH_DOCS_TOOL = {
    "name": "search_docs",
    "description": (
        "Search the configured diffusers docs for grounded context (a real checkout "
        "when available, else a bundled snapshot — results state their provenance). "
        "Use before answering 'how does the library do X' or before scaffolding, so "
        "code matches the repository rather than an old blog post or model memory."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural-language question or keywords."},
            "k": {"type": "integer", "description": "Max results (default 5).", "default": 5},
        },
        "required": ["query"],
    },
}


# --------------------------------------------------------------------------- #
# Core search (shared by CLI and MCP)                                          #
# --------------------------------------------------------------------------- #
def search_docs(query: str, k: int = 5, root: Path = DOCS_ROOT):
    """Return up to k doc sections matching the query (keyword TF score).

    Ranking is deliberately simple and dependency-free. The honest upgrade path
    is embeddings if recall proves weak — but keyword search over curated docs
    is a strong, debuggable baseline and needs no model download.
    """
    terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]
    results = []
    if not root.exists():
        return results
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for sec in re.split(r"(?m)^#{1,4}\s+", text):
            if not sec.strip():
                continue
            low = sec.lower()
            score = sum(low.count(t) for t in terms)
            if score:
                heading = sec.splitlines()[0][:100]
                snippet = " ".join(sec.split())[:280]
                results.append((score, str(path.relative_to(root)), heading, snippet))
    results.sort(key=lambda r: (-r[0], r[1]))
    return [{"score": s, "path": p, "heading": h, "snippet": sn} for s, p, h, sn in results[:k]]


def _format_hits(hits) -> str:
    header = f"(source: {DOCS_PROVENANCE})"
    if not hits:
        return (f"{header}\nNo matches in {DOCS_ROOT}. Point DIFFUSERS_DOCS_ROOT at a "
                f"diffusers docs checkout for full coverage.")
    out = [header]
    for h in hits:
        out.append(f"[{h['path']}] {h['heading']}\n{h['snippet']}")
    return "\n\n".join(out)


# --------------------------------------------------------------------------- #
# MCP stdio server                                                             #
# --------------------------------------------------------------------------- #
def _handle(msg: dict):
    """Dispatch one JSON-RPC request; return a response dict or None (notify)."""
    method = msg.get("method")
    mid = msg.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": mid,
            "result": {
                "protocolVersion": msg.get("params", {}).get("protocolVersion", PROTOCOL_VERSION),
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }
    if method in ("notifications/initialized", "initialized"):
        return None  # notification, no reply
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": [SEARCH_DOCS_TOOL]}}
    if method == "tools/call":
        params = msg.get("params", {})
        if params.get("name") != "search_docs":
            return {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32602, "message": f"unknown tool {params.get('name')}"}}
        args = params.get("arguments", {})
        hits = search_docs(args.get("query", ""), int(args.get("k", 5)))
        return {"jsonrpc": "2.0", "id": mid,
                "result": {"content": [{"type": "text", "text": _format_hits(hits)}],
                           "isError": False}}
    # Unknown method
    if mid is not None:
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32601, "message": f"method not found: {method}"}}
    return None


def serve(stdin=None, stdout=None):
    """Run the MCP stdio loop: read newline-delimited JSON-RPC, write responses."""
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = _handle(msg)
        if resp is not None:
            stdout.write(json.dumps(resp) + "\n")
            stdout.flush()


# --------------------------------------------------------------------------- #
def _selftest() -> int:
    """Simulate the Cursor handshake end-to-end and assert the responses."""
    import io
    reqs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "search_docs", "arguments": {"query": "scheduler set_timesteps step", "k": 2}}},
    ]
    stdin = io.StringIO("\n".join(json.dumps(r) for r in reqs) + "\n")
    stdout = io.StringIO()
    serve(stdin, stdout)
    lines = [json.loads(l) for l in stdout.getvalue().splitlines() if l.strip()]
    assert lines[0]["result"]["serverInfo"]["name"] == "diffusers-docs", "initialize failed"
    assert lines[1]["result"]["tools"][0]["name"] == "search_docs", "tools/list failed"
    assert "content" in lines[2]["result"], "tools/call failed"
    print("MCP self-test OK: initialize -> tools/list -> tools/call all responded.")
    print("  tools/call returned:\n   ",
          lines[2]["result"]["content"][0]["text"].replace("\n", "\n    ")[:400])
    return 0


def main(argv):
    if "--serve" in argv:
        serve()
        return 0
    if "--selftest" in argv:
        return _selftest()
    if "--query" in argv:
        i = argv.index("--query")
        q = " ".join(argv[i + 1:]) or "scheduler"
        print(_format_hits(search_docs(q)))
        return 0
    print(__doc__)
    print(f"[info] DOCS_ROOT = {DOCS_ROOT} (exists: {DOCS_ROOT.exists()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
