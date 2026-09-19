<!-- Root AGENTS.md — read natively by Cursor, Codex, Claude Code, and others. -->
<!-- GENERATED from conventions/rules.yaml by tools/build_projections.py. DO NOT EDIT. Run `make build`. -->

# Contributing to huggingface/diffusers (Ramp Kit)

This repo uses convention-as-code. The authoritative rules live in
`conventions/rules.yaml` and are enforced by `tools/convention_check.py`.
Before opening a PR, run `make check` and fix every blocking finding.
Ground your work with the `diffusers-docs` MCP tool rather than memory.

## Conventions

### Upstream conventions (what diffusers itself requires)
- **[MUST] SCHED001 Schedulers inherit SchedulerMixin and ConfigMixin** (scheduler) — Declare `class XScheduler(SchedulerMixin, ConfigMixin):`. (source: VERIFIED: scheduling_ddpm.py, scheduling_euler_discrete.py (class bases))
- **[MUST] SCHED002 Schedulers implement the step() / set_timesteps() contract** (scheduler) — Implement `set_timesteps(self, num_inference_steps, device=None)` and `step(self, model_output, timestep, sample, generator=None, return_dict=True) -> SchedulerOutput`. (source: VERIFIED: scheduling_ddpm.py + scheduling_euler_discrete.py (def set_timesteps / def step))
- **[MUST] SCHED003 Scheduler __init__ is decorated with @register_to_config** (scheduler) — Add `@register_to_config` directly above `def __init__`. (source: VERIFIED: scheduling_ddpm.py, scheduling_euler_discrete.py (@register_to_config on __init__))
- **[MUST] REPRO001 Randomness threads through a generator, never global RNG** (any) — Use `randn_tensor(shape, generator=generator, device=..., dtype=...)` and thread `generator` through the call chain. (source: review-rules.md (reproducibility); randn_tensor utility)
- **[MUST] DEVICE001 No hardcoded CUDA/device placement** (any) — Respect the module's existing device: `.to(sample.device)` or accept a `device` argument. (source: review-rules.md (device handling))
- **[MUST] DEPR001 No deprecated/moved import paths** (any) — Use the current import path shown in the check output. (source: diffusers module reorganisation (models -> models.unets, attention_processor))
- **[SHOULD] DEPR002 Avoid deprecated kwargs (verify per release)** (any) — Prefer the newer kwarg, but confirm against your pinned diffusers version. (source: diffusers changelog (predict_epsilon->prediction_type; torch_dtype->dtype))
- **[SHOULD] IMPORT001 Schedulers stay self-contained (no heavy util imports)** (scheduler) — Copy the small helper in-file with a `# Copied from` marker instead of importing deep internals. (source: conceptual/philosophy.md (schedulers self-contained))
- **[SHOULD] COPY001 # Copied from markers are well-formed** (any) — Format: `# Copied from diffusers.<module.path>.<Symbol> with A->B`. (source: conceptual/contribution.md (# Copied from mechanism))
- **[MUST] MUT001 No mutable default arguments** (any) — Default to None and initialise inside the body. (source: review-rules.md (mutable defaults across schedulers))
- **[SHOULD] LOG001 Library code logs, it does not print()** (any) — Use `logger = logging.get_logger(__name__)` and `logger.info(...)`. (source: conceptual/contribution.md (style); diffusers.utils.logging)
- **[SHOULD] DOC001 Public methods have docstrings** (any) — Add a Google-style docstring with Args/Returns. (source: conceptual/contribution.md (PR rule 10: docstrings))
- **[MUST] TEST001 New schedulers/models ship with a matching test file** (scheduler) — Generate a contract test from tests/_templates/scheduler_test.py that asserts set_timesteps and step. (source: conceptual/contribution.md (PR rule 9: high-coverage tests))

### Customer guardrails (what OUR org additionally requires)
- **[SHOULD] CUST001 No debugging leftovers committed** (any) — Remove breakpoint()/pdb before committing. (source: customer policy: ramp-kit team standards)

## Boundaries
Do not import or copy code from outside this repository. `.cursorignore`
marks paths that are off-limits as agent context.

## First task
Scaffold a correct first contribution: `/scaffold scheduler <Name>`. See `.cursor/commands/scaffold.md`.
