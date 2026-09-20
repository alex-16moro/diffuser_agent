"""Tests for kit wiring: MCP framing, afterFileEdit hook, TEST001 mentions."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from convention_check import check_file, load_rules  # noqa: E402


class TestLibraryPaths(unittest.TestCase):
    def test_kit_standin_or_adjacent_fork(self):
        from library_paths import KIT_ROOT, resolve_docs_root, resolve_library_root

        lib = resolve_library_root()
        sibling = (KIT_ROOT.parent / "diffusers").resolve()
        if (sibling / "docs" / "source" / "en").is_dir():
            self.assertEqual(lib, sibling)
            docs, provenance = resolve_docs_root()
            self.assertIn("diffusers checkout", provenance)
        else:
            self.assertEqual(lib, KIT_ROOT)
            docs, provenance = resolve_docs_root()
            self.assertIn("bundled snapshot", provenance)
            self.assertTrue(docs.exists())

    def test_env_docs_root_wins(self):
        from library_paths import resolve_docs_root

        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "en"
            fake.mkdir()
            (fake / "x.md").write_text("# Hello\n")
            proc = subprocess.run(
                [sys.executable, "-c",
                 "from library_paths import resolve_docs_root; p,s=resolve_docs_root(); print(p); print(s)"],
                cwd=ROOT,
                env={**dict(**{k: v for k, v in __import__("os").environ.items()}),
                     "DIFFUSERS_DOCS_ROOT": str(fake),
                     "PYTHONPATH": str(ROOT / "tools")},
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(str(fake), proc.stdout)
        self.assertIn("configured checkout", proc.stdout)


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


class TestOverlayMcpDefaults(unittest.TestCase):
    def test_overlay_mcp_json_is_empty(self):
        cfg = json.loads((ROOT / "overlay" / "mcp.json").read_text())
        self.assertEqual(cfg.get("mcpServers"), {})

    def test_overlay_mcp_optional_lists_opt_in_servers(self):
        raw = (ROOT / "overlay" / "mcp.optional.json").read_text()
        self.assertNotIn("${workspaceFolder}", raw)
        cfg = json.loads(raw)
        servers = cfg["mcpServers"]
        self.assertIn("diffusers-docs", servers)
        self.assertIn("huggingface", servers)
        stdio = servers["diffusers-docs"]
        self.assertEqual(stdio.get("type"), "stdio")
        self.assertEqual(stdio["command"], "python3")
        self.assertEqual(stdio["args"], ["-u", "/workspace/.cursor/mcp-diffusers-docs.py"])
        self.assertEqual(servers["huggingface"].get("url"), "https://huggingface.co/mcp")

    def test_attach_copies_empty_default_and_optional(self):
        src = (ROOT / "tools" / "attach_library.py").read_text()
        self.assertIn('shutil.copy2(overlay / "mcp.json", cursor / "mcp.json")', src)
        self.assertIn(
            'shutil.copy2(overlay / "mcp.optional.json", cursor / "mcp.optional.json")',
            src,
        )


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


class TestTest002Adequacy(unittest.TestCase):
    def test_zero_assertion_function_is_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            layout = Path(td) / "examples" / "foo"
            layout.mkdir(parents=True)
            target = layout / "scheduling_weak.py"
            target.write_text(
                "class WeakScheduler:\n    def step(self): ...\n    def set_timesteps(self): ...\n"
            )
            tests = Path(td) / "examples" / "tests"
            tests.mkdir(parents=True)
            (tests / "test_scheduling_weak.py").write_text(
                "import unittest\n"
                "class T(unittest.TestCase):\n"
                "    def test_set_timesteps_and_step(self):\n"
                "        pass  # mentions set_timesteps and step; zero assertions\n"
            )
            findings = check_file(target, load_rules())
            t002 = [f for f in findings if f.rule_id == "TEST002"]
            self.assertTrue(t002, findings)
            self.assertTrue(
                any("zero assertions" in f.message for f in t002),
                t002,
            )

    def test_scaffolded_example_is_clean(self):
        sched = ROOT / "examples" / "scaffolded_scheduler" / "scheduling_ddpm_lite.py"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "convention_check.py"), str(sched)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("0 findings", proc.stdout)

    def test_scaffolded_test_file_is_clean(self):
        test = ROOT / "tests" / "schedulers" / "test_scheduling_ddpm_lite.py"
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "convention_check.py"), str(test)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


class TestOwnersAndProjections(unittest.TestCase):
    def test_every_rule_has_owner(self):
        import yaml

        data = yaml.safe_load((ROOT / "conventions" / "rules.yaml").read_text())
        allowed = {"dev", "architect", "qa", "pm", "devops"}
        missing = [r["id"] for r in data["rules"] if r.get("owner") not in allowed]
        self.assertEqual(missing, [])

    def test_projections_mention_owners(self):
        pm = (ROOT / "projections" / "pm" / "definition-of-done.md").read_text()
        qa = (ROOT / "projections" / "qa" / "review-checklist.md").read_text()
        devops = (ROOT / "projections" / "devops" / "ci-gate.md").read_text()
        self.assertIn("owner: `qa`", pm)
        self.assertIn("### `pm`", pm)
        self.assertIn("owner: qa", qa)
        self.assertIn("owner", devops)
        self.assertIn("Projection drift", devops)


class TestGrokbotSim(unittest.TestCase):
    CONTEXT = ROOT / "examples" / "change_context.example.json"

    def _gate_json(self, example_dir: str) -> str:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "convention_check.py"),
             "--json", str(ROOT / "examples" / example_dir)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertIn('"findings"', proc.stdout)
        return proc.stdout

    def _sim(self, role: str, gate_json: str | None = None, context: bool = True) -> str:
        cmd = [sys.executable, str(ROOT / "tools" / "grokbot_sim.py"), "--role", role]
        if context:
            cmd.extend(["--context", str(self.CONTEXT)])
        if gate_json is None:
            gate_json = self._gate_json("scaffolded_scheduler")
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            input=gate_json,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def _first_section(self, text: str) -> str:
        parts = text.split("## ")
        self.assertGreater(len(parts), 1, text)
        return parts[1]

    def test_qa_risk_briefing_from_sample_gate(self):
        out = self._sim("qa", self._gate_json("candidate_scheduler"), context=False)
        self.assertIn("SIMULATION", out)
        self.assertIn("RISK BRIEFING", out)
        self.assertIn("Test adequacy", out)
        self.assertIn("Does not gate", out)

    def test_devops_leads_with_ci_and_drift(self):
        out = self._sim("devops")
        lead = self._first_section(out)
        self.assertIn("Pipeline health", lead)
        self.assertIn("convention_gate", lead)
        self.assertIn("[ci]", lead)
        self.assertIn("[drift]", lead)
        self.assertIn("inherited_workflows", lead)
        self.assertNotIn("SCHED", lead)
        self.assertNotIn("TEST001", lead)

    def test_pm_leads_with_dod_merge_and_issue(self):
        out = self._sim("pm")
        lead = self._first_section(out)
        self.assertIn("DoD state", lead)
        self.assertIn("scaffolded", lead)
        self.assertIn("scaffold ≠ product-done", lead)
        self.assertIn("merge-eligible", lead)
        self.assertIn("issue:", lead)
        self.assertIn("milestone:", lead)
        self.assertIn("[issue]", lead)
        self.assertIn("[gate]", lead)

    def test_pm_and_devops_are_not_interchangeable(self):
        pm = self._sim("pm")
        devops = self._sim("devops")
        pm_lead = self._first_section(pm)
        devops_lead = self._first_section(devops)
        self.assertIn("inherited_workflows", devops_lead)
        self.assertNotIn("inherited_workflows", pm_lead)
        self.assertIn("milestone", pm_lead.lower())
        self.assertNotIn("milestone", devops_lead.lower())
        self.assertNotEqual(pm_lead, devops_lead)
        self.assertNotIn("Pipeline health", pm)
        self.assertNotIn("DoD state", devops)

    def test_qa_leads_with_test_adequacy_and_residual_math(self):
        out = self._sim("qa", self._gate_json("candidate_scheduler"))
        lead = self._first_section(out)
        self.assertIn("Test adequacy", lead)
        self.assertIn("TEST001", lead)
        self.assertIn("Residual math risk", out)
        self.assertIn("numerical method vs the paper", out.lower())

    def test_every_claim_line_is_tagged_and_cannot_see_is_nonempty(self):
        import re

        tag = re.compile(r"\[(gate|ci|issue|drift)\]")
        for role in ("pm", "qa", "devops"):
            out = self._sim(role)
            bullets = [ln for ln in out.splitlines() if ln.startswith("- ")]
            self.assertTrue(bullets, f"{role} produced no bullets")
            for ln in bullets:
                self.assertRegex(ln, tag, f"{role} untagged: {ln}")
            self.assertIn("## Cannot see", out)
            after = out.split("## Cannot see", 1)[1]
            cannot_bullets = [ln for ln in after.splitlines() if ln.startswith("- ")]
            self.assertTrue(cannot_bullets, f"{role} Cannot see is empty")

    def test_pm_does_not_invent_timelines(self):
        out = self._sim("pm").lower()
        for needle in ("story points", "eta:", "ship by", "velocity is"):
            self.assertNotIn(needle, out)

    def test_change_context_example_schema(self):
        data = json.loads(self.CONTEXT.read_text())
        self.assertIn("pr", data)
        for key in ("number", "title", "issue", "milestone", "labels", "draft"):
            self.assertIn(key, data["pr"], key)
        for key in ("convention_gate", "drift_check", "inherited_workflows"):
            self.assertIn(key, data["ci"], key)
        self.assertIn(data["state"], ("scaffolded", "gate-green", "tests-pass", "merge-eligible"))
        self.assertIn("EulerLite", data["pr"]["title"] + data["pr"]["issue"])


class TestGrokbotIphonePack(unittest.TestCase):
    def test_profiles_cover_three_roles_and_never_gate(self):
        text = (ROOT / "agents" / "grokbot-profiles.md").read_text()
        for needle in (
            "Ramp Kit QA",
            "Ramp Kit PM",
            "Ramp Kit DevOps",
            "never gate",
            "never merge",
            "Edit Profile",
            "git pull",
            "pull_request",
            "not merge",
            "agents/grokbot-qa.md",
        ):
            self.assertIn(needle, text)
        qa = (ROOT / "agents" / "grokbot-qa.md").read_text()
        pm = (ROOT / "agents" / "grokbot-pm.md").read_text()
        devops = (ROOT / "agents" / "grokbot-devops.md").read_text()
        self.assertIn("Residual math risk", qa)
        self.assertIn("DoD state", pm)
        self.assertIn("status-view", pm.lower())
        self.assertIn("CI/CD", devops)
        self.assertIn("Cannot see", qa)
        self.assertIn("Cannot see", pm)
        self.assertIn("Cannot see", devops)
        self.assertIn("[gate]", qa)
        self.assertIn("opened", qa.lower())
        self.assertIn("do not brief on merge", qa.lower())
        self.assertIn("do not brief on merge", pm.lower())
        self.assertIn("Optional: after merge", devops)
        self.assertIn("ramp-kit-overlay", devops)
        self.assertIn("do not copy it", devops.lower())
        self.assertNotIn("enable convention-gate.yml on the fork", devops.lower())
        self.assertIn("closed", devops.lower())
        for role in ("qa", "pm", "devops"):
            agent = ROOT / ".cursor" / "agents" / f"grokbot-{role}.md"
            self.assertTrue(agent.is_file(), agent)
            body = agent.read_text()
            self.assertIn("readonly: true", body)
            self.assertIn("never merge", body.lower())
            self.assertIn(f"agents/grokbot-{role}.md", body)

    def test_grokbot_pack_prints_profiles(self):
        proc = subprocess.run(
            ["make", "grokbot-pack"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Ramp Kit QA", proc.stdout)
        self.assertIn("git pull", proc.stdout)


class TestSchedulerContractVerify(unittest.TestCase):
    def test_passes_against_fork_or_skips_kit_standin(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "verify_scheduler_contract.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertTrue("OK" in proc.stdout or "SKIP" in proc.stdout)

    def test_reports_drift_when_required_method_renamed(self):
        from library_paths import resolve_library_root

        lib = resolve_library_root()
        src = lib / "src" / "diffusers" / "schedulers" / "scheduling_ddpm.py"
        euler = lib / "src" / "diffusers" / "schedulers" / "scheduling_euler_discrete.py"
        if not src.is_file() or not euler.is_file():
            self.skipTest("fork reference schedulers not attached")
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td)
            dest = fake / "src" / "diffusers" / "schedulers"
            dest.mkdir(parents=True)
            dest.joinpath("scheduling_ddpm.py").write_text(
                src.read_text(encoding="utf-8").replace("def set_timesteps", "def set_num_inference_steps", 1)
            )
            dest.joinpath("scheduling_euler_discrete.py").write_text(
                euler.read_text(encoding="utf-8")
            )
            proc = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "verify_scheduler_contract.py"),
                 "--library", str(fake)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0, proc.stdout)
            self.assertIn("DRIFT", proc.stderr)
            self.assertIn("set_timesteps", proc.stderr)


class TestProjectionDrift(unittest.TestCase):
    def test_hand_edit_then_rebuild_diff_is_red(self):
        mdc = ROOT / ".cursor" / "rules" / "00-conventions.mdc"
        original = mdc.read_text()

        def restore():
            mdc.write_text(original)
            subprocess.run(["git", "checkout", "--", str(mdc)], cwd=ROOT, check=False,
                           capture_output=True)

        self.addCleanup(restore)
        mdc.write_text(original + "\n<!-- hand-edit should fail drift -->\n")
        subprocess.run(["git", "add", "--", str(mdc)], cwd=ROOT, check=True, capture_output=True)
        try:
            subprocess.run(
                [sys.executable, str(ROOT / "tools" / "build_projections.py")],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            diff = subprocess.run(
                ["git", "diff", "--exit-code", "--", ".cursor/rules", ".cursor/agents", "AGENTS.md",
                 "projections", ".github/workflows", "agents"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(diff.returncode, 0, "hand-edited generated file must fail drift")
        finally:
            subprocess.run(["git", "reset", "HEAD", "--", str(mdc)], cwd=ROOT,
                           capture_output=True)
            subprocess.run(["git", "checkout", "--", str(mdc)], cwd=ROOT, capture_output=True)

    def test_rebuild_is_idempotent(self):
        paths = [
            ROOT / ".cursor" / "rules" / "00-conventions.mdc",
            ROOT / "AGENTS.md",
            ROOT / "projections" / "pm" / "definition-of-done.md",
            ROOT / "agents" / "grokbot-qa.md",
            ROOT / "agents" / "grokbot-profiles.md",
            ROOT / ".cursor" / "agents" / "grokbot-qa.md",
        ]
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_projections.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        before = {p: p.read_text() for p in paths if p.exists()}
        self.assertIn(ROOT / "agents" / "grokbot-qa.md", before)
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_projections.py")],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        after = {p: p.read_text() for p in paths if p.exists()}
        self.assertEqual(before, after)


class TestAttachEmptyMcp(unittest.TestCase):
    def test_attach_writes_empty_mcp_servers(self):
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "diffusers"
            (fake / "src" / "diffusers" / "schedulers").mkdir(parents=True)
            (fake / ".gitignore").write_text("# Cursor\n.cursor\n")
            proc = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "attach_library.py"),
                 "--target", str(fake)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            cfg = json.loads((fake / ".cursor" / "mcp.json").read_text())
            self.assertEqual(cfg.get("mcpServers"), {})
            self.assertTrue((fake / ".cursor" / "mcp.optional.json").is_file())
            self.assertNotIn("AGENTS.md", [p.name for p in fake.iterdir()])
            wf = (fake / ".github" / "workflows" / "ramp-kit-overlay.yml").read_text()
            self.assertIn("ramp-kit-overlay", wf)
            self.assertNotIn("convention_check.py --all", wf)
            self.assertIn("Never convention_check --all", wf)
            self.assertTrue((fake / ".github" / "scripts" / "overlay_pr_gate.py").is_file())

    def test_attach_does_not_delete_inherited_workflows(self):
        with tempfile.TemporaryDirectory() as td:
            fake = Path(td) / "diffusers"
            (fake / "src" / "diffusers" / "schedulers").mkdir(parents=True)
            inherited = fake / ".github" / "workflows" / "pr_tests.yml"
            inherited.parent.mkdir(parents=True)
            inherited.write_text("name: inherited\n")
            proc = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "attach_library.py"),
                 "--target", str(fake)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
            self.assertTrue(inherited.is_file())
            self.assertEqual(inherited.read_text(), "name: inherited\n")
            self.assertTrue((fake / ".github" / "workflows" / "ramp-kit-overlay.yml").is_file())


class TestOverlayPrGate(unittest.TestCase):
    def test_skips_when_no_relevant_files(self):
        env = {**os.environ, "OVERLAY_GATE_FILES": "README.md", "OVERLAY_KIT": str(ROOT)}
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "overlay_pr_gate.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("skip", proc.stdout.lower())

    def test_file_scoped_clean_and_refuses_all(self):
        target = ROOT / "examples" / "scaffolded_scheduler" / "scheduling_ddpm_lite.py"
        env = {
            **os.environ,
            "OVERLAY_GATE_FILES": str(target.relative_to(ROOT)),
            "OVERLAY_KIT": str(ROOT),
        }
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "overlay_pr_gate.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertIn("file-scoped", proc.stdout.lower())
        refuse = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "overlay_pr_gate.py"), "--all"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(refuse.returncode, 2)
        self.assertIn("refusing --all", refuse.stderr)

    def test_flags_candidate_scheduler(self):
        target = ROOT / "examples" / "candidate_scheduler" / "scheduling_my_sde.py"
        env = {
            **os.environ,
            "OVERLAY_GATE_FILES": str(target.relative_to(ROOT)),
            "OVERLAY_KIT": str(ROOT),
        }
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "overlay_pr_gate.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertGreater(proc.returncode, 0, proc.stdout + proc.stderr)


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
