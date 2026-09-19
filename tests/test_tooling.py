"""Tests for kit wiring: MCP framing, afterFileEdit hook, TEST001 mentions."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from convention_check import check_file, load_rules  # noqa: E402


class TestMcpFraming(unittest.TestCase):
    def test_selftest_uses_content_length(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "docs_mcp_server.py"), "--selftest"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("Content-Length", proc.stdout)


class TestMcpLauncher(unittest.TestCase):
    def test_project_mcp_json_has_no_workspace_folder_var(self):
        raw = (ROOT / ".cursor" / "mcp.json").read_text()
        self.assertNotIn("${workspaceFolder}", raw)
        self.assertNotIn("${workspaceFolderBasename}", raw)
        cfg = json.loads(raw)
        server = cfg["mcpServers"]["diffusers-docs"]
        self.assertEqual(server.get("type"), "stdio")
        self.assertEqual(server["command"], "python3")
        self.assertEqual(server["args"], ["-u", ".cursor/mcp-diffusers-docs.py"])
        self.assertTrue((ROOT / ".cursor" / "mcp-diffusers-docs.py").is_file())
        self.assertTrue((ROOT / ".cursor" / "mcp-diffusers-docs.sh").is_file())
        self.assertTrue((ROOT / ".cursor" / "commands" / "search-docs.md").is_file())
        self.assertTrue((ROOT / ".cursor" / "skills" / "search-docs" / "SKILL.md").is_file())

    def test_launcher_serves_from_unrelated_cwd(self):
        """Cloud stdio has no cwd; the launcher must still find the server."""
        sys.path.insert(0, str(ROOT / "tools"))
        from docs_mcp_server import _frame  # noqa: WPS433

        reqs = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-03-26", "capabilities": {}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ]
        proc = subprocess.run(
            [sys.executable, "-u", str(ROOT / ".cursor" / "mcp-diffusers-docs.py")],
            cwd=tempfile.gettempdir(),
            input=b"".join(_frame(r) for r in reqs),
            capture_output=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        self.assertIn(b"search_docs", proc.stdout)
        self.assertNotIn(b"${workspaceFolder}", proc.stdout)


class TestAfterFileEditHook(unittest.TestCase):
    def test_hook_reports_findings_on_candidate(self):
        payload = json.dumps({
            "file_path": str(ROOT / "examples" / "candidate_scheduler" / "scheduling_my_sde.py"),
            "edits": [],
        })
        proc = subprocess.run(
            [sys.executable, str(ROOT / ".cursor" / "hooks" / "convention_gate.py")],
            cwd=ROOT,
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("SCHED001", proc.stderr)
        self.assertIn("DEPR001", proc.stderr)

    def test_hook_skips_non_python(self):
        payload = json.dumps({"file_path": str(ROOT / "README.md"), "edits": []})
        proc = subprocess.run(
            [sys.executable, str(ROOT / ".cursor" / "hooks" / "convention_gate.py")],
            cwd=ROOT,
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr.strip(), "")


class TestTest001Mentions(unittest.TestCase):
    def test_dummy_test_file_is_not_enough(self):
        with tempfile.TemporaryDirectory() as td:
            sched = Path(td) / "scheduling_dummy.py"
            sched.write_text(
                "class DummyScheduler:\n    def step(self): ...\n    def set_timesteps(self): ...\n"
            )
            test_dir = Path(td) / "tests"
            test_dir.mkdir()
            (test_dir / "test_scheduling_dummy.py").write_text("# empty dummy test\n")
            # Point the rule's search at this temp tree by using the candidate
            # next-to-file lookup: parent.parent / tests / test_{stem}.py
            # sched parent is td, parent.parent is tmp parent — that won't hit.
            # Instead copy into a nested layout matching the checker's fallback:
            layout = Path(td) / "examples" / "foo"
            layout.mkdir(parents=True)
            target = layout / "scheduling_dummy.py"
            target.write_text(sched.read_text())
            tests = Path(td) / "examples" / "tests"
            tests.mkdir(parents=True, exist_ok=True)
            (tests / "test_scheduling_dummy.py").write_text("# empty dummy test\n")
            findings = check_file(target, load_rules())
            ids = {f.rule_id for f in findings}
            self.assertIn("TEST001", ids)
            self.assertTrue(any("does not exercise" in f.message for f in findings if f.rule_id == "TEST001"))


class TestDemoContribute(unittest.TestCase):
    def test_create_gate_clean_then_remove(self):
        name = "ToolingProbe"
        stem = "scheduling_tooling_probe"
        impl = ROOT / "src" / "diffusers" / "schedulers" / f"{stem}.py"
        test = ROOT / "tests" / "schedulers" / f"test_{stem}.py"
        self.addCleanup(lambda: impl.exists() and impl.unlink())
        self.addCleanup(lambda: test.exists() and test.unlink())
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "demo_contribute.py"),
             "--name", name, "--skip-bad-example"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("0 findings", proc.stdout.lower() + proc.stderr.lower() or proc.stdout)
        self.assertFalse(impl.exists(), "default run must not leave contribution files")
        self.assertFalse(test.exists())


if __name__ == "__main__":
    unittest.main()
