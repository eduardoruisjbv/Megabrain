#!/usr/bin/env python3
"""Ownership-aware installation of public skills and relevant-skill routing.

Python 3.8+, standard library only. Never executes downloaded skill content.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile


COLLECTIONS = {
    "security-audit": ("cloudflare/security-audit-skill",
                       "c1c8a8c1471069fb0e188eeaff69b8e8db6564a8", "skills/security-audit/SKILL.md"),
    "claude-red": ("SnailSploit/claude-red",
                   "a8de813edc9f66f60d44cfe42d47750e89d9930b", "Skills/*/*/SKILL.md"),
}
AUTO_BEGIN = "<!-- megabrain:skills-auto:start -->"
AUTO_END = "<!-- megabrain:skills-auto:end -->"
AUTO_BLOCK = """<!-- megabrain:skills-auto:start -->
## Automatic skill selection

At the start of each task and when its scope changes, consult the installed skill
catalog and automatically load skills relevant to the user's actual goal. The
user does not need to name skills or type slash commands. Combine complementary
skills, prefer specific workflows over overlapping generic ones, and keep using
them while applicable. Inspect SKILL.md when a promising catalog entry has no
description. Load bodies progressively rather than loading the entire catalog.

For code review, consider Open Code Review. For security guidance or audits,
consider security-audit and the matching Claude-Red skills. Choose guidance or
full-audit mode according to the user's request. Use mac-remoto for tasks on the
Mac, mimic for HAR/cURL analysis or API client generation, Playwright for browser
automation, and Firecrawl for web extraction. Installation and selection do
not authorize new targets, captures, scans, exploits, publishing, or unrelated
actions; preserve the task's normal permissions and scope.
<!-- megabrain:skills-auto:end -->"""


def exists(path):
    return path.exists() or path.is_symlink()


def digest(path):
    if path.is_symlink():
        return None
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    if not path.is_dir():
        return None
    result = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_symlink() or not (item.is_file() or item.is_dir()):
            return None
        if item.is_file():
            result.update(str(item.relative_to(path)).encode("utf-8") + b"\0")
            result.update(item.read_bytes() + b"\0")
    return result.hexdigest()


def normalize_skill(path):
    """Adapt missing/oversized discovery metadata without discarding upstream prose."""
    text = path.read_text(encoding="utf-8")
    name = path.parent.name
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError("Invalid skill directory: " + name)
    if not text.startswith("---\n"):
        match = re.search(r"(?ms)^## Description\s*\n(.*?)(?=^## |\Z)", text)
        if not match:
            raise ValueError("Missing discovery description: " + name)
        description = " ".join(match.group(1).split())
        text = "---\nname: " + name + "\ndescription: " + json.dumps(description, ensure_ascii=False) + "\n---\n\n" + text
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError("Invalid skill header: " + name)
    match = re.search(r"(?ms)^description:[ \t]*(.*?)(?=\n[A-Za-z_-]+:|\Z)", parts[1])
    if not match:
        raise ValueError("Missing skill description: " + name)
    raw = match.group(1).strip()
    try:
        description = json.loads(raw) if raw.startswith('"') else raw
    except ValueError:
        description = raw.strip('"\'')
    if len(description) > 1024:
        first = re.split(r"(?<=[.!?])\s+", description)[0]
        if len(first) > 800:
            first = first[:800].rsplit(" ", 1)[0] + "."
        short = first + " Use for authorized security work involving " + name.replace("offensive-", "", 1).replace("-", " ") + "."
        parts[1] = parts[1][:match.start()] + "description: " + json.dumps(short, ensure_ascii=False) + "\n" + parts[1][match.end():]
        parts[2] = "\n\n## Upstream discovery description\n\n" + description + "\n" + parts[2]
        text = "---" + parts[1] + "---" + parts[2]
    path.write_text(text, encoding="utf-8")


def download_collection(component, temporary):
    repo, revision, _ = COLLECTIONS[component]
    request = urllib.request.Request("https://codeload.github.com/" + repo + "/zip/" + revision,
                                     headers={"User-Agent": "MEGABRAIN-skill-installer"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read(25 * 1024 * 1024 + 1)
    if len(payload) > 25 * 1024 * 1024:
        raise ValueError("Skill archive exceeds download limit")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        infos = archive.infolist()
        if sum(item.file_size for item in infos) > 64 * 1024 * 1024:
            raise ValueError("Skill archive exceeds extracted-size limit")
        for item in infos:
            path = PurePosixPath(item.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in item.filename or stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError("Unsafe archive member")
        archive.extractall(temporary)
    roots = list(Path(temporary).iterdir())
    if len(roots) != 1 or not roots[0].is_dir():
        raise ValueError("Unexpected skill archive layout")
    return roots[0]


class Installer:
    def __init__(self, home, state_dir, agents, codex_home=None):
        self.home = Path(home).absolute()
        self.state_dir = Path(state_dir).absolute()
        self.codex_home = Path(codex_home).absolute() if codex_home else self.home / ".codex"
        self.agents = set(agents) & {"claude", "codex"}
        self.state_path = self.state_dir / "skills.json"
        self.data = json.loads(self.state_path.read_text()) if self.state_path.exists() else {"version": 1, "entries": {}}
        if self.data.get("version") != 1:
            raise ValueError("Unsupported skills ownership ledger")

    def save(self):
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = self.state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.chmod(0o600)
        os.replace(str(temporary), str(self.state_path))

    def remember(self, path, component, kind, **details):
        self.data["entries"][str(path)] = dict(details, component=component, kind=kind)
        self.save()

    def owned_parents(self, path):
        return [(Path(key), item) for key, item in self.data["entries"].items()
                if item["kind"] == "directory" and Path(key) in path.parents
                and digest(Path(key)) == item["after"]]

    def edit(self, path, new_text, kind="edit", **details):
        before = path.read_text(encoding="utf-8") if path.exists() else None
        if before == new_text:
            return
        key = str(path)
        previous = self.data["entries"].get(key)
        if previous and previous.get("after") != digest(path):
            # Do not acquire ownership of intervening user changes on a rerun.
            return
        backup = previous.get("backup") if previous else None
        if before is not None and not previous:
            backup_path = self.state_dir / "skills-backups" / hashlib.sha256(key.encode()).hexdigest()
            backup_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            backup_path.write_text(before, encoding="utf-8")
            backup_path.chmod(0o600)
            backup = str(backup_path)
        parents = self.owned_parents(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_text, encoding="utf-8")
        for parent, item in parents:
            item["after"] = digest(parent)
        self.remember(path, "skills-auto", kind, backup=backup, after=digest(path), **details)

    def install_collection(self, component, source=None):
        if not self.agents:
            return {"created": 0, "preexisting": 0}
        with tempfile.TemporaryDirectory(prefix="megabrain-skills-") as temporary:
            root = Path(source) if source else download_collection(component, temporary)
            pattern = COLLECTIONS[component][2] if component in COLLECTIONS else "skills/*/SKILL.md"
            entries = sorted(root.glob(pattern))
            if not entries:
                raise ValueError("No skills found in pinned collection: " + component)
            count = {"created": 0, "preexisting": 0}
            for entry in entries:
                targets = []
                name = entry.parent.name
                if "codex" in self.agents:
                    codex = [self.codex_home / "skills" / name, self.home / ".agents/skills" / name]
                    if not any(exists(path) for path in codex):
                        targets.extend(codex)
                if "claude" in self.agents:
                    path = self.home / ".claude/skills" / name
                    if not exists(path):
                        targets.append(path)
                if not targets:
                    count["preexisting"] += 1
                    continue
                destination = self.state_dir / "skill-files" / component / name
                if not exists(destination):
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with tempfile.TemporaryDirectory(prefix=".prepare-", dir=str(destination.parent)) as stage:
                        prepared = Path(stage) / name
                        shutil.copytree(entry.parent, prepared)
                        normalize_skill(prepared / "SKILL.md")
                        if (root / "LICENSE").is_file():
                            shutil.copy2(root / "LICENSE", prepared / "LICENSE.upstream")
                        os.replace(str(prepared), str(destination))
                    self.remember(destination, component, "directory", after=digest(destination))
                elif str(destination) not in self.data["entries"]:
                    raise ValueError("Unmanaged destination preserved: " + str(destination))
                for target in targets:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.symlink_to(destination, target_is_directory=True)
                    self.remember(target, component, "link", target=str(destination))
                count["created"] += 1
            return count

    def skill_roots(self):
        roots = [self.home / ".agents/skills"]
        if "codex" in self.agents:
            roots.append(self.codex_home / "skills")
            try:
                result = subprocess.run(["codex", "plugin", "list", "--json"], stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, universal_newlines=True, timeout=30, check=True)
                def walk(value):
                    if isinstance(value, list):
                        for item in value:
                            yield from walk(item)
                    elif isinstance(value, dict):
                        if value.get("installed") and value.get("enabled") and "pluginId" in value:
                            yield self.codex_home / "plugins/cache" / value["marketplaceName"] / value["name"] / value["version"]
                        else:
                            for item in value.values():
                                yield from walk(item)
                roots.extend(walk(json.loads(result.stdout)))
            except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                print("Note: Codex plugin metadata unavailable; personal skills remain eligible.", file=sys.stderr)
        if "claude" in self.agents:
            roots.append(self.home / ".claude/skills")
            registry = self.home / ".claude/plugins/installed_plugins.json"
            settings_file = self.home / ".claude/settings.json"
            settings = json.loads(settings_file.read_text()) if settings_file.exists() else {}
            if registry.exists():
                for name, entries in json.loads(registry.read_text()).get("plugins", {}).items():
                    if settings.get("enabledPlugins", {}).get(name, True):
                        roots.extend(Path(item["installPath"]) for item in entries if item.get("installPath"))
        return roots

    def install_auto(self):
        instructions = []
        if "codex" in self.agents:
            instructions.append(self.codex_home / "AGENTS.md")
        if "claude" in self.agents:
            instructions.append(self.home / ".claude/CLAUDE.md")
        for path in instructions:
            before = path.read_text(encoding="utf-8") if path.exists() else ""
            if AUTO_BEGIN not in before:
                self.edit(path, before.rstrip() + "\n\n" + AUTO_BLOCK + "\n", kind="instructions", block=AUTO_BLOCK)
        seen = set()
        for root in self.skill_roots():
            # pathlib does not recurse into symlink directories. Resolve direct
            # personal-skill links so both installed layouts are supported.
            candidates = list(root.rglob("SKILL.md")) + list(root.rglob("openai.yaml")) if root.is_dir() else []
            if root.is_dir():
                for link in root.iterdir():
                    if link.is_symlink() and link.is_dir():
                        candidates.extend(link.resolve().rglob("SKILL.md"))
                        candidates.extend(link.resolve().rglob("openai.yaml"))
            for path in candidates:
                path = path.resolve()
                if path in seen or (self.codex_home / "skills/.system").resolve() in path.parents:
                    continue
                seen.add(path)
                text = path.read_text(encoding="utf-8")
                if path.name == "openai.yaml":
                    changed = re.sub(r"(?m)^(\s*allow_implicit_invocation:[ \t]*)false([ \t]*(?:#.*)?)$", r"\g<1>true\2", text)
                elif text.startswith("---\n"):
                    parts = text.split("---", 2)
                    if len(parts) != 3:
                        continue
                    parts[1] = re.sub(r"(?m)^(disable-model-invocation:\s*)true\b", r"\g<1>false", parts[1])
                    changed = "---".join(parts)
                else:
                    continue
                if changed != text:
                    self.edit(path, changed)
        if "claude" in self.agents:
            path = self.home / ".claude/settings.json"
            settings = json.loads(path.read_text()) if path.exists() else {}
            old_budget = settings.get("skillListingBudgetFraction")
            overrides = settings.get("skillOverrides", {})
            had_overrides = "skillOverrides" in settings
            settings["skillListingBudgetFraction"] = max(old_budget or 0.01, 0.03)
            settings["skillOverrides"] = {key: "on" for key in overrides}
            if not settings["skillOverrides"] and not had_overrides:
                settings.pop("skillOverrides")
            self.edit(path, json.dumps(settings, ensure_ascii=False, indent=2) + "\n", kind="settings")
        return {"owned_entries": len(self.owned("skills-auto"))}

    def owned(self, component):
        return {key: item for key, item in self.data["entries"].items() if item["component"] == component}

    def uninstall(self, component):
        result = {"removed": 0, "kept_modified": 0}
        entries = self.owned(component)
        for key, item in sorted(entries.items(), key=lambda pair: pair[1]["kind"] == "directory"):
            path = Path(key)
            remove = not exists(path)
            if item["kind"] == "link":
                if path.is_symlink() and os.readlink(str(path)) == item["target"]:
                    path.unlink()
                    remove = True
            elif exists(path) and digest(path) == item.get("after"):
                parents = self.owned_parents(path)
                if item["kind"] == "directory":
                    shutil.rmtree(path)
                elif item.get("backup"):
                    shutil.copyfile(item["backup"], path)
                else:
                    path.unlink()
                for parent, parent_entry in parents:
                    parent_entry["after"] = digest(parent)
                remove = True
            elif item["kind"] == "instructions" and path.is_file() and not path.is_symlink():
                text = path.read_text(encoding="utf-8")
                if item["block"] in text:
                    path.write_text(text.replace(item["block"], "", 1), encoding="utf-8")
                    remove = True
            if remove:
                self.data["entries"].pop(key)
                result["removed"] += 1
                self.save()
            else:
                result["kept_modified"] += 1
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "uninstall", "owned"])
    parser.add_argument("component", choices=list(COLLECTIONS) + ["skills-auto"])
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME"))
    parser.add_argument("--agents", default="claude,codex")
    args = parser.parse_args()
    installer = Installer(args.home, args.state_dir, args.agents.replace(",", " ").split(), args.codex_home)
    if args.action == "owned":
        return 0 if installer.owned(args.component) else 1
    if args.action == "uninstall":
        result = installer.uninstall(args.component)
    elif args.component == "skills-auto":
        result = installer.install_auto()
    else:
        result = installer.install_collection(args.component)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print("MEGABRAIN skills: " + str(error), file=sys.stderr)
        sys.exit(1)
