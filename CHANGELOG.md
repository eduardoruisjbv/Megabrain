# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Add Playwright MCP, keyless Firecrawl MCP, pinned Mimic CLI and task skill,
  and Open Code Review CLI with native Codex/Claude Code plugins.
- Add a configurable Mac SSH client and public persistent job worker, explicit
  shared context, status/logs/results, record exports, cancellation and resume.
- Preserve pre-existing native integrations and subsequent configuration changes
  through a separate ownership ledger; keep remote tasks and SSH configuration.
- Show the active component in a scrolling fixed-height progress panel.
- Install Cloudflare Security Audit and the pinned Claude-Red collection for
  detected Codex and Claude Code clients, including complete reference files.
- Adapt missing/oversized discovery metadata without discarding upstream content.
- Configure automatic selection of relevant installed skills, with backed-up
  invocation metadata and global instructions; keep execution permissions intact.
- Track skill copies, links and configuration edits in a separate ownership
  ledger that survives forced/selected reinstalls and preserves later user edits.
- Add offline ownership/rollback tests and CI coverage for the skill installer.

### Fixed
- Allow CAD installation dry-runs with explicit agent overrides even when those
  agent commands are not installed, matching the rest of the simulated workflow.

## [1.0.2] - 2026-10-20

### Added
- Install text-to-cad for detected Codex and Claude Code clients, track ownership
  independently per client, and remove only copies installed by MEGABRAIN.
- Install Anthropic's read-only claude-code-setup recommendations plugin for
  detected Claude Code clients.
- Document text-to-cad's first-use CAD runtime download and telemetry controls.
- Install REA for detected supported clients, track whether MEGABRAIN owns its
  CLI and setup separately, and preserve pre-existing REA configuration on uninstall.

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

[Unreleased]: https://github.com/eduardoruisjbv/Megabrain/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/eduardoruisjbv/Megabrain/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/eduardoruisjbv/Megabrain/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/eduardoruisjbv/Megabrain/releases/tag/v1.0.0
