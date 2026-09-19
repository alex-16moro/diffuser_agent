#!/usr/bin/env bash
# Put `diffusers-docs-mcp` on PATH so Cloud Agent dashboard stdio can spawn
# the server without ${workspaceFolder} or a relative script path.
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
echo "docs MCP launcher: $SRC"
echo "PATH command: ${HOME}/.local/bin/diffusers-docs-mcp"
