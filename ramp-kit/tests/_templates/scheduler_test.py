"""TEMPLATE — copy to tests/schedulers/test_scheduling_<snake>.py and set the
two constants below. Runs with zero installs (structural contract) and adds a
numeric determinism check when torch is available.

See examples/correct_scheduler + tests/schedulers/test_scheduling_ddpm_lite.py
for a filled-in example.
"""
import ast
import importlib.util
import unittest
from pathlib import Path

# ---- edit these two for your scheduler -------------------------------------
TARGET = Path(__file__).resolve().parents[2] / "src" / "diffusers" / "schedulers" / "scheduling_CHANGE_ME.py"
CLASS = "ChangeMeScheduler"
# ----------------------------------------------------------------------------


def _class_node():
    for node in ast.walk(ast.parse(TARGET.read_text())):
        if isinstance(node, ast.ClassDef) and node.name == CLASS:
            return node
    raise AssertionError(f"{CLASS} not found in {TARGET}")


class TestSchedulerContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = _class_node()

    def test_inherits_required_mixins(self):
        bases = {getattr(b, "id", getattr(b, "attr", "")) for b in self.node.bases}
        self.assertIn("SchedulerMixin", bases)
        self.assertIn("ConfigMixin", bases)

    def test_has_contract_methods(self):
        methods = {n.name for n in self.node.body if isinstance(n, ast.FunctionDef)}
        self.assertIn("step", methods)
        self.assertIn("set_timesteps", methods)


class TestSchedulerNumerics(unittest.TestCase):
    def setUp(self):
        if importlib.util.find_spec("torch") is None:
            self.skipTest("torch not installed")

    def test_same_seed_same_output(self):
        import torch
        spec = importlib.util.spec_from_file_location(CLASS, TARGET)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sched = getattr(mod, CLASS)()
        sched.set_timesteps(10)
        sample = torch.zeros(1, 3, 8, 8)
        mo = torch.ones_like(sample)
        a = sched.step(mo, 1, sample, generator=torch.Generator().manual_seed(0)).prev_sample
        b = sched.step(mo, 1, sample, generator=torch.Generator().manual_seed(0)).prev_sample
        self.assertTrue(torch.equal(a, b))


if __name__ == "__main__":
    unittest.main()
