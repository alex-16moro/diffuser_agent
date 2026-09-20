# diffusers Ramp Kit — one entry point for every audience.
# `make help` lists targets. Everything here also runs standalone (see README).

PYTHON ?= python3

.PHONY: help doctor build check check-json test mcp demo demo-contribute demo-contribute-clean demo-maintain grokbot verify-contract drift attach clean

help:
	@echo "diffusers Ramp Kit"
	@echo "  make doctor     Pre-flight: python3, PyYAML, Cursor files present"
	@echo "  make build      Regenerate all audience surfaces from conventions/rules.yaml"
	@echo "  make check      Run the convention gate on the whole repo (sets exit code)"
	@echo "  make check-json Same, machine-readable (CI / dashboards)"
	@echo "  make test       Run the contract tests (zero third-party installs needed)"
	@echo "  make mcp        Self-test the diffusers-docs MCP server (Cursor handshake)"
	@echo "  make demo       Catch the bad scheduler, pass the good one, MCP, tests"
	@echo "  make demo-contribute  First-contribution journey (KEEP=1 leaves files)"
	@echo "  make demo-contribute-clean  Remove the EulerLite contribution files"
	@echo "  make demo-maintain  Prove req #4: add a rule, rebuild, watch it propagate"
	@echo "  make grokbot    Simulate a GrokBot role briefing from sample gate JSON (ROLE=qa)"
	@echo "  make verify-contract  Re-check SCHED001-003 against fork reference source"
	@echo "  make drift      Rebuild projections and fail if generated files were hand-edited"
	@echo "  make attach     Copy overlay Cursor files into a diffusers checkout (TARGET=../diffusers)"
	@echo "  make clean      Remove generated projections"

doctor:
	@command -v $(PYTHON) >/dev/null || (echo "Need python3 on PATH"; exit 1)
	@$(PYTHON) -c "import yaml" 2>/dev/null || (echo "Need PyYAML: pip install -r requirements.txt"; exit 1)
	@test -f .cursor/hooks.json && test -f .cursor/mcp.json && test -f .cursor/commands/scaffold.md && test -f .cursorignore \
		&& test -f .cursor/mcp-diffusers-docs.py && test -f .cursor/mcp-diffusers-docs.sh \
		&& test -f .cursor/commands/search-docs.md && test -f .cursor/skills/search-docs/SKILL.md \
		|| (echo "Missing Cursor wiring (hooks, mcp launcher, scaffold, search-docs, .cursorignore)"; exit 1)
	@! grep -q workspaceFolder .cursor/mcp.json || (echo "mcp.json must not use workspaceFolder vars (Cloud stdio does not expand them)"; exit 1)
	@test -f tools/attach_library.py && test -f overlay/OVERLAY.md \
		&& test -f overlay/mcp.json && test -f overlay/mcp.optional.json \
		|| (echo "Missing overlay attach tooling"; exit 1)
	@$(PYTHON) -c "import json, pathlib; c=json.loads(pathlib.Path('overlay/mcp.json').read_text()); assert c.get('mcpServers') == {}, c" \
		|| (echo "overlay/mcp.json must have empty mcpServers (Cloud default)"; exit 1)
	@$(PYTHON) -c "import json, pathlib; s=json.loads(pathlib.Path('overlay/mcp.optional.json').read_text())['mcpServers']; assert 'diffusers-docs' in s and 'huggingface' in s, s" \
		|| (echo "overlay/mcp.optional.json must list opt-in servers"; exit 1)
	@$(PYTHON) tools/docs_mcp_server.py --selftest >/dev/null
	@test -f tools/grokbot_sim.py && test -f tools/verify_scheduler_contract.py \
		|| (echo "Missing GrokBot / contract-verify tooling"; exit 1)
	@echo "doctor OK: $(PYTHON) + PyYAML + Cursor files + MCP self-test + overlay"

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
	$(PYTHON) tools/grokbot_sim.py --role $(or $(ROLE),qa) /tmp/ramp-kit-gate.json

verify-contract:
	$(PYTHON) tools/verify_scheduler_contract.py $(if $(LIBRARY),--library $(LIBRARY),)

drift:
	$(PYTHON) tools/build_projections.py
	git diff --exit-code -- .cursor/rules AGENTS.md projections .github/workflows \
		.github/PULL_REQUEST_TEMPLATE.md .github/ISSUE_TEMPLATE agents

test:
	$(PYTHON) -m unittest discover -s tests -t . -v

mcp:
	$(PYTHON) tools/docs_mcp_server.py --selftest

# The live-demo sequence: gate catches the from-memory scheduler (nonzero exit,
# shown), then passes the scaffolded one, then the MCP grounds an answer, then
# the contract tests are green.
demo:
	@echo "\n========== 1. A new engineer's first-cut scheduler =========="
	-$(PYTHON) tools/convention_check.py examples/candidate_scheduler
	@echo "\n========== 2. The scaffolded, convention-correct version =========="
	$(PYTHON) tools/convention_check.py examples/scaffolded_scheduler
	@echo "\n========== 3. Grounded doc-search via the MCP server =========="
	$(PYTHON) tools/docs_mcp_server.py --selftest
	@echo "\n========== 4. Contract tests (zero install) =========="
	$(PYTHON) -m unittest discover -s tests -t . -v
	@echo "\n========== 5. GrokBot QA simulation (read-side, does not gate) =========="
	@$(PYTHON) tools/convention_check.py --json examples/candidate_scheduler > /tmp/ramp-kit-gate.json || true
	$(PYTHON) tools/grokbot_sim.py --role qa /tmp/ramp-kit-gate.json
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
	@git status --short .cursor/rules AGENTS.md projections conventions/rules.yaml \
		.github/workflows .github/PULL_REQUEST_TEMPLATE.md .github/ISSUE_TEMPLATE agents || true
	@echo "\nRestoring original state ..."
	@git checkout -- conventions/rules.yaml .cursor/rules AGENTS.md projections \
		.github/workflows .github/PULL_REQUEST_TEMPLATE.md .github/ISSUE_TEMPLATE
	@git checkout -- agents 2>/dev/null || true
	@$(PYTHON) tools/build_projections.py >/dev/null
	@echo "Done. One edit -> agent rules + AGENTS.md + PM DoD + QA + CI all updated."

clean:
	rm -f AGENTS.md .cursor/rules/*.mdc
	rm -rf projections/pm projections/qa projections/devops
	@echo "Removed generated files. Run 'make build' to regenerate."
