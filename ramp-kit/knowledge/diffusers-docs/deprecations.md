<!--
Seed corpus excerpt: common API moves new engineers trip on. Mirrors the
DEPR001 map in conventions/rules.yaml — keep the two in sync when the library
moves an API. Source: diffusers changelog / module reorganisation history.
-->
# Import path moves

- `diffusers.models.unet_2d` moved to `diffusers.models.unets.unet_2d`.
- `diffusers.models.unet_2d_condition` moved to `diffusers.models.unets.unet_2d_condition`.
- `diffusers.models.cross_attention` moved to `diffusers.models.attention_processor`.

# Renamed / removed kwargs

- `predict_epsilon=True/False` was replaced by `prediction_type="epsilon"/"sample"`.
- `torch_dtype=` on from_pretrained is superseded by `dtype=`.

# Reproducibility

Use `randn_tensor(shape, generator=generator, device=..., dtype=...)` and thread
a `torch.Generator` through the call chain. Never call global RNG (torch.randn
without generator, np.random) inside library code — it makes outputs unseedable.
