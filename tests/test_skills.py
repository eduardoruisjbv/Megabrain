"""Exercise real filesystem ownership and rollback, without changing the user's home."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest import mock


SPEC = importlib.util.spec_from_file_location("megabrain_skills", Path(__file__).resolve().parents[1] / "lib/skills.py")
skills = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(skills)


class SkillsTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / "user"
        self.state = self.root / "state"
        self.home.mkdir()
        self.installer = skills.Installer(self.home, self.state, ["codex", "claude"])
        self.source = self.root / "upstream"
        directory = self.source / "skills/security-audit"
        directory.mkdir(parents=True)
        (directory / "SKILL.md").write_text("---\nname: security-audit\ndescription: Review security when asked.\n---\n\nOriginal content.\n")
        (directory / "report-schema.json").write_text('{"type":"object"}')
        (self.source / "LICENSE").write_text("Test upstream license")

    def test_collection_installs_complete_skill_and_all_client_links(self):
        result = self.installer.install_collection("security-audit", self.source)
        self.assertEqual(result["created"], 1)
        for base in [".codex/skills", ".agents/skills", ".claude/skills"]:
            link = self.home / base / "security-audit"
            self.assertTrue(link.is_symlink())
            self.assertEqual((link / "report-schema.json").read_text(), '{"type":"object"}')
            self.assertEqual((link / "LICENSE.upstream").read_text(), "Test upstream license")
        self.installer.uninstall("security-audit")
        self.assertFalse(self.installer.owned("security-audit"))
        self.assertFalse((self.home / ".codex/skills/security-audit").is_symlink())

    def test_preexisting_skills_are_never_overwritten_or_owned(self):
        for base in [".agents/skills", ".claude/skills"]:
            directory = self.home / base / "security-audit"
            directory.mkdir(parents=True)
            (directory / "SKILL.md").write_text("User's existing skill")
        self.assertEqual(self.installer.install_collection("security-audit", self.source)["preexisting"], 1)
        self.assertFalse(self.installer.owned("security-audit"))
        self.installer.uninstall("security-audit")
        self.assertEqual((self.home / ".agents/skills/security-audit/SKILL.md").read_text(), "User's existing skill")

    def test_rerun_keeps_ownership_and_modified_skill_data(self):
        self.installer.install_collection("security-audit", self.source)
        reloaded = skills.Installer(self.home, self.state, ["codex", "claude"])
        self.assertEqual(reloaded.install_collection("security-audit", self.source)["created"], 0)
        target = self.home / ".codex/skills/security-audit/SKILL.md"
        actual = target.resolve()
        target.write_text(target.read_text() + "User changes\n")
        result = reloaded.uninstall("security-audit")
        self.assertEqual(result["kept_modified"], 1)
        self.assertTrue(actual.exists())
        self.assertIn("User changes", actual.read_text())

    def test_changed_user_link_is_preserved(self):
        self.installer.install_collection("security-audit", self.source)
        link = self.home / ".claude/skills/security-audit"
        link.unlink()
        link.symlink_to(self.source, target_is_directory=True)
        self.installer.uninstall("security-audit")
        self.assertEqual(link.resolve(), self.source)

    def test_auto_selection_round_trip_preserves_existing_config(self):
        instructions = self.home / ".codex/AGENTS.md"
        instructions.parent.mkdir()
        instructions.write_text("Existing instructions\n")
        settings_path = self.home / ".claude/settings.json"
        settings_path.parent.mkdir()
        settings = {"language": "portuguese", "permissions": {"deny": ["Bash(sudo *)"]},
                    "skillOverrides": {"my-skill": "user-invocable-only"}}
        original = json.dumps(settings) + "\n"
        settings_path.write_text(original)
        metadata = self.home / ".codex/skills/my-skill/agents/openai.yaml"
        metadata.parent.mkdir(parents=True)
        metadata.write_text("policy:\n  allow_implicit_invocation: false\n")
        with mock.patch.object(self.installer, "skill_roots", return_value=[self.home / ".codex/skills"]):
            self.installer.install_auto()
            self.installer.install_auto()
        self.assertEqual(instructions.read_text().count(skills.AUTO_BEGIN), 1)
        current = json.loads(settings_path.read_text())
        self.assertEqual(current["permissions"], settings["permissions"])
        self.assertEqual(current["skillOverrides"]["my-skill"], "on")
        self.assertIn("allow_implicit_invocation: true", metadata.read_text())
        self.installer.uninstall("skills-auto")
        self.assertEqual(instructions.read_text(), "Existing instructions\n")
        self.assertEqual(settings_path.read_text(), original)
        self.assertIn("allow_implicit_invocation: false", metadata.read_text())

    def test_auto_cleanup_keeps_later_user_edits(self):
        with mock.patch.object(self.installer, "skill_roots", return_value=[]):
            self.installer.install_auto()
        instructions = self.home / ".codex/AGENTS.md"
        instructions.write_text(instructions.read_text() + "Later user instruction\n")
        settings = self.home / ".claude/settings.json"
        current = json.loads(settings.read_text())
        current["language"] = "pt"
        settings.write_text(json.dumps(current))
        result = self.installer.uninstall("skills-auto")
        self.assertIn("Later user instruction", instructions.read_text())
        self.assertNotIn(skills.AUTO_BEGIN, instructions.read_text())
        self.assertEqual(json.loads(settings.read_text())["language"], "pt")
        self.assertEqual(result["kept_modified"], 1)

    def test_headerless_and_long_metadata_keep_upstream_content(self):
        p = self.root / "offensive-example/SKILL.md"
        p.parent.mkdir()
        body = "# Example\n\n## Description\n" + "Long reference sentence. " * 80 + "\n\n## Instructions\nOriginal instructions.\n"
        p.write_text(body)
        skills.normalize_skill(p)
        text = p.read_text()
        self.assertTrue(text.startswith("---\nname: offensive-example\n"))
        description_line = next(line for line in text.splitlines() if line.startswith("description:"))
        description = json.loads(description_line.split(":", 1)[1])
        self.assertLessEqual(len(description), 1024)
        self.assertIn(body, text)
        self.assertIn("Original instructions.", text)

    def test_failed_normalization_does_not_claim_or_leave_destination(self):
        (self.source / "skills/security-audit/SKILL.md").write_text("Invalid upstream format")
        with self.assertRaises(ValueError):
            self.installer.install_collection("security-audit", self.source)
        self.assertFalse((self.state / "skill-files/security-audit/security-audit").exists())
        self.assertFalse(self.installer.owned("security-audit"))

    def test_other_agents_do_not_receive_claude_or_codex_configuration(self):
        installer = skills.Installer(self.home, self.state, ["gemini"])
        self.assertEqual(installer.install_collection("security-audit", self.source)["created"], 0)
        with mock.patch.object(installer, "skill_roots", return_value=[]):
            installer.install_auto()
        self.assertFalse((self.home / ".codex").exists())
        self.assertFalse((self.home / ".claude").exists())

    def test_auto_edits_inside_owned_skill_do_not_look_like_user_changes(self):
        source = self.source / "skills/security-audit/SKILL.md"
        source.write_text(source.read_text().replace("description:", "disable-model-invocation: true\ndescription:"))
        self.installer.install_collection("security-audit", self.source)
        with mock.patch.object(self.installer, "skill_roots", return_value=[self.home / ".codex/skills"]):
            self.installer.install_auto()
        self.installer.uninstall("skills-auto")
        result = self.installer.uninstall("security-audit")
        self.assertEqual(result["kept_modified"], 0)
        self.assertFalse(self.installer.data["entries"])

    def test_download_rejects_archive_traversal_and_symlinks(self):
        for filename, mode in [("../outside", 0), ("source/link", 0o120777 << 16)]:
            payload = io.BytesIO()
            with zipfile.ZipFile(payload, "w") as archive:
                item = zipfile.ZipInfo(filename)
                item.external_attr = mode
                archive.writestr(item, "untrusted")
            with mock.patch.object(skills.urllib.request, "urlopen", return_value=io.BytesIO(payload.getvalue())):
                with self.assertRaisesRegex(ValueError, "Unsafe archive"):
                    skills.download_collection("security-audit", self.root / "extract")
        self.assertFalse((self.root / "outside").exists())


if __name__ == "__main__":
    unittest.main()
