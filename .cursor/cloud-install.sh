#!/usr/bin/env bash
# Cloud Agent snapshot bootstrap (idempotent).
# Torch stays out of requirements.txt so local `make check` stays pyyaml-only.
# No docs MCP server is installed or allowlisted.
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m pip install --user -r requirements.txt
python3 -m pip install --user --index-url https://download.pytorch.org/whl/cpu torch
python3 -m pip install --user diffusers
python3 "$ROOT/tools/docs_mcp_server.py" --query "set_timesteps" >/dev/null
python3 - <<'PY'
import torch
import diffusers

print("torch", torch.__version__, "cuda", torch.cuda.is_available())
print("diffusers", diffusers.__version__)
PY
echo "cloud-install: ok"
