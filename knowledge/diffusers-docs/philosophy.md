<!--
Seed corpus for the doc-search MCP (curated excerpts, not the full docs).
Point DIFFUSERS_DOCS_ROOT at a real diffusers checkout's docs/source/en for
complete coverage. Source: https://huggingface.co/docs/diffusers/conceptual/philosophy
-->
# Single-file policy

Diffusers follows a single-file policy: almost all of the code of a certain
class is written in a single, self-contained file. This applies to pipelines and
schedulers, and (with UNet/legacy exceptions) to models. Prefer copy-pasted code
over hasty abstractions so contributors can read and tweak one file.

# Schedulers

Schedulers guide the denoising process for inference and define the noise
schedule for training. They are individual classes with loadable configuration
files and strongly follow the single-file policy. All schedulers live in
src/diffusers/schedulers and must stay self-contained — they are not allowed to
import from large util files.

Schedulers inherit from SchedulerMixin and ConfigMixin and can be swapped via
ConfigMixin.from_config. Every scheduler must define set_timesteps(...) (called
once before the denoising loop) and step(...) (called each iteration), and its
__init__ is registered to the config via @register_to_config.
