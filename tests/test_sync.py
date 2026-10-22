"""Vault mirror: curated sources, Graft cards and preserved vault edits, in a temporary home."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import sync_memories


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.home, self.vault, self.state = root / "home", root / "vault", root / "state"
        self.mirror = self.vault / "03-Recursos/IA"
        self.write(".claude/projects/-home-me/memory/MEMORY.md", "claude index")
        self.write(".codex/memories/MEMORY.md", "codex index")
        self.write(".codex/memories/rollout_summaries/one.md", "summary")
        self.write(".codex/memories/raw_memories.md", "raw")
        self.write(".codex/memories/graft/INDEX.md", "codex graph")
        self.write("graft/INDEX.md", "home graph")
        self.write("graft/cards/file.md", "card")
        self.write("graft/.cache/internal.md", "internal")
        self.vault.mkdir()

    def write(self, relative, text):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def sync(self):
        return sync_memories.sync(self.home, self.vault, self.state)

    def test_curated_sources_and_graft_cards_are_mirrored(self):
        self.sync()
        self.assertEqual((self.mirror / "Claude/-home-me/MEMORY.md").read_text(), "claude index")
        self.assertEqual((self.mirror / "Codex/rollout_summaries/one.md").read_text(), "summary")
        self.assertEqual((self.mirror / "Graft/Home/cards/file.md").read_text(), "card")
        self.assertEqual((self.mirror / "Graft/Codex-Memory/INDEX.md").read_text(), "codex graph")
        self.assertFalse((self.mirror / "Codex/raw_memories.md").exists())
        self.assertFalse((self.mirror / "Codex/graft").exists())
        self.assertFalse((self.mirror / "Graft/Home/.cache").exists())
        self.assertIn("Graft/Home/", (self.mirror / "INDEX.md").read_text())
        self.assertTrue((self.state / "last-sync").is_file())

    def test_vault_edit_is_kept_and_source_updates_resume_after(self):
        self.sync()
        edited = self.mirror / "Codex/MEMORY.md"
        edited.write_text("edited in Obsidian")
        self.write(".codex/memories/MEMORY.md", "codex index v2")
        self.assertEqual(self.sync()["kept_edited"], 1)
        self.assertEqual(edited.read_text(), "edited in Obsidian")
        self.write(".claude/projects/-home-me/memory/MEMORY.md", "claude v2")
        self.sync()
        self.assertEqual((self.mirror / "Claude/-home-me/MEMORY.md").read_text(), "claude v2")

    def test_removed_source_deletes_only_untouched_copies(self):
        self.sync()
        (self.mirror / "Graft/Home/INDEX.md").write_text("annotated")
        (self.home / "graft/cards/file.md").unlink()
        (self.home / "graft/INDEX.md").unlink()
        self.assertEqual(self.sync()["removed"], 1)
        self.assertFalse((self.mirror / "Graft/Home/cards/file.md").exists())
        self.assertEqual((self.mirror / "Graft/Home/INDEX.md").read_text(), "annotated")

    def test_first_run_refreshes_copies_of_the_earlier_shell_sync_only(self):
        (self.mirror / "Codex").mkdir(parents=True)
        (self.mirror / "Codex/MEMORY.md").write_text("old shell copy")
        (self.mirror / "INDEX.md").write_text("the user's own index")
        self.sync()
        self.assertEqual((self.mirror / "Codex/MEMORY.md").read_text(), "codex index")
        self.assertEqual((self.mirror / "INDEX.md").read_text(), "the user's own index")

    def test_hermes_mirrors_only_persistent_notes_and_keeps_vault_edits(self):
        self.write(".hermes/memories/MEMORY.md", "remember project")
        self.write(".hermes/memories/USER.md", "user preferences")
        self.write(".hermes/memories/private.md", "not selected")
        self.write(".hermes/sessions/transcript.md", "raw conversation")
        self.write(".hermes/.env", "SECRET=private")
        self.write(".hermes/auth.json", "credentials")
        self.sync()
        self.assertEqual(sorted(path.name for path in (self.mirror / "Hermes").iterdir()),
                         ["MEMORY.md", "USER.md"])
        note = self.mirror / "Hermes/MEMORY.md"
        note.write_text("Obsidian edit")
        self.write(".hermes/memories/MEMORY.md", "new memory")
        self.sync()
        self.sync()
        self.assertEqual(note.read_text(), "Obsidian edit")

    def test_custom_hermes_home_selects_only_that_profile(self):
        profile = self.home / "custom-hermes"
        (profile / "memories").mkdir(parents=True)
        (profile / "memories/MEMORY.md").write_text("custom profile")
        self.write(".hermes/memories/MEMORY.md", "default profile")
        with patch.dict(os.environ, {"HERMES_HOME": str(profile)}):
            self.sync()
        self.assertEqual((self.mirror / "Hermes/MEMORY.md").read_text(), "custom profile")

    def test_unmounted_vault_is_reported_without_creating_a_replacement(self):
        missing = self.home / "unmounted-drive/vault"
        result = subprocess.run([sys.executable, str(Path(sync_memories.__file__)),
                                 "--home", str(self.home), "--vault", str(missing), "--state-dir", str(self.state)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(result.returncode, 2)
        self.assertIn("vault unavailable", result.stderr)
        self.assertFalse(missing.exists())
        self.assertFalse(self.state.exists())


if __name__ == "__main__":
    unittest.main()
