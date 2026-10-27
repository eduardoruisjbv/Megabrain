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
import shlex
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile


# component -> pinned upstream sources: (repo, revision, SKILL.md globs, options).
# Options: "name" names a skill whose SKILL.md sits at the repository root,
# "exclude" lists relative paths left out of the installed copy, and
# "security" keeps the authorized-security suffix on shortened descriptions.
COLLECTIONS = {
    "security-audit": [("cloudflare/security-audit-skill", "c1c8a8c1471069fb0e188eeaff69b8e8db6564a8",
                        ["skills/security-audit/SKILL.md"], {"security": True})],
    "claude-red": [("SnailSploit/claude-red", "a8de813edc9f66f60d44cfe42d47750e89d9930b",
                    ["Skills/*/*/SKILL.md"], {"security": True})],
    "design-skills": [
        ("juliobsz/skills", "ea8f1455c2b0e71469d4ecfd32f47862b834d2d0", ["awwwards/SKILL.md", "jury/SKILL.md"], {}),
        ("miqdadbadjuber/anti-slop", "439a2ef5b9dd0ebe74e8113ff43f5928d0fe2a6a", ["skills/*/SKILL.md"], {}),
        ("kaankiziltug/logo-design-skill", "734090317a2155c5bf1ae8bd4cc85c6848a0128f",
         ["skills/logo-design/SKILL.md"], {}),
        ("Tejashmakwana/motionmaxxing", "8c8ec0f2a6f6c9a0da15cd24f7b1298ab298368c", ["SKILL.md"],
         {"name": "motionmaxxing", "exclude": ["docs/media"]}),
    ],
    "writing-skills": [
        ("blader/humanizer", "8c307f367c91bd974002f10f2be2965d642c13df", ["SKILL.md"],
         {"name": "humanizer", "exclude": [".github"]}),
        ("petergyang/no-ai-slop", "000650b156983f5159695b441477f4e63b25dc85", ["skills/no-ai-slop/SKILL.md"], {}),
    ],
    "workflow-skills": [
        ("vercel-labs/skills", "a80e4c9d12d607631249d4d7d059f835d4b2f13a", ["skills/find-skills/SKILL.md"], {}),
        ("mattpocock/skills", "5beb35b040e3de97e54fa9e386d7e42d15c295c2",
         ["skills/productivity/grill-me/SKILL.md"], {}),
    ],
}
MAX_DOWNLOAD = 64 * 1024 * 1024
MAX_EXTRACTED = 160 * 1024 * 1024
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
automation, and Firecrawl for web extraction. For interfaces and websites,
consider awwwards (build), jury (score) and the antislop skills; logo-design for
brand marks; motionmaxxing for motion graphics and promo films; humanizer and
no-ai-slop when editing prose; grill-me to stress-test a plan; and find-skills
when no installed skill fits. Installation and selection do
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


def normalize_skill(path, security=True):
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
        short = first
        if security:
            short += " Use for authorized security work involving " + name.replace("offensive-", "", 1).replace("-", " ") + "."
        parts[1] = parts[1][:match.start()] + "description: " + json.dumps(short, ensure_ascii=False) + "\n" + parts[1][match.end():]
        parts[2] = "\n\n## Upstream discovery description\n\n" + description + "\n" + parts[2]
        text = "---" + parts[1] + "---" + parts[2]
    path.write_text(text, encoding="utf-8")


def download_source(repo, revision, temporary):
    request = urllib.request.Request("https://codeload.github.com/" + repo + "/zip/" + revision,
                                     headers={"User-Agent": "MEGABRAIN-skill-installer"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read(MAX_DOWNLOAD + 1)
    if len(payload) > MAX_DOWNLOAD:
        raise ValueError("Skill archive exceeds download limit")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        infos = archive.infolist()
        if sum(item.file_size for item in infos) > MAX_EXTRACTED:
            raise ValueError("Skill archive exceeds extracted-size limit")
        for item in infos:
            path = PurePosixPath(item.filename)
            if path.is_absolute() or ".." in path.parts or "\\" in item.filename:
                raise ValueError("Unsafe archive member")
        # Symbolic links are never materialized; they could point outside the copy.
        archive.extractall(temporary, [item for item in infos if not stat.S_ISLNK(item.external_attr >> 16)])
    roots = list(Path(temporary).iterdir())
    if len(roots) != 1 or not roots[0].is_dir():
        raise ValueError("Unexpected skill archive layout")
    return roots[0]


def download_collection(component, temporary):
    repo, revision, _, _ = COLLECTIONS[component][0]
    return download_source(repo, revision, temporary)


def excluded(root, patterns):
    """shutil.copytree ignore callback leaving out the given relative paths."""
    def ignore(directory, names):
        relative = Path(directory).relative_to(root)
        return [name for name in names if (relative / name).as_posix() in patterns]
    return ignore


class Installer:
    def __init__(self, home, state_dir, agents, codex_home=None):
        self.home = Path(home).absolute()
        self.state_dir = Path(state_dir).absolute()
        self.codex_home = Path(codex_home).absolute() if codex_home else self.home / ".codex"
        self.hermes_home = Path(os.environ.get("HERMES_HOME", str(self.home / ".hermes"))).absolute()
        self.agents = set(agents) & {"claude", "codex", "hermes"}
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

    def save_router_roots(self, roots):
        directory = self.state_dir / "skill-router"
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        shared = self.home / ".agents/skills"
        clients = {
            "codex": (self.codex_home, "codex"),
            "claude": (self.home / ".claude", "claude"),
        }
        for client, (base, agent) in clients.items():
            if agent not in self.agents:
                continue
            selected = [str(Path(root).absolute()) for root in roots
                        if Path(root).absolute() == shared.absolute()
                        or base.absolute() == Path(root).absolute()
                        or base.absolute() in Path(root).absolute().parents]
            target = directory / ("roots-" + client + ".json")
            temporary = target.with_suffix(".tmp")
            temporary.write_text(json.dumps(selected) + "\n", encoding="utf-8")
            temporary.chmod(0o600)
            os.replace(str(temporary), str(target))

    def invalidate_router_index(self):
        for path in (self.state_dir / "skill-router").glob("local-index-*.json"):
            try:
                path.unlink()
            except OSError:
                pass

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

    def edit_hook(self, path, new_text, event, command):
        """Merge one owned hook even when a user changed other settings later."""
        before = path.read_text(encoding="utf-8") if path.exists() else None
        key = str(path)
        previous = self.data["entries"].get(key)
        preserve_existing = bool(previous and previous.get("after") != digest(path)) or bool(previous and previous.get("preserve_existing"))
        backup = previous.get("backup") if previous and not preserve_existing else None
        if before is not None and not backup and not preserve_existing:
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
        self.remember(path, "skills-auto", "router-hook", backup=backup, after=digest(path),
                      event=event, command=command, preserve_existing=preserve_existing)

    def register_router_hook(self, path, event, command):
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if not isinstance(data, dict):
            raise ValueError("Invalid hook settings object: " + str(path))
        hooks = data.setdefault("hooks", {})
        if not isinstance(hooks, dict):
            raise ValueError("Invalid hooks object: " + str(path))
        groups = hooks.setdefault(event, [])
        if not isinstance(groups, list):
            raise ValueError("Invalid hook event list: " + event)
        found = False
        changed = False
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks", []), list):
                continue
            for handler in group.get("hooks", []):
                if isinstance(handler, dict) and handler.get("command") == command:
                    found = True
                    if handler.get("timeout") != 65:
                        handler["timeout"] = 65
                        changed = True
        if not found:
            groups.append({"hooks": [{"type": "command", "command": command, "timeout": 65}]})
            changed = True
        if changed:
            self.edit_hook(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                           event=event, command=command)

    def install_collection(self, component, source=None):
        """Install every pinned source of a component; `source` replaces downloads
        (one path for all sources, or a mapping of repository to path)."""
        self.invalidate_router_index()
        if not self.agents:
            return {"created": 0, "preexisting": 0}
        specs = COLLECTIONS.get(component, [(None, None, ["skills/*/SKILL.md"], {})])
        count = {"created": 0, "preexisting": 0}
        for index, (repo, revision, patterns, options) in enumerate(specs):
            with tempfile.TemporaryDirectory(prefix="megabrain-skills-") as temporary:
                if isinstance(source, dict):
                    root = Path(source[repo])
                elif source:
                    root = Path(source)
                else:
                    root = download_source(repo, revision, temporary)
                entries = sorted(entry for pattern in patterns for entry in root.glob(pattern))
                if not entries:
                    raise ValueError("No skills found in pinned collection: " + component + " (" + str(repo) + ")")
                self.install_entries(component, root, entries, options, count)
        return count

    def install_entries(self, component, root, entries, options, count):
        for entry in entries:
            targets = []
            name = options["name"] if entry.parent == root and options.get("name") else entry.parent.name
            if "codex" in self.agents:
                codex = [self.codex_home / "skills" / name, self.home / ".agents/skills" / name]
                if not any(exists(path) for path in codex):
                    targets.extend(codex)
            if "claude" in self.agents:
                path = self.home / ".claude/skills" / name
                if not exists(path):
                    targets.append(path)
            if "hermes" in self.agents:
                path = self.hermes_home / "skills" / name
                # Bundled and user skills can live in category subdirectories.
                # A flat copy with the same name would shadow an existing skill.
                if not hasattr(self, "_hermes_names"):
                    root = self.hermes_home / "skills"
                    self._hermes_names = {item.name for item in root.rglob("*")
                                          if item.is_dir() and (item / "SKILL.md").is_file()}
                if not exists(path) and name not in self._hermes_names:
                    targets.append(path)
                    self._hermes_names.add(name)
            if not targets:
                count["preexisting"] += 1
                continue
            destination = self.state_dir / "skill-files" / component / name
            if not exists(destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(prefix=".prepare-", dir=str(destination.parent)) as stage:
                    prepared = Path(stage) / name
                    shutil.copytree(entry.parent, prepared,
                                    ignore=excluded(entry.parent, set(options.get("exclude", []))))
                    normalize_skill(prepared / "SKILL.md", options.get("security", False))
                    if (root / "LICENSE").is_file() and entry.parent != root:
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

    def skill_roots(self):
        roots = [self.home / ".agents/skills"] if self.agents & {"codex", "claude"} else []
        if "hermes" in self.agents:
            roots.append(self.hermes_home / "skills")
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

    def refresh_block(self, path, text):
        """Replace an older MEGABRAIN block with the current one on update.
        Only the block this installer wrote is touched; edits around it are kept."""
        entry = self.data["entries"].get(str(path))
        if not entry or entry.get("kind") != "instructions" or entry.get("block") == AUTO_BLOCK:
            return
        if entry.get("block") not in text:
            return  # the user edited the block itself; leave it alone
        unchanged = digest(path) == entry.get("after")
        path.write_text(text.replace(entry["block"], AUTO_BLOCK, 1), encoding="utf-8")
        entry["block"] = AUTO_BLOCK
        if unchanged:
            entry["after"] = digest(path)
        self.save()

    def install_auto(self):
        self.invalidate_router_index()
        instructions = []
        if "codex" in self.agents:
            instructions.append(self.codex_home / "AGENTS.md")
        if "claude" in self.agents:
            instructions.append(self.home / ".claude/CLAUDE.md")
        if "hermes" in self.agents:
            instructions.append(self.hermes_home / "SOUL.md")
        for path in instructions:
            before = path.read_text(encoding="utf-8") if path.exists() else ""
            if AUTO_BEGIN not in before:
                self.edit(path, before.rstrip() + "\n\n" + AUTO_BLOCK + "\n", kind="instructions", block=AUTO_BLOCK)
            else:
                self.refresh_block(path, before)
        seen = set()
        active_roots = self.skill_roots()
        self.save_router_roots(active_roots)
        for root in active_roots:
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
        hook_script = self.state_dir.parent / "lib/skill_router.py"
        hook_command_codex = "python3 " + shlex.quote(str(hook_script)) + " hook --client codex"
        hook_command_claude = "python3 " + shlex.quote(str(hook_script)) + " hook --client claude"
        if "codex" in self.agents:
            self.register_router_hook(self.codex_home / "hooks.json", "UserPromptSubmit", hook_command_codex)
        if "claude" in self.agents:
            self.register_router_hook(self.home / ".claude/settings.json", "UserPromptSubmit", hook_command_claude)
        return {"owned_entries": len(self.owned("skills-auto"))}

    def owned(self, component):
        return {key: item for key, item in self.data["entries"].items() if item["component"] == component}

    def uninstall(self, component):
        if component == "skills-auto" or component in COLLECTIONS:
            self.invalidate_router_index()
        if component == "skills-auto":
            for client in ("codex", "claude"):
                try:
                    (self.state_dir / "skill-router" / ("roots-" + client + ".json")).unlink()
                except OSError:
                    pass
        result = {"removed": 0, "kept_modified": 0}
        entries = self.owned(component)
        for key, item in sorted(entries.items(), key=lambda pair: pair[1]["kind"] == "directory"):
            path = Path(key)
            remove = not exists(path)
            if item["kind"] == "link":
                if path.is_symlink() and os.readlink(str(path)) == item["target"]:
                    path.unlink()
                    remove = True
            elif exists(path) and digest(path) == item.get("after") and not (item["kind"] == "router-hook" and item.get("preserve_existing")):
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
            elif item["kind"] == "router-hook" and path.is_file() and not path.is_symlink():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    hooks = data.get("hooks", {})
                    groups = hooks.get(item.get("event"), [])
                    kept = []
                    for group in groups:
                        group["hooks"] = [entry for entry in group.get("hooks", []) if entry.get("command") != item.get("command")]
                        if group["hooks"]:
                            kept.append(group)
                    if kept:
                        hooks[item["event"]] = kept
                    else:
                        hooks.pop(item.get("event"), None)
                    if not hooks:
                        data.pop("hooks", None)
                    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                    if digest(path) != item.get("after"):
                        result["kept_modified"] += 1
                    remove = True
                except (ValueError, TypeError):
                    pass
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
