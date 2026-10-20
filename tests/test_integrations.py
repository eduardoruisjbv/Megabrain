import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from integrations import Manager, PLAYWRIGHT
import mac_agent
import mac_worker
import ui


class IntegrationsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.state = self.home / "state"
        self.calls = []
        self.servers = {"codex": [], "claude": {}}

    def runner(self, command, **kwargs):
        self.calls.append(command)
        agent = command[0]
        if command[1:3] == ["mcp", "list"]:
            return subprocess.CompletedProcess(command, 0, json.dumps(self.servers[agent]), "")
        if command[1:3] == ["mcp", "add"]:
            name = "firecrawl" if "firecrawl" in command else "playwright"
            if agent == "codex":
                self.servers[agent].append({"name": name, "transport": command[3:], "auth_status": "unsupported"})
            else:
                self.servers[agent][name] = {"command": command[3:]}
                (self.home / ".claude.json").write_text(json.dumps({"mcpServers": self.servers[agent], "other": True}))
        if command[1:3] == ["mcp", "remove"]:
            name = command[3]
            if agent == "codex":
                self.servers[agent] = [x for x in self.servers[agent] if x["name"] != name]
            else:
                self.servers[agent].pop(name)
                (self.home / ".claude.json").write_text(json.dumps({"mcpServers": self.servers[agent], "other": True}))
        return subprocess.CompletedProcess(command, 0, "", "")

    def manager(self):
        return Manager(self.home, self.state, ["codex", "claude"], runner=self.runner)

    def test_mcp_both_agents_rerun_and_conservative_uninstall(self):
        manager = self.manager()
        manager.install("firecrawl")
        self.assertEqual(len(manager.data["entries"]), 2)
        manager = self.manager()
        manager.install("firecrawl")
        self.assertEqual(sum(x[1:3] == ["mcp", "add"] for x in self.calls), 2)
        self.servers["codex"][0]["transport"] = ["user modification"]
        manager.uninstall("firecrawl")
        self.assertEqual(len(self.servers["codex"]), 1)
        self.assertEqual(self.servers["claude"], {})
        self.assertTrue(json.loads((self.home / ".claude.json").read_text())["other"])
        self.assertEqual(len(manager.data["entries"]), 1)

    def test_existing_mcp_is_not_owned_or_replaced(self):
        self.servers["codex"] = [{"name": "firecrawl", "enabled": False}]
        manager = self.manager()
        manager.agents = {"codex"}
        manager.install("firecrawl")
        self.assertFalse(manager.owned("firecrawl"))
        self.assertFalse(any(x[1:3] == ["mcp", "add"] for x in self.calls))

    def test_playwright_uses_pinned_isolated_browser_and_skips_preexisting_downloads(self):
        manager = self.manager()
        with patch.object(manager, "browser", return_value="/browser") as browser:
            manager.install("playwright")
            manager.install("playwright")
        browser.assert_called_once()
        adds = [x for x in self.calls if x[1:3] == ["mcp", "add"]]
        self.assertEqual(len(adds), 2)
        self.assertTrue(all(PLAYWRIGHT in x and "--headless" in x and "--isolated" in x and "/browser" in x for x in adds))

    def test_codex_available_plugin_is_not_treated_as_installed(self):
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, json.dumps({"installed": [], "available": [
                {"pluginId": "open-code-review-codex@open-code-review", "installed": False}]}), "")
        manager = Manager(self.home, self.state, ["codex"], runner=runner)
        self.assertIsNone(manager.probe({"kind": "plugin", "agent": "codex", "name": "open-code-review-codex@open-code-review"}))

    def test_downloaded_chromium_is_registered_by_executable_path(self):
        manager = self.manager()
        browser = self.state / "browsers/chromium-1234/chrome-linux64/chrome"
        browser.parent.mkdir(parents=True)
        browser.write_text("browser")
        with patch("integrations.shutil.which", return_value=None), patch("integrations.Path.is_file", return_value=False):
            executable = manager.browser()
        self.assertEqual(executable, str(browser))
        self.assertTrue(any("chromium" in x for x in self.calls))

    def test_mac_runtime_is_local_and_preserves_preexisting_command(self):
        command = self.home / ".local/bin/mac-agent"
        command.parent.mkdir(parents=True)
        command.write_text("existing user command")
        manager = self.manager()
        manager.install("mac-agent")
        self.assertEqual(self.calls, [])  # no SSH connection during installation
        self.assertTrue((self.state / "mac-runtime/mac_worker.py").is_file())
        self.assertTrue((self.home / ".claude/skills/mac-remoto/SKILL.md").is_file())
        manager.uninstall("mac-agent")
        self.assertEqual(command.read_text(), "existing user command")
        self.assertFalse((self.state / "mac-runtime").exists())

    def test_mac_runtime_unchanged_cleanup_and_modified_command_preserved(self):
        manager = self.manager()
        manager.install("mac-agent")
        command = self.home / ".local/bin/mac-agent"
        command.write_text(command.read_text() + "# later edit\n")
        manager.uninstall("mac-agent")
        self.assertTrue(command.exists())
        self.assertIn(str(command), manager.skills.owned("mac-agent"))


class RemoteTest(unittest.TestCase):
    def test_prompt_never_enters_shell_command(self):
        payload = {"action": "start", "prompt": "$(touch /bad); `whoami`\n'quoted'", "context": "explicit context"}
        with patch("mac_agent.subprocess.run", return_value=subprocess.CompletedProcess([], 0, '{"ok":true,"data":{"id":"job"}}', "")) as run:
            mac_agent.ssh_request({"host": "test-mac", "python": "/path with spaces/python"}, payload)
        args, kwargs = run.call_args
        self.assertNotIn(payload["prompt"], " ".join(args[0]))
        self.assertEqual(json.loads(kwargs["input"]), payload)
        self.assertIn("BatchMode=yes", args[0])
        self.assertNotIn("StrictHostKeyChecking=no", args[0])

    def test_invalid_host_and_job_ids_rejected(self):
        for host in ["-oProxyCommand=bad", "host; command", "$(bad)"]:
            with self.assertRaises(ValueError):
                mac_agent.ssh_request({"host": host}, {})
        for job in ["../../etc", "not-a-job", "/tmp/job"]:
            with self.assertRaises(ValueError):
                mac_worker.job_dir(job)

    def test_configure_does_not_connect_and_fetch_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "config.json"
            with patch("mac_agent.ssh_request") as request:
                mac_agent.main(["--config", str(config), "configure", "test-mac"])
                request.assert_not_called()
            self.assertEqual(config.stat().st_mode & 0o777, 0o600)
            output = Path(directory) / "export"
            output.mkdir()
            with patch("mac_agent.ssh_request", return_value={"result.md": "result"}):
                with self.assertRaises(FileExistsError):
                    mac_agent.main(["--config", str(config), "fetch", "job", "--output", str(output)])

    def test_worker_marks_agent_error_even_with_zero_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "events.jsonl").write_text(json.dumps({"type": "result", "session_id": "abc", "is_error": True, "result": "permission denied"}) + "\n")
            session, error = mac_worker.parse_events(path, "claude")
            self.assertEqual(session, "abc")
            self.assertEqual(error, "permission denied")

    def test_running_step_remains_visible_in_fixed_height_ui(self):
        state = ui.State("test")
        state.steps[-2].state = "running"
        output = ui.right_panel(state, state.t_start)
        self.assertEqual(len(output), ui.HEIGHT)
        self.assertIn("Vault", "\n".join(row[0] for row in output))


if __name__ == "__main__":
    unittest.main()
