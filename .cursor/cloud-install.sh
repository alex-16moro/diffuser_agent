#!/usr/bin/env bash
# Cloud Agent snapshot bootstrap (idempotent).
# Torch stays out of requirements.txt so local `make check` stays pyyaml-only.
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pip install --user -r requirements.txt
python3 -m pip install --user --index-url https://download.pytorch.org/whl/cpu torch
python3 -m pip install --user diffusers
bash "$ROOT/.cursor/install-docs-mcp.sh"
python3 "$ROOT/tools/docs_mcp_server.py" --selftest
python3 - <<'PY'
import torch
import diffusers

print("torch", torch.__version__, "cuda", torch.cuda.is_available())
print("diffusers", diffusers.__version__)
PY
test -x "${HOME}/.local/bin/diffusers-docs-mcp"
echo "shim: ${HOME}/.local/bin/diffusers-docs-mcp"
echo "cloud-install: ok"
