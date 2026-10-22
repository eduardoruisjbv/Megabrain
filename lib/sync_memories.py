#!/usr/bin/env python3
"""Mirror curated agent memories and Graft cards into the vault.

Python 3.8+, standard library only. Sources are only read. In the vault, a
mirrored note that was edited there (for example in Obsidian) is never
overwritten, and a note whose source disappeared is removed only while it is
still exactly what this sync wrote.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

INTERNAL = {".cache", ".graph", ".git"}
LEGACY = ("Claude/", "Codex/", "Gemini/")  # folders the earlier shell sync wrote


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=str(path.parent), delete=False) as handle:
        handle.write(payload)
        temporary = handle.name
    os.replace(temporary, str(path))


def markdown(root, skip=()):
    """Markdown files under root, without graph internals or skipped subtrees."""
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if INTERNAL & set(relative.parts) or (relative.parts and relative.parts[0] in skip):
            continue
        if path.is_file():
            yield relative, path


def collect(home):
    selected = {}
    # Claude Code: automatic memory of every project.
    for memory in sorted((home / ".claude/projects").glob("*/memory")):
        for relative, path in markdown(memory):
            selected["Claude/" + memory.parent.name + "/" + relative.as_posix()] = path
    # Codex: curated memories and session summaries; raw extraction files are left out.
    codex = home / ".codex/memories"
    if codex.is_dir():
        for relative, path in markdown(codex, skip={"graft"}):
            if not path.name.lower().startswith("raw_memories"):
                selected["Codex/" + relative.as_posix()] = path
    gemini = home / ".gemini/GEMINI.md"
    if gemini.is_file():
        selected["Gemini/GEMINI.md"] = gemini
    # Hermes: only its two persistent notes, never auth, sessions, databases or .env.
    hermes = Path(os.environ.get("HERMES_HOME", str(home / ".hermes")))
    for name in ["MEMORY.md", "USER.md"]:
        note = hermes / "memories" / name
        if note.is_file():
            selected["Hermes/" + name] = note
    # Graft cards, when a graph was built for the home folder or the Codex memories.
    for label, root in [("Home", home / "graft"), ("Codex-Memory", codex / "graft")]:
        if (root / "INDEX.md").is_file():
            for relative, path in markdown(root):
                selected["Graft/" + label + "/" + relative.as_posix()] = path
    return selected


def index_note(selected):
    groups = sorted({"/".join(key.split("/")[:2]) if key.startswith(("Claude/", "Graft/")) else key.split("/")[0]
                     for key in selected})
    lines = ["# AI contexts", "",
             "Mirrored automatically by MEGABRAIN. Notes edited here are kept; their source is not changed.", ""]
    lines += ["- " + group + "/" for group in groups] or ["- (nothing to mirror yet)"]
    return ("\n".join(lines) + "\n").encode("utf-8")


def sync(home, vault, state_dir, dry_run=False):
    destination = vault / "03-Recursos/IA"
    manifest_path = state_dir / "sync-manifest.json"
    # Before this manifest existed, the sync overwrote its mirror on every run,
    # so a first run may refresh those copies like any earlier run did.
    legacy = not manifest_path.exists()
    try:
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    current = collect(home)
    payloads = {key: path.read_bytes() for key, path in current.items()}
    payloads["INDEX.md"] = index_note(current)
    result = {"created": 0, "updated": 0, "kept_edited": 0, "removed": 0}
    manifest = {}
    for key, payload in sorted(payloads.items()):
        target = destination / key
        wanted = hashlib.sha256(payload).hexdigest()
        previous = old.get(key)
        if target.is_file():
            found = digest(target)
            if previous and found != previous:
                result["kept_edited"] += 1
                manifest[key] = previous
                continue
            if found == wanted:
                manifest[key] = wanted
                continue
            if not previous and not (legacy and key.startswith(LEGACY)):
                # A note that this sync never wrote: never take it over.
                result["kept_edited"] += 1
                continue
            result["updated"] += 1
        else:
            result["created"] += 1
        manifest[key] = wanted
        if not dry_run:
            atomic_write(target, payload)
    for key, previous in old.items():
        target = destination / key
        if key not in payloads and target.is_file() and digest(target) == previous:
            result["removed"] += 1
            if not dry_run:
                target.unlink()
    if not dry_run:
        state_dir.mkdir(parents=True, exist_ok=True)
        atomic_write(manifest_path, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        atomic_write(state_dir / "last-sync", (stamp + "\n").encode("utf-8"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", required=True)
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--home", default=str(Path.home()))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    vault = Path(args.vault)
    if not vault.is_dir():
        print("MEGABRAIN vault unavailable: " + str(vault), file=sys.stderr)
        return 2
    print(json.dumps(sync(Path(args.home), vault, Path(args.state_dir), args.dry_run)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError as error:
        print("MEGABRAIN sync: " + str(error), file=sys.stderr)
        sys.exit(1)
