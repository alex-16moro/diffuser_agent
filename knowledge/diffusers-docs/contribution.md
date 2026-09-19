<!--
Seed corpus excerpt. Source: https://huggingface.co/docs/diffusers/conceptual/contribution
-->
# Copied from mechanism

The `# Copied from` mechanism keeps duplicated blocks identical to their source.
Marking code with `# Copied from diffusers.<module.path>.<Symbol> with A->B`
forces it to match, and `make fix-copies` propagates changes. Use it instead of
importing deep internals when two files need the same helper.

# Tests

No quality testing = no merge. Add high-coverage tests for any new pipeline,
model, or scheduler. Slow tests are marked @slow and run nightly; keep the
default test suite fast and GPU-free. Run `make style` and `make quality`
before opening a PR.

# Coding with AI agents

The repository keeps AI-agent configuration in .ai/ (AGENTS.md, models.md,
pipelines.md, review-rules.md) and on-demand skills (model-integration,
self-review). `.ai/` is maintained by core maintainers; contributors should not
edit it. Self-review your diff against review-rules.md before opening a PR and
include the test commands you ran in the PR description.
