"""Hermes config ownership, skill routing and runtime setup, without provider calls."""
import json
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from integrations import Manager
from skills import Installer, AUTO_BEGIN


class HermesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "home"
        self.home.mkdir()
        self.state = Path(self.temp.name) / "state"
        self.vault = Path(self.temp.name) / "vault with spaces"
        self.cli = self.home / "hermes"
        self.cli.write_text("existing Hermes launcher")
        self.config = {}
        self.calls = []
        self.patch = patch("integrations.shutil.which", side_effect=self.which)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def which(self, name):
        return str(self.cli) if name == "hermes" else None

    def runner(self, args, **kwargs):
        self.calls.append(args)
        self.assertEqual(kwargs["env"]["HERMES_HOME"], str(self.home / ".hermes"))
        if args == ["hermes", "--version"]:
            return subprocess.CompletedProcess(args, 0, "Hermes 0.22.4\n", "")
        if args[:3] == ["hermes", "config", "get"]:
            if args[3] not in self.config:
                return subprocess.CompletedProcess(args, 1, "Config key not set: " + args[3] + "\n", "")
            return subprocess.CompletedProcess(args, 0, json.dumps(self.config[args[3]], sort_keys=True), "")
        if args[:3] == ["hermes", "config", "set"]:
            self.config[args[3]] = json.loads(args[4])
        elif args[:3] == ["hermes", "config", "unset"]:
            del self.config[args[3]]
        return subprocess.CompletedProcess(args, 0, "", "")

    def manager(self):
        return Manager(self.home, self.state, ["hermes"], runner=self.runner, vault_dir=self.vault)

    def test_mcp_rerun_and_uninstall_preserve_other_keys_and_user_edits(self):
        self.config["provider"] = "user's provider"
        manager = self.manager()
        manager.install("firecrawl")
        manager.install("firecrawl")
        self.assertEqual(sum(args[:3] == ["hermes", "config", "set"] for args in self.calls), 1)
        self.assertEqual(self.config["mcp_servers.firecrawl"], {"url": "https://mcp.firecrawl.dev/v2/mcp"})
        self.config["mcp_servers.firecrawl"] = {"url": "user's endpoint", "enabled": False}
        self.manager().uninstall("firecrawl")
        self.assertEqual(self.config["provider"], "user's provider")
        self.assertEqual(self.config["mcp_servers.firecrawl"]["enabled"], False)
        self.assertTrue(self.manager().owned("firecrawl"))

    def test_unchanged_mcp_is_removed_without_removing_other_settings(self):
        self.config["provider"] = "keep"
        self.manager().install("firecrawl")
        self.manager().uninstall("firecrawl")
        self.assertEqual(self.config, {"provider": "keep"})

    def test_rtk_ownership_keeps_a_later_user_plugin_edit(self):
        manager = self.manager()
        plugin = self.home / ".hermes/plugins/rtk-rewrite"
        original_runner = manager.runner

        def runner(args, **kwargs):
            if args[0] == "rtk":
                plugin.mkdir(parents=True)
                (plugin / "plugin.yaml").write_text("owned plugin")
                self.config["plugins"] = ["rtk-rewrite"]
            return original_runner(args, **kwargs)

        manager.runner = runner
        manager.native("hermes", "hermes-rtk", "rtk-rewrite", [["rtk", "init"]], ["rtk", "remove"], "hermes")
        (plugin / "plugin.yaml").write_text("user plugin changes")
        self.manager().uninstall("hermes")
        self.assertEqual((plugin / "plugin.yaml").read_text(), "user plugin changes")
        self.assertNotIn(["rtk", "remove"], self.calls)

    def test_existing_mcp_even_disabled_is_never_replaced(self):
        self.config["mcp_servers.firecrawl"] = {"enabled": False}
        self.manager().install("firecrawl")
        self.assertFalse(self.manager().owned("firecrawl"))
        self.assertEqual(self.config["mcp_servers.firecrawl"], {"enabled": False})

    def test_config_read_error_fails_instead_of_overwriting(self):
        manager = self.manager()
        manager.runner = lambda args, **kwargs: subprocess.CompletedProcess(args, 1, "", "invalid YAML")
        with self.assertRaisesRegex(RuntimeError, "Cannot read Hermes"):
            manager.install("firecrawl")
        self.assertEqual(self.config, {})

    def test_existing_runtime_is_not_owned_and_vault_skill_is_hermes_only(self):
        manager = self.manager()
        manager.install("hermes")
        self.assertFalse(any(item["kind"] == "cli" for item in manager.data["entries"].values()))
        skill = self.home / ".hermes/skills/megabrain/SKILL.md"
        self.assertIn(str(self.vault), skill.read_text())
        self.assertFalse((self.home / ".claude").exists())
        self.assertFalse((self.home / ".codex").exists())
        self.assertFalse(any(args[:3] == ["hermes", "auth", "add"] for args in self.calls))
        manager.uninstall("hermes")
        self.assertTrue(self.cli.exists())
        self.assertFalse(skill.exists())

    def test_hermes_skill_install_and_auto_routing_preserve_identity(self):
        installer = Installer(self.home, self.state, ["hermes"])
        soul = self.home / ".hermes/SOUL.md"
        soul.parent.mkdir(parents=True)
        soul.write_text("User identity\n")
        source = self.home / "upstream/skills/security-audit/SKILL.md"
        source.parent.mkdir(parents=True)
        source.write_text("---\nname: security-audit\ndescription: Audit when asked.\n---\nGuidance\n")
        installer.install_collection("security-audit", self.home / "upstream")
        self.assertTrue((self.home / ".hermes/skills/security-audit").is_symlink())
        installer.install_auto()
        installer.install_auto()
        self.assertEqual(soul.read_text().count(AUTO_BEGIN), 1)
        installer.uninstall("skills-auto")
        self.assertEqual(soul.read_text(), "User identity\n")
        self.assertFalse((self.home / ".claude").exists())

    def test_categorized_builtin_skill_is_not_shadowed_by_flat_install(self):
        builtin = self.home / ".hermes/skills/security/security-audit/SKILL.md"
        builtin.parent.mkdir(parents=True)
        builtin.write_text("existing categorized skill")
        source = self.home / "upstream/skills/security-audit/SKILL.md"
        source.parent.mkdir(parents=True)
        source.write_text("---\nname: security-audit\ndescription: Audit when asked.\n---\nnew skill\n")
        installer = Installer(self.home, self.state, ["hermes"])
        result = installer.install_collection("security-audit", self.home / "upstream")
        self.assertEqual(result["preexisting"], 1)
        self.assertFalse((self.home / ".hermes/skills/security-audit").exists())
        self.assertEqual(builtin.read_text(), "existing categorized skill")

    def test_vault_path_updates_only_unchanged_generated_skill(self):
        self.manager().install("hermes")
        manager = self.manager()
        manager.vault_dir = self.vault / "new vault"
        manager.install("hermes")
        note = self.home / ".hermes/skills/megabrain/SKILL.md"
        self.assertIn(str(manager.vault_dir), note.read_text())
        note.write_text("User's own skill")
        manager = self.manager()
        manager.install("hermes")
        self.assertEqual(note.read_text(), "User's own skill")

    def test_new_runtime_uses_official_installer_and_no_full_data_removal(self):
        available = False
        original_runner = self.runner

        def runner(args, **kwargs):
            nonlocal available
            if args[0] == "bash":
                self.assertEqual(args[-1], "--non-interactive")
                self.assertEqual(Path(args[1]).read_text(), "official installer fixture")
                available = True
            return original_runner(args, **kwargs)

        manager = self.manager()
        manager.runner = runner
        with patch("integrations.shutil.which", side_effect=lambda name: str(self.cli) if name == "hermes" and available else None), \
                patch("integrations.urllib.request.urlopen", return_value=io.BytesIO(b"official installer fixture")) as download:
            manager.install("hermes")
            self.assertEqual(download.call_args[0][0], "https://hermes-agent.nousresearch.com/install.sh")
            self.assertFalse(self.config["auth.adopt_external_logins"])
            self.assertTrue(any(item["kind"] == "cli" for item in manager.data["entries"].values()))
            manager.uninstall("hermes")
        self.assertIn(["hermes", "uninstall", "--yes"], self.calls)
        self.assertFalse(any("--full" in args or "auth.json" in str(args) for args in self.calls))

    def test_dry_run_can_bootstrap_and_respects_explicit_agent_override(self):
        script = Path(__file__).resolve().parents[1] / "install.sh"
        env = dict(os.environ, HOME=str(self.home), MEGABRAIN_HOME=str(self.home / ".megabrain"))
        result = subprocess.run(["bash", str(script), "--dry-run", "--no-anim", "-y", "--only", "hermes"],
                                env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("official stable installer", result.stdout)
        result = subprocess.run(["bash", str(script), "--dry-run", "--no-anim", "-y", "--agents", "codex", "--only", "hermes"],
                                env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Hermes excluded by --agents", result.stdout)
        self.assertFalse((self.home / ".megabrain").exists())

    def test_custom_hermes_home_is_used_for_config_and_skills(self):
        profile = self.home / "custom profile"
        with patch.dict(os.environ, {"HERMES_HOME": str(profile)}):
            manager = self.manager()
            self.assertEqual(manager.skills.hermes_home, profile)
            calls = []

            def runner(args, **kwargs):
                calls.append(kwargs["env"]["HERMES_HOME"])
                return subprocess.CompletedProcess(args, 1, "Config key not set: " + args[3], "")

            manager.runner = runner
            self.assertIsNone(manager.hermes_config("mcp_servers.firecrawl"))
            self.assertEqual(calls, [str(profile)])

    def test_targeted_reinstall_retains_previously_configured_agents_and_ownership(self):
        script = (Path(__file__).resolve().parents[1] / "install.sh").read_text()
        functions = script[script.index("mf_get() {"):script.index('SKILL_COMPONENTS=')]
        self.state.mkdir()
        (self.state / "manifest.env").write_text('AGENTS="claude codex"\nMANAGED_rtk="1"\n')
        body = 'DRY=0\nMB_HOME="$1"\nMANIFEST="$MB_HOME/manifest.env"\n' + functions
        body += '\nmf_reset_keep_owned\nKEEP_OWNED=1\nmf_put AGENTS hermes\nmf_get AGENTS\n'
        result = subprocess.run(["bash", "-c", body, "test", str(self.state)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        self.assertEqual(set(result.stdout.split()), {"hermes", "claude", "codex"})
        self.assertIn('MANAGED_rtk="1"', (self.state / "manifest.env").read_text())


if __name__ == "__main__":
    unittest.main()
