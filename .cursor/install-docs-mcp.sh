#!/usr/bin/env bash
# Put `diffusers-docs-mcp` on PATH and copy the relative launcher into Cloud
# workspace roots so `python3 -u .cursor/mcp-diffusers-docs.py` resolves when
# stdio is spawned from /agent or /workspace (not the git repo).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/.cursor/mcp-diffusers-docs.py"
chmod +x "$SRC" "$ROOT/.cursor/mcp-diffusers-docs.sh" "$ROOT/.cursor/install-docs-mcp.sh"

write_shim() {
  local dest="$1"
  mkdir -p "$(dirname "$dest")"
  cat > "$dest" <<EOF
#!/usr/bin/env bash
exec python3 -u "$SRC" --serve "\$@"
EOF
  chmod +x "$dest"
}

copy_workspace_launcher() {
  local dest_dir="$1"
  mkdir -p "$dest_dir" 2>/dev/null || return 0
  cp "$SRC" "$dest_dir/mcp-diffusers-docs.py" 2>/dev/null || return 0
  chmod +x "$dest_dir/mcp-diffusers-docs.py" 2>/dev/null || true
}

write_shim "$HOME/.local/bin/diffusers-docs-mcp"
path_line='export PATH="$HOME/.local/bin:$PATH"'
for rc in "$HOME/.profile" "$HOME/.bashrc"; do
  if [ -f "$rc" ] && grep -q '\.local/bin' "$rc" 2>/dev/null; then
    continue
  fi
  echo "$path_line" >> "$rc"
done
if mkdir -p /usr/local/bin 2>/dev/null && [ -w /usr/local/bin ]; then
  write_shim /usr/local/bin/diffusers-docs-mcp || true
fi

for ws in /agent /workspace "${CURSOR_WORKSPACE:-}" "${CURSOR_PROJECT_DIR:-}"; do
  if [ -n "$ws" ] && [ -d "$ws" ]; then
    copy_workspace_launcher "$ws/.cursor" || true
  fi
done

echo "docs MCP launcher: $SRC"
echo "PATH command: ${HOME}/.local/bin/diffusers-docs-mcp"
echo "Cloud dropdown: diffusers-docs-mcp"
echo "  (or: python3 -u .cursor/mcp-diffusers-docs.py)"
