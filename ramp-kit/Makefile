# diffusers Ramp Kit — one entry point for every audience.
# `make help` lists targets. Everything here also runs standalone (see README).

.PHONY: help build check check-json test mcp demo demo-maintain clean

help:
	@echo "diffusers Ramp Kit"
	@echo "  make build      Regenerate all audience surfaces from conventions/rules.yaml"
	@echo "  make check      Run the convention gate on the whole repo (sets exit code)"
	@echo "  make check-json Same, machine-readable (CI / dashboards)"
	@echo "  make test       Run the contract tests (zero third-party installs needed)"
	@echo "  make mcp        Self-test the diffusers-docs MCP server (Cursor handshake)"
	@echo "  make demo       The 90-second live demo: catch bad, pass good, MCP, tests"
	@echo "  make demo-maintain  Prove req #4: add a rule, rebuild, watch it propagate"
	@echo "  make clean      Remove generated projections"

build:
	python tools/build_projections.py

check:
	python tools/convention_check.py --all

check-json:
	python tools/convention_check.py --all --json

test:
	python -m unittest discover -s tests -t . -v

mcp:
	python tools/docs_mcp_server.py --selftest

# The live-demo sequence: gate catches the from-memory scheduler (nonzero exit,
# shown), then passes the scaffolded one, then the MCP grounds an answer, then
# the contract tests are green.
demo:
	@echo "\n========== 1. A new engineer's first-cut scheduler =========="
	-python tools/convention_check.py examples/candidate_scheduler
	@echo "\n========== 2. The scaffolded, convention-correct version =========="
	python tools/convention_check.py examples/scaffolded_scheduler
	@echo "\n========== 3. Grounded doc-search via the MCP server =========="
	python tools/docs_mcp_server.py --selftest
	@echo "\n========== 4. Contract tests (zero install) =========="
	python -m unittest discover -s tests -t . -v

# Requirement #4 made visible: add a rule, rebuild, show EVERY surface changed,
# then restore. This is the "what happens when you're gone" answer, live.
demo-maintain:
	@echo "Adding a demo rule to conventions/rules.yaml ..."
	@python tools/_demo_add_rule.py
	@echo "\nRegenerating all surfaces from the one edit ..."
	@python tools/build_projections.py >/dev/null
	@echo "\nSurfaces that changed from a SINGLE registry edit:"
	@git status --short .cursor AGENTS.md projections conventions/rules.yaml || true
	@echo "\nRestoring original state ..."
	@git checkout -- conventions/rules.yaml .cursor AGENTS.md projections 2>/dev/null || true
	@python tools/build_projections.py >/dev/null
	@echo "Done. One edit -> agent rules + AGENTS.md + PM DoD + QA + CI all updated."

clean:
	rm -f AGENTS.md .cursor/rules/*.mdc
	rm -rf projections/pm projections/qa projections/devops
	@echo "Removed generated files. Run 'make build' to regenerate."
