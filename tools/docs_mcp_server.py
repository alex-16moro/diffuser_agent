#!/usr/bin/env python3
"""
docs_mcp_server.py — a real MCP server that gives the agent GROUNDED search over
the library's own docs, so "how does diffusers do X" is answered from THIS repo
at THIS version, not from stale training memory.

WHY THIS IS A PRIMITIVE (not per-task tooling): discovery is component-agnostic.
The same server serves scheduler, model, and pipeline questions — you scale it
by pointing it at more docs, never by adding new machinery. It complements the
convention gate: the gate stops WRONG code; doc-search improves DISCOVERY.

TRANSPORT: MCP stdio — JSON-RPC 2.0 as newline-delimited JSON (what Cursor
expects on stdio). The reader still accepts Content-Length (LSP-style) as
well as NDJSON, so older clients keep working. Cursor Desktop launches it
from .cursor/mcp.json via .cursor/mcp-diffusers-docs.py (workspace-relative
arg; no ${workspaceFolder} — Cloud stdio does not expand it and cannot set
cwd). Implemented with the standard library only, so it runs on a fresh
clone / GPU-less CI with zero installs (a hard PyPI-free constraint we
actually hit while building this).

Methods implemented: initialize, notifications/initialized, ping, tools/list,
tools/call (tool: search_docs).

Run modes:
  python3 tools/docs_mcp_server.py --serve            # MCP stdio (what Cursor uses)
  python3 tools/docs_mcp_server.py --query "..."      # CLI, for offline testing
  python3 tools/docs_mcp_server.py --selftest         # simulate the MCP handshake
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from library_paths import (  # noqa: E402
    BUNDLED_DOCS as BUNDLED,
    KIT_ROOT as REPO_ROOT,
    resolve_docs_root,
)

DOCS_ROOT, DOCS_PROVENANCE = resolve_docs_root()

PROTOCOL_VERSION = "2024-11-05"
SUPPORTED_PROTOCOL_VERSIONS = (
    "2024-11-05",
    "2025-03-26",
    "2025-06-18",
    "2025-11-25",
)
SERVER_INFO = {"name": "diffusers-docs", "version": "0.6.0"}
INSTRUCTIONS = (
    "Ground 'how does diffusers do X' in this repo before scaffolding. "
    "Call search_docs (query + optional k). Results include provenance "
    "(real checkout vs bundled snapshot). conventions/rules.yaml is the "
    "authoritative gate if snippets miss a contract."
)

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
def _coerce_args(args):
    """Cursor sometimes sends tool arguments as a JSON string."""
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return {"query": args}
    return args if isinstance(args, dict) else {}


def _handle(msg: dict):
    """Dispatch one JSON-RPC request; return a response dict or None (notify)."""
    method = msg.get("method")
    mid = msg.get("id")

    if method == "initialize":
        requested = (msg.get("params") or {}).get("protocolVersion", PROTOCOL_VERSION)
        version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else PROTOCOL_VERSION
        return {
            "jsonrpc": "2.0", "id": mid,
            "result": {
                "protocolVersion": version,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"listChanged": False},
                    "prompts": {"listChanged": False},
                },
                "serverInfo": SERVER_INFO,
                "instructions": INSTRUCTIONS,
            },
        }
    if method in ("notifications/initialized", "initialized",
                  "notifications/cancelled", "notifications/progress"):
        return None  # notification, no reply
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "logging/setLevel":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": [SEARCH_DOCS_TOOL]}}
    if method == "resources/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"resources": []}}
    if method == "prompts/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"prompts": []}}
    if method == "tools/call":
        params = msg.get("params", {})
        if params.get("name") != "search_docs":
            return {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32602, "message": f"unknown tool {params.get('name')}"}}
        args = _coerce_args(params.get("arguments", {}))
        try:
            k = int(args.get("k", 5))
        except (TypeError, ValueError):
            k = 5
        hits = search_docs(str(args.get("query", "")), k)
        return {"jsonrpc": "2.0", "id": mid,
                "result": {"content": [{"type": "text", "text": _format_hits(hits)}],
                           "isError": False}}
    # Unknown method — never fail the handshake on optional list calls.
    if mid is not None:
        return {"jsonrpc": "2.0", "id": mid,
                "error": {"code": -32601, "message": f"method not found: {method}"}}
    return None


def _write_message(msg, stdout=None):
    """Write one JSON-RPC message as newline-delimited JSON (MCP stdio spec)."""
    stdout = stdout if stdout is not None else sys.stdout
    stdout.write(json.dumps(msg, separators=(",", ":")) + "\n")
    stdout.flush()


def _read_line_bytes(stdin) -> bytes:
    if hasattr(stdin, "buffer") and not isinstance(stdin, (bytes, bytearray)):
        # text wrapper — prefer the raw buffer so Content-Length is in bytes
        try:
            return stdin.buffer.readline()
        except Exception:
            pass
    line = stdin.readline()
    return line if isinstance(line, bytes) else line.encode("utf-8")


def _read_exact(stdin, n: int) -> bytes:
    buf = getattr(stdin, "buffer", stdin)
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = buf.read(remaining)
        if not chunk:
            break
        if isinstance(chunk, str):
            chunk = chunk.encode("utf-8")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _read_message(stdin):
    """Read one JSON-RPC message. Content-Length (bytes) first; NDJSON fallback."""
    line = _read_line_bytes(stdin)
    if line == b"":
        return None
    text = line.decode("utf-8")
    if text.lower().startswith("content-length:"):
        try:
            length = int(text.split(":", 1)[1].strip())
        except ValueError:
            return None
        while True:
            header = _read_line_bytes(stdin)
            if header in (b"", b"\r\n", b"\n"):
                break
        body = _read_exact(stdin, length)
        return json.loads(body.decode("utf-8"))
    stripped = text.strip()
    if not stripped:
        return _read_message(stdin)
    return json.loads(stripped)


def serve(stdin=None, stdout=None):
    """Run the MCP stdio loop (NDJSON write; Content-Length or NDJSON read)."""
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    # Anything extra on stdout breaks NDJSON. Keep logs on stderr.
    if stdout is sys.stdout:
        sys.stdout.flush()
    while True:
        try:
            msg = _read_message(stdin)
        except json.JSONDecodeError:
            continue
        if msg is None:
            break
        resp = _handle(msg)
        if resp is not None:
            _write_message(resp, stdout)


def _frame(msg: dict) -> bytes:
    body = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


def _parse_ndjson(blob) -> list[dict]:
    """Parse newline-delimited JSON-RPC responses."""
    if isinstance(blob, bytes):
        text = blob.decode("utf-8")
    else:
        text = blob
    return [json.loads(ln) for ln in text.splitlines() if ln.strip()]


# --------------------------------------------------------------------------- #
def _selftest() -> int:
    """Simulate the Cursor handshake end-to-end; parse NDJSON responses."""
    import io
    reqs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-03-26", "capabilities": {}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "resources/list"},
        {"jsonrpc": "2.0", "id": 4, "method": "prompts/list"},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
         "params": {"name": "search_docs", "arguments": {"query": "scheduler set_timesteps step", "k": 2}}},
        {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
         "params": {"name": "search_docs",
                    "arguments": json.dumps({"query": "SchedulerMixin", "k": 1})}},
    ]
    # Reader still accepts Content-Length; writer emits NDJSON.
    stdin = io.BytesIO(b"".join(_frame(r) for r in reqs))
    stdout = io.StringIO()
    serve(stdin, stdout)
    raw = stdout.getvalue()
    assert "Content-Length" not in raw, raw
    messages = _parse_ndjson(raw)
    assert messages[0]["result"]["serverInfo"]["name"] == "diffusers-docs", "initialize failed"
    assert messages[0]["result"]["protocolVersion"] == "2025-03-26", "protocol negotiate failed"
    assert messages[1]["result"]["tools"][0]["name"] == "search_docs", "tools/list failed"
    assert messages[2]["result"]["resources"] == [], "resources/list should be empty, not an error"
    assert messages[3]["result"]["prompts"] == [], "prompts/list should be empty, not an error"
    assert "content" in messages[4]["result"], "tools/call failed"
    assert "content" in messages[5]["result"], "tools/call JSON-string arguments failed"
    print("MCP self-test OK: initialize -> list -> search_docs (NDJSON).")
    print("  tools/call returned:\n   ",
          messages[4]["result"]["content"][0]["text"].replace("\n", "\n    ")[:400])
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
