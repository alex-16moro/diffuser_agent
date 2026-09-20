# diffusers Ramp Kit — one entry point for every audience.
# `make help` lists targets. Everything here also runs standalone (see README).

PYTHON ?= python3

.PHONY: help doctor build check check-json test mcp demo demo-contribute demo-contribute-clean demo-maintain grokbot grokbot-pack verify-contract drift attach clean

help:
	@echo "diffusers Ramp Kit"
	@echo "  make doctor     Pre-flight: python3, PyYAML, Cursor files present"
	@echo "  make build      Regenerate all audience surfaces from conventions/rules.yaml"
	@echo "  make check      Run the convention gate on the whole repo (sets exit code)"
	@echo "  make check-json Same, machine-readable (CI / dashboards)"
	@echo "  make test       Run the contract tests (zero third-party installs needed)"
	@echo "  make mcp        Optional docs CLI: docs_mcp_server.py --query set_timesteps"
	@echo "  make demo       Catch the bad scheduler, pass the good one, docs CLI, tests"
	@echo "  make demo-contribute  First-contribution journey (KEEP=1 leaves files)"
	@echo "  make demo-contribute-clean  Remove the EulerLite contribution files"
	@echo "  make demo-maintain  Prove req #4: add a rule, rebuild, watch it propagate"
	@echo "  make grokbot    Simulate a GrokBot role briefing from sample gate JSON (ROLE=qa)"
	@echo "  make grokbot-pack  Print paste-ready Grok Bot iPhone/desktop profiles"
	@echo "  make verify-contract  Re-check SCHED001-003 against fork reference source"
	@echo "  make drift      Rebuild projections and fail if generated files were hand-edited"
	@echo "  make attach     Copy overlay Cursor files into a diffusers checkout (TARGET=../diffusers)"
	@echo "  make clean      Remove generated projections"

doctor:
	@command -v $(PYTHON) >/dev/null || (echo "Need python3 on PATH"; exit 1)
	@$(PYTHON) -c "import yaml" 2>/dev/null || (echo "Need PyYAML: pip install -r requirements.txt"; exit 1)
	@test -f .cursor/hooks.json && test -f .cursor/mcp.json && test -f .cursor/commands/scaffold.md && test -f .cursorignore \
		&& test ! -e .cursor/mcp-diffusers-docs.py && test ! -e .cursor/mcp-diffusers-docs.sh \
		&& test ! -e .cursor/install-docs-mcp.sh && test ! -e overlay/mcp.optional.json \
		&& test -f .cursor/commands/search-docs.md && test -f .cursor/skills/search-docs/SKILL.md \
		|| (echo "Missing Cursor wiring or leftover docs-MCP launchers still present"; exit 1)
	@$(PYTHON) -c "import json, pathlib; c=json.loads(pathlib.Path('.cursor/mcp.json').read_text()); assert c.get('mcpServers')=={}, c" \
		|| (echo ".cursor/mcp.json must be {\"mcpServers\":{}}"; exit 1)
	@test -f tools/attach_library.py && test -f overlay/OVERLAY.md && test -f overlay/mcp.json \
		|| (echo "Missing overlay attach tooling"; exit 1)
	@$(PYTHON) -c "import json, pathlib; c=json.loads(pathlib.Path('overlay/mcp.json').read_text()); assert c.get('mcpServers')=={}, c" \
		|| (echo "overlay/mcp.json must be {\"mcpServers\":{}}"; exit 1)
	@$(PYTHON) -c "import json, pathlib; e=json.loads(pathlib.Path('.cursor/environment.json').read_text()); assert 'mcpServerAllowlist' not in e and 'start' not in e, e" \
		|| (echo "kit environment.json must not allowlist or start a docs MCP"; exit 1)
	@$(PYTHON) -c "import json, pathlib; e=json.loads(pathlib.Path('overlay/environment.json').read_text()); assert 'mcpServerAllowlist' not in e and 'start' not in e, e" \
		|| (echo "overlay environment.json must not allowlist or start a docs MCP"; exit 1)
	@$(PYTHON) tools/docs_mcp_server.py --query "set_timesteps" >/dev/null
	@test -f tools/grokbot_sim.py && test -f tools/verify_scheduler_contract.py \
		&& test -f agents/grokbot-profiles.md && test -f .cursor/agents/grokbot-qa.md \
		|| (echo "Missing GrokBot / contract-verify tooling"; exit 1)
	@echo "doctor OK: $(PYTHON) + PyYAML + empty mcpServers + docs CLI --query + overlay"

attach:
	$(PYTHON) tools/attach_library.py --target $(or $(TARGET),../diffusers)

build:
	$(PYTHON) tools/build_projections.py

check:
	$(PYTHON) tools/convention_check.py --all

check-json:
	$(PYTHON) tools/convention_check.py --all --json

grokbot:
	@$(PYTHON) tools/convention_check.py --json examples/candidate_scheduler > /tmp/ramp-kit-gate.json || true
	$(PYTHON) tools/grokbot_sim.py --role $(or $(ROLE),qa) --context examples/change_context.example.json /tmp/ramp-kit-gate.json

grokbot-pack:
	@test -f agents/grokbot-profiles.md || $(PYTHON) tools/build_projections.py
	@cat agents/grokbot-profiles.md

verify-contract:
	$(PYTHON) tools/verify_scheduler_contract.py $(if $(LIBRARY),--library $(LIBRARY),)

drift:
	$(PYTHON) tools/build_projections.py
	git diff --exit-code -- .cursor/rules .cursor/agents AGENTS.md projections .github/workflows \
		.github/PULL_REQUEST_TEMPLATE.md .github/ISSUE_TEMPLATE agents

test:
	$(PYTHON) -m unittest discover -s tests -t . -v

mcp:
	$(PYTHON) tools/docs_mcp_server.py --query "set_timesteps"

# The live-demo sequence: gate catches the from-memory scheduler (nonzero exit,
# shown), then passes the scaffolded one, then the optional docs CLI, then
# the contract tests are green.
demo:
	@echo "\n========== 1. A new engineer's first-cut scheduler =========="
	-$(PYTHON) tools/convention_check.py examples/candidate_scheduler
	@echo "\n========== 2. The scaffolded, convention-correct version =========="
	$(PYTHON) tools/convention_check.py examples/scaffolded_scheduler
	@echo "\n========== 3. Optional docs CLI fallback (--query) =========="
	$(PYTHON) tools/docs_mcp_server.py --query "set_timesteps"
	@echo "\n========== 4. Contract tests (zero install) =========="
	$(PYTHON) -m unittest discover -s tests -t . -v
	@echo "\n========== 5. GrokBot QA simulation (read-side, does not gate) =========="
	@$(PYTHON) tools/convention_check.py --json examples/candidate_scheduler > /tmp/ramp-kit-gate.json || true
	$(PYTHON) tools/grokbot_sim.py --role qa --context examples/change_context.example.json /tmp/ramp-kit-gate.json
	@echo "\n========== 6. Scheduler contract vs fork source =========="
	$(PYTHON) tools/verify_scheduler_contract.py

# Full contribution journey (plan → ground → scaffold → gate → test → CI).
# Default: create, prove, delete (safe rehearsal / CI).
# Live walkthrough: `make demo-contribute KEEP=1` then open the two files.
demo-contribute:
	$(PYTHON) tools/demo_contribute.py $(if $(KEEP),--keep,) $(if $(NAME),--name $(NAME),)

demo-contribute-clean:
	$(PYTHON) tools/demo_contribute.py --clean-only --name $(or $(NAME),EulerLite)

# Requirement #4 made visible: add a rule, rebuild, show EVERY surface changed,
# then restore. This is the "what happens when you're gone" answer, live.
demo-maintain:
	@echo "Adding a demo rule to conventions/rules.yaml ..."
	@$(PYTHON) tools/_demo_add_rule.py
	@echo "\nRegenerating all surfaces from the one edit ..."
	@$(PYTHON) tools/build_projections.py >/dev/null
	@echo "\nSurfaces that changed from a SINGLE registry edit:"
	@git status --short .cursor/rules .cursor/agents AGENTS.md projections conventions/rules.yaml \
		.github/workflows .github/PULL_REQUEST_TEMPLATE.md .github/ISSUE_TEMPLATE agents || true
	@echo "\nRestoring original state ..."
	@git checkout -- conventions/rules.yaml .cursor/rules AGENTS.md projections \
		.github/workflows .github/PULL_REQUEST_TEMPLATE.md .github/ISSUE_TEMPLATE
	@git checkout -- agents .cursor/agents 2>/dev/null || true
	@$(PYTHON) tools/build_projections.py >/dev/null
	@echo "Done. One edit -> agent rules + AGENTS.md + PM DoD + QA + CI all updated."

clean:
	rm -f AGENTS.md .cursor/rules/*.mdc
	rm -rf projections/pm projections/qa projections/devops
	@echo "Removed generated files. Run 'make build' to regenerate."
