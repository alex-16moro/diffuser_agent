#!/usr/bin/env python3
"""Append a harmless demo rule to conventions/rules.yaml (used by `make demo-maintain`).

It appends a valid warn rule whose regex never matches real code, so the repo
stays green. `make demo-maintain` restores the file afterwards via git checkout.
This exists to DEMONSTRATE, live, that one registry edit propagates to every
audience surface (requirement #4).
"""
from pathlib import Path

RULES = Path(__file__).resolve().parent.parent / "conventions" / "rules.yaml"

DEMO_RULE = '''
  - id: DEMO001
    component: any
    source_type: customer
    title: "DEMO: added live to prove one-edit propagation"
    applies_to: ["src/diffusers/**"]
    severity: warn
    check: regex
    params:
      pattern: "ZZZ_DEMO_NEVER_MATCH_ZZZ"
    rationale: "Live-added rule; demonstrates registry -> all surfaces regeneration."
    source: "demo"
    agent_hint: "n/a"
    review_prompt: "n/a (demo rule)"
    dod: "n/a"
'''

text = RULES.read_text()
if "DEMO001" not in text:
    RULES.write_text(text.rstrip() + "\n" + DEMO_RULE)
    print("  added DEMO001 to conventions/rules.yaml")
else:
    print("  DEMO001 already present")
