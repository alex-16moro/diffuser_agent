# Stand-in scheduler tree

`/scaffold scheduler <Name>` writes `scheduling_<name>.py` here so the path
matches `huggingface/diffusers` (`src/diffusers/schedulers/`).

This directory is **not** a vendored copy of the library. The scaffolded
file imports `diffusers` at runtime; the convention gate only checks
structure. Pair every new file with `tests/schedulers/test_scheduling_<name>.py`.
