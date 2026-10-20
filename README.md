<div align="center">

# 🧠 MEGABRAIN

**One command that gives every AI coding agent on your machine token-saving tools and a long-term memory vault.**

![Version](https://img.shields.io/badge/version-1.0.2-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platforms](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20WSL-lightgrey)
![Shell](https://img.shields.io/badge/shell-bash-4EAA25)
![Agents](https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex%20%7C%20Gemini%20%7C%20Cursor%20%7C%20%2B10-8A2BE2)

</div>

```
                   ⢀⢄⢤⢴⢴⢴⢴⢄⢤⢴⢴⠄⢵⢝⠅⢕⢴⠄⢀⢀⢀⢀⢀⠀
            ⢀⢀⢀⢀⢀⢀⠐⢙⢙⠁⢅⢹⢝⢽⢽⢽⢝⢽⠅⢽⢝⠅⢝⢽⠅⢽⢽⢽⢝⢽⢽⢴⢄⠀
          ⢀⢴⢝⢽⢽⢽⢽⢽⢝⠝⠝⢵⢵⢼⠝⢁⢔⢽⢽⢽⠅⢽⢽⠅⢝⢽⠅⢽⢝⢽⢉⢍⠝⠝⠝⠕⠄
        ⠀⢐⠝⢝⢝⢝⢙⢥⢴⢤⢕⢄⢙⢴⠝⢁⢕⢽⢝⢽⢝⠝⠁⠽⢽⠅⢽⠝⢅⠍⢝⢽⢤⢥⢽⢽⢝⢽⢽⢽⢝⢤⢄⠀
     ⠀⠔⠴⠽⠽⠝⢙⠙⢽⢽⢽⢽⢽⢽⢽⠝⢁⢴⢽⠝⢍⠙⢽⢽⢅⠝⢁⢽⠅⢝⢵⢔⢴⢝⢽⢝⢽⠽⢽⢝⢽⢝⠝⢙⢽⢝⢥⠀
   ⢀⢔⢴⢴⢴⢴⢴⢕⢝⢅⢽⠽⠽⢝⢽⢝⢽⠅⢽⢽⢽⢅⠙⢅⢽⢽⢽⠅⢽⠝⠅⠝⢽⢝⢽⠝⢙⢙⠁⢕⠤⢙⢽⢝⢄⢙⢴⢴⢴⢴⠄
  ⢀⢭⢍⢍⢍⢍⢍⢍⠍⢍⢍⢍⠅⠵⢐⢽⢝⢽⢅⢽⢝⢽⢝⠅⢝⢽⠝⢍⢵⢽⢅⠝⢁⢽⠽⢅⢴⢽⢽⢽⢕⢴⢝⢽⠝⢉⠙⢽⠽⢽⢝⢅⠀
  ⢘⢙⢙⢙⢙⢙⢙⢁⢐⠄⢙⢽⢽⢽⢝⢽⢝⢥⢝⢽⢽⠽⢉⢴⢝⢽⠁⢽⢽⢽⢝⢽⢿⣕⢱⢽⢿⣽⢿⣽⢿⣽⢿⢽⢇⣝⢁⢴⢗⢴⢵⢴⢵⢴⢄
⠀⠼⠝⠽⠝⠽⠽⠝⢉⠙⢵⢴⢽⢽⢝⢽⢽⢽⢝⢽⢽⢽⢝⢰⢽⢽⢽⢽⠅⢽⢿⣽⢿⣽⢿⢟⢝⢝⢝⢝⢽⣿⣿⣿⣿⣿⢿⣽⢿⢽⢿⣽⢿⣽⢽⢽⢽⢅
⢵⢵⢵⢵⢕⢵⢕⢄⢙⢵⢝⢽⢝⠅⢔⠄⠙⢝⠙⠹⢽⢽⢝⢼⢽⣽⢿⣽⢕⣿⢿⢟⢝⣵⣿⣿⣿⣿⢿⣿⢿⣿⢿⣿⢿⣿⢿⣿⣝⢗⣵⣵⣵⣵⢵⣵⢵⢵⠄
⢽⢽⢝⢽⢝⢽⠝⠽⢝⢽⢝⢽⢝⢵⢵⢴⢝⢽⢝⢵⢝⢽⢝⢽⣿⣽⣿⣿⢝⢟⢕⣵⢿⣿⢿⢽⢿⢽⢿⢽⢿⢽⢿⢽⢿⠍⢵⠍⠿⠿⠿⢿⠿⢿⢿⢿⢿⢿⠅
⠀⠡⢅⢥⢅⢥⠅⠽⢐⢽⢝⢽⢽⢽⢽⢽⢝⢽⢽⢽⠕⢽⢟⢝⢟⢝⢝⣵⢵⢽⢿⢽⢽⢽⢿⢽⢽⢽⢝⢽⢽⢽⢝⢽⢽⢵⢍⢵⢝⢽⢽⠝⢝⠝⠿⢽⠿⢿⢷
 ⠀⠝⠽⠝⠽⠽⠽⠝⢉⠝⢽⢝⢽⢽⢽⢿⢽⠟⢕⢵⣵⣿⣿⢿⣽⢿⢽⢿⢽⢽⢽⢽⢽⢽⢽⢽⠽⠝⢁⢵⢜⢝⢽⢝⢽⢝⢽⢝⢽⢝⢥⢍⢵⢟⢽⢿⢿⢿⣇
  ⠑⢵⢽⢵⢝⢵⢕⢤⢥⢽⢽⢽⢽⢽⠟⢵⣿⣿⣿⣿⢿⣽⢿⠝⠝⢽⢽⢽⢝⠽⠝⢙⢉⢥⢴⢴⢝⢵⢵⢴⢽⢽⠝⢡⢔⢴⢔⢴⢵⢴⢍⢙⢙⢙⢙⢙⢙⢙
   ⠀⠑⢥⢵⢥⢵⢥⢝⢽⢽⢽⢿⢅⣽⣿⢿⣿⢿⢽⠿⢍⢕⢽⢕⢵⢕⢥⢵⢴⢽⢽⢝⢽⢝⢽⢽⢽⢝⢽⠝⢡⢽⢽⠍⢵⠍⠙⠝⠝⠝⠝⠝⠝⠝⠝⠝⠅
      ⠀⠁⠉⠉⠙⠙⠙⠙⠗⢽⣿⣿⢿⣽⢿⢽⢟⢽⠍⢵⠍⢽⢝⢽⢝⢽⠝⠽⠝⠝⢁⢥⢕⢥⢕⢵⢝⢽⢽⢽⢕⢥⢵⢽⢽⢽⢝⢽⢝⢽⢽⢽⠝⠀
               ⠈⢭⣭⢝⠽⢝⢽⢝⢽⢕⢥⢕⢝⢽⢽⢽⢽⢝⢵⢝⢽⢽⢽⢽⢽⠽⠝⠙⠙⠉⢉⢉⢉⠉⠙⠙⠙⠝⠽⠝⠽⠝⠉⠁
                ⠙⢽⢽⢵⢍⢙⢙⢙⠁⢴⠙⢽⢵⢝⢝⢽⢝⠽⠝⠙⢉⢁⢥⢴⢔⢴⢝⢽⢽⢽⢝⢽⢝⢽⢝⢵⢕⢴⢴⠄
                  ⠉⠙⠝⢽⢽⢽⢕⢴⢜⠽⠝⠙⠀⢁⢅⢴⢴⢥⠀⢽⢝⢽⢽⢽⢽⢽⢽⢽⢝⢽⢝⢽⢝⢽⢝⢽⠝⠁
                     ⠀⠁⠁⠁⠁⠀⠀⠀⠀⠁⠀⠙⢽⢝⢽⢵⠈⠹⢽⢝⢽⢝⢵⢝⢽⢝⢽⢽⢽⢽⢽⢝⠝⠁
                                 ⠈⠙⢽⢝⢵⢄⠙⠝⢽⢝⢽⢝⢽⢝⢽⢝⢽⢝⠝⠉⠀
                                   ⠀⠙⢽⢽⢵⢥⢌⠙⠝⠝⠝⠝⠝⠙⠉⠁
                                     ⠙⢿⢽⣿⣿⣅
                                      ⠘⢿⣿⣿⣿⣧
```

MEGABRAIN detects the coding agents you already use, installs a curated set of
open-source tools that cut token usage and give your agents persistent memory, and
creates a plain-Markdown **memory vault** you own. It is reversible: a safe
uninstaller removes only what it installed.

## Quick start

```bash
curl -fsSL https://raw.githubusercontent.com/eduardoruisjbv/Megabrain/main/install.sh | bash
```

Or clone and inspect it first (recommended):

```bash
git clone https://github.com/eduardoruisjbv/Megabrain.git
cd Megabrain
bash install.sh
```

Want to see what it looks like **without installing anything?**

```bash
python3 lib/ui.py --demo              # install experience
python3 lib/ui.py --demo --installed  # "already installed" + uninstall flow
bash install.sh --dry-run --no-anim   # exact list of steps it would run
```

## What you get

| Component | What it does | Installed for |
|---|---|---|
| [**RTK**](https://github.com/rtk-ai/rtk) | Compresses command output before it reaches the model (typically 60–90% fewer tokens on `grep`, `git`, `ls`…) | every detected agent that supports hooks |
| [**graft**](https://www.npmjs.com/package/@nanonets/graft) | A graph of your repo (symbols, callers, spans) so agents read less code | MCP server for Claude Code and Codex; `graft init` per repo |
| [**codebase-memory-mcp**](https://github.com/DeusData/codebase-memory-mcp) | Structural code knowledge graph (SQLite) with search, tracing and impact analysis | every client it supports |
| [**claude-mem**](https://github.com/thedotmack/claude-mem) | Persistent memory across sessions | Claude Code |
| [**superpowers**](https://github.com/anthropics/claude-plugins-official) | Process skills (brainstorming, debugging, planning…) | Claude Code |
| [**ECC**](https://github.com/affaan-m/ECC) | Agents, skills and hooks (profile `standard`) | Claude Code |
| [**text-to-cad**](https://github.com/earthtojake/text-to-cad) | Local CAD workflows and viewer for generating STEP, GLB, STL and 3MF models | Codex and Claude Code |
| [**claude-code-setup**](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-code-setup) | Read-only, project-specific recommendations for Claude Code hooks, skills, MCP servers and agents | Claude Code |
| **Memory vault** | Plain-Markdown vault (PARA layout), mirrored from your agents' memories every 48h | you |
| [**Obsidian**](https://obsidian.md) *(optional)* | Visualize the vault as a graph | asked at the end |

### Supported agents

Detected automatically — nothing to configure:

`claude` · `codex` · `gemini` · `cursor` · `windsurf` · `opencode` · `kilocode` ·
`antigravity` · `hermes` · `kiro` · `droid` · `vibe` · `pi` · `copilot` · `cline`

```bash
bash install.sh --list-agents          # what was detected
bash install.sh --agents claude,codex  # force a list
```

## The memory vault

Always created — with or without Obsidian — at `~/.megabrain/vault` (a hidden folder).
It is just Markdown, so it works with Obsidian, VS Code, Logseq, or `cat`.

```
~/.megabrain/vault/
├── 00-Inbox/            quick capture
├── 01-Projetos/         work with a beginning and an end
├── 02-Áreas/            ongoing responsibilities
├── 03-Recursos/IA/      ← your agents' memories are mirrored here (Claude/, Codex/, Gemini/)
├── 04-Arquivo/          finished
├── Diário/Logs de IA/   what each AI session did
├── Templates/           project, AI-log and spec templates
├── .obsidian/           graph view pre-configured
└── MAPA.md  AGENTS.md  README.md
```

A sync job (systemd user timer, launchd or cron — whichever your system has) copies
new or changed memories every 48 hours. Run it now with `megabrain sync`.

To open it in Obsidian: **Open folder as vault → `~/.megabrain/vault` → Graph view**.

## Already installed? Uninstall

Run the installer again (or `megabrain`). MEGABRAIN knows it is installed and asks
what you want to do:

```
  MEGABRAIN already installed
  v1.0.2 · installed 2026-10-20 · claude, codex
  removes only what MEGABRAIN installed · your vault is kept

  Uninstall MEGABRAIN?   [ ○ Yes ]  [ ● No ]
```

```bash
megabrain status                     # what is installed, and what MEGABRAIN owns
megabrain uninstall                  # interactive
bash uninstall.sh -y                 # no questions; vault is kept
bash uninstall.sh -y --purge-vault   # also delete the vault
```

**Uninstall is conservative by design.** MEGABRAIN records, per component, whether
*it* installed it or it was already on your machine:

| Situation | On uninstall |
|---|---|
| Installed by MEGABRAIN | removed |
| Already on your machine before | **left untouched** |
| Memory vault | **kept** unless you confirm or pass `--purge-vault` |
| Code indexes (codebase-memory) | **kept** |
| claude-mem data | **kept** |

## Options

| Option | Description |
|---|---|
| `uninstall` · `status` · `sync` · `version` | subcommands |
| `--agents a,b` | skip detection, use this list |
| `--skip <item>` / `--only <item>` | `rtk graft cbm claude-mem superpowers ecc text-to-cad claude-code-setup vault deps obsidian` |
| `--obsidian yes\|no` | answer the Obsidian question without asking |
| `--vault-dir <dir>` | vault location (default `~/.megabrain/vault`) |
| `--language <lang>` | answer language for Claude Code |
| `--force` | reinstall even if already installed |
| `--purge-vault` | with `uninstall`: also delete the vault |
| `--no-deps` | never install curl/git/node/npm with the package manager |
| `--no-anim` | plain text output |
| `--dry-run` | show what would happen, change nothing |
| `-y`, `--yes` | no confirmations |

## Privacy and safety

- **Nothing is copied between machines.** No chat history, memories, tokens, indexes
  or personal paths are part of this project; each tool generates its own config.
- **Detection only checks that commands and folders exist.** It never reads their
  contents.
- **Your files are backed up before they change** (`settings.json.bak-<timestamp>`)
  and vault seed files are written only if missing.
- **Everything is logged** to `~/.megabrain/logs/` so you can audit exactly what ran.
- **Third-party tools keep their own policies.** For example, graft ships with
  anonymous usage telemetry on; disable it with `graft telemetry disable`.
- **text-to-cad telemetry:** cadgen sends anonymous usage statistics and crash
  reports by default; disable them with `uvx cadgen telemetry off`. Its CAD
  runtime is downloaded by `uv` the first time the plugin is used.
- **Claude Code setup is read-only:** it recommends automations for the current
  project and does not change project files.
- Read the script before running it — it is one readable file: [`install.sh`](install.sh).

## Compatibility

| System | Status |
|---|---|
| Fedora / Nobara (dnf) | tested end-to-end in a sandbox |
| Debian / Ubuntu (apt) · Arch (pacman) · openSUSE (zypper) · Alpine (apk) · Void (xbps) | supported by design, not yet verified — [issues welcome](https://github.com/eduardoruisjbv/Megabrain/issues) |
| macOS Intel (Homebrew) | tested end-to-end by the author |
| macOS Apple Silicon | supported by design, not yet verified |
| Windows | use WSL |
| Immutable systems (rpm-ostree, NixOS) | system packages are not installed automatically; install `curl git nodejs` yourself |

Requirements: `bash`, `curl`, `git`. `node`/`npm` are needed for graft and Claude
plugins; the corresponding Codex or Claude Code CLI is needed for its plugins.
`uv` downloads text-to-cad's CAD runtime on first use. `python3` is only needed
for the animation (plain text is used otherwise).
Missing dependencies are installed through your package manager after asking.

## How it works

One Bash engine drives everything and streams events to a small Python renderer;
a manifest tracks what it owns. See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Troubleshooting

- **Something failed:** open the log path printed at the end
  (`~/.megabrain/logs/install-<timestamp>.log`).
- **Command not found after install:** add `export PATH="$HOME/.local/bin:$PATH"` to
  your shell rc file.
- **Agents do not see the tools:** restart them; hooks and MCP servers load on new
  sessions.
- **No animation:** it needs a terminal and `python3`; use `--no-anim` for plain text.

## Versioning

[Semantic Versioning](https://semver.org). The version lives in [`VERSION`](VERSION),
every release is tagged `vX.Y.Z`, and changes are listed in [`CHANGELOG.md`](CHANGELOG.md).
Pin the latest published release with `MEGABRAIN_REF=v1.0.1`.

## Credits

MEGABRAIN stands on the shoulders of [RTK](https://github.com/rtk-ai/rtk),
[graft](https://www.npmjs.com/package/@nanonets/graft),
[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp),
[claude-mem](https://github.com/thedotmack/claude-mem),
[superpowers](https://github.com/anthropics/claude-plugins-official),
[ECC](https://github.com/affaan-m/ECC),
[text-to-cad](https://github.com/earthtojake/text-to-cad),
[claude-code-setup](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-code-setup)
and [Obsidian](https://obsidian.md).
It only orchestrates their official installers; all credit belongs to their authors.

## License

[MIT](LICENSE) © 2026 eduardoruisjbv
