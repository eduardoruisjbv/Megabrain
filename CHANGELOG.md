# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1] - 2026-10-13

### Changed
- README hero now shows only the brain artwork, without installer context.

### Verified
- Full install verified on macOS (Intel, Homebrew).

## [1.0.0] - 2026-10-13

First public release.

### Added
- **Universal installer** (`install.sh`): detects the coding agents present on the
  machine (Claude Code, Codex, Gemini, Cursor, Windsurf, OpenCode, Kilo Code,
  Antigravity, Hermes, Kiro, Droid, Vibe, Pi, Copilot, Cline) and configures the
  stack for every one of them.
- **Stack**: [RTK](https://github.com/rtk-ai/rtk) (command output compression),
  [graft](https://www.npmjs.com/package/@nanonets/graft) (repository context graph),
  [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) (structural
  graph), plus the `claude-mem`, `superpowers` and `ECC` plugins for Claude Code.
- **Memory vault**: a plain-Markdown vault (PARA layout, Obsidian-ready) created
  with or without Obsidian, with a sync job that mirrors agent memories into
  `03-Recursos/IA/` every 48 hours (systemd user timer, launchd or cron).
- **Optional Obsidian install** at the end, with a Yes/No selector and the right
  command for the detected OS (Homebrew, Flatpak, Snap, pacman).
- **Animated terminal UI** (`lib/ui.py`): braille brain, per-step progress, live log,
  keyboard selector. Falls back to plain text when there is no TTY/Python.
- **Install detection**: a manifest (`~/.megabrain/manifest.env`) records what was
  installed. Running the installer again shows *"MEGABRAIN already installed"* and
  offers to uninstall.
- **Safe uninstaller** (`uninstall.sh`, `megabrain uninstall`): removes only what
  MEGABRAIN installed itself, keeps the vault unless asked, and never touches
  tools that were already on the machine.
- **`megabrain` command** (`status`, `sync`, `uninstall`, `version`).
- **Preview mode**: `python3 lib/ui.py --demo` shows the whole experience without
  installing or writing anything.
- Linux (apt, dnf, yum, pacman, zypper, apk, xbps), macOS (Homebrew) and WSL support.

[Unreleased]: https://github.com/eduardoruisjbv/Megabrain/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/eduardoruisjbv/Megabrain/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/eduardoruisjbv/Megabrain/releases/tag/v1.0.0
