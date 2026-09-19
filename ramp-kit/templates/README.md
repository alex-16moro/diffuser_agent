# Templates + how to add a component (without new machinery)

This directory holds the scaffold templates the `/scaffold <component> <Name>`
command copies from. The whole point of the kit's design is that **adding a new
component is a DATA change, not a code change** — you never add a new command,
a new rule dialect, or a new working mode.

## Add a component in 3 steps

Say you want to scaffold **models** as well as schedulers:

1. **Declare it** in `conventions/rules.yaml` under `meta.components`:

   ```yaml
   model:
     label: "Model"
     path: "src/diffusers/models/**/modeling_*.py"
     reference: "examples/correct_model/modeling_example.py"
     template: "templates/model/modeling_TEMPLATE.py"
   ```

2. **Add rules** tagged `component: model` (reuse existing `check:` types —
   `ast_class_bases`, `ast_required_methods`, `regex`, `deprecation_map`, …).
   Only add a NEW check function to `convention_check.py` if a genuinely new
   kind of check is needed; that is the rare exception, not the rule.

3. **Drop a template** at `templates/model/modeling_TEMPLATE.py`.

Then `make build` automatically:
- generates `.cursor/rules/10-model.mdc` (auto-attached to the model globs),
- lists the model rules in `AGENTS.md`, the PM DoD, the QA checklist, and CI,
- and `/scaffold model <Name>` works with no command change.

That is the scaling contract: **primitives are fixed; components are data.**
It keeps the system reliable as it grows instead of fragmenting into a bespoke
approach per task type.
