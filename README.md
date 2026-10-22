<div align="center">

# 🧠 MEGABRAIN

**One command that gives every AI coding agent on your machine token-saving tools and a long-term memory vault.**

![Version](https://img.shields.io/badge/version-1.1.0-blue)
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
open-source tools that cut token usage, provide shared agent memory, and create
a plain-Markdown **knowledge vault** you own. It is reversible: a safe
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
| [**Hermes Agent**](https://github.com/NousResearch/hermes-agent) | Installs the official stable CLI, connects available repository MCPs and adds a vault context skill | default automatic detection, or explicit `--agents hermes` |
| [**ai-memory**](https://github.com/akitaonrails/ai-memory) | Shared agent memory with lifecycle capture, search and handoffs; pinned to v3.1.0 | detected supported agents, including Claude Code, Codex and Hermes |
| [**RTK**](https://github.com/rtk-ai/rtk) | Compresses command output before it reaches the model (typically 60–90% fewer tokens on `grep`, `git`, `ls`…) | every detected agent that supports hooks |
| [**graft**](https://www.npmjs.com/package/@nanonets/graft) | A graph of your repo (symbols, callers, spans) so agents read less code | MCP server for Claude Code, Codex and Hermes; `graft init` per repo |
| [**codebase-memory-mcp**](https://github.com/DeusData/codebase-memory-mcp) | Structural code knowledge graph (SQLite) with search, tracing and impact analysis | every client it supports |
| [**superpowers**](https://github.com/anthropics/claude-plugins-official) | Process skills (brainstorming, debugging, planning…) | Claude Code |
| [**ECC**](https://github.com/affaan-m/ECC) | Agents, skills and hooks (profile `standard`) | Claude Code |
| [**text-to-cad**](https://github.com/earthtojake/text-to-cad) | Local CAD workflows and viewer for generating STEP, GLB, STL and 3MF models | Codex and Claude Code |
| [**claude-code-setup**](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-code-setup) | Read-only, project-specific recommendations for Claude Code hooks, skills, MCP servers and agents | Claude Code |
| [**REA**](https://github.com/morluto/rea) | Reverse engineering workflows, MCP registrations and agent skill | detected supported agents (including Codex, Claude Code and Claude Desktop) |
| [**Playwright**](https://github.com/microsoft/playwright-mcp) | Browser MCP with isolated, headless sessions; reuses Chrome/Chromium or downloads matching Chromium | Codex, Claude Code and Hermes |
| [**Firecrawl**](https://docs.firecrawl.dev/mcp-server) | Keyless HTTP MCP for web search, scraping and parsing, within daily limits | Codex, Claude Code and Hermes |
| [**Mimic**](https://github.com/littledivy/mimic) | API capture analysis and Python client generation; CLI, proxy runtime cache and task skill | Codex and Claude Code |
| [**Open Code Review**](https://github.com/alibaba/open-code-review) | Review CLI and official native plugins; delegated review uses the current agent without an extra LLM key | Codex and Claude Code |
| **Mac SSH runner** | Persistent Claude/Codex jobs, explicit context, progress, results and resume on your Mac | Codex and Claude Code; user-configured SSH alias |
| [**Security Audit**](https://github.com/cloudflare/security-audit-skill) | Cloudflare's security guidance and multi-phase code-audit skill, including validators | Codex and Claude Code |
| [**Claude-Red**](https://github.com/SnailSploit/claude-red) | Security methodology library (79 skills at the pinned revision) | Codex and Claude Code |
| **Automatic skill selection** | Persistent guidance to select relevant installed skills without naming them in each prompt | Codex, Claude Code and Hermes |
| **Knowledge vault** | Plain-Markdown vault (PARA layout) for your notes and references; separate from agent memory | you |
| [**Obsidian**](https://obsidian.md) *(optional)* | Visualize the vault as a graph | asked at the end |

### Supported agents

Detected automatically (individual tools and native plugins support different clients):

`claude` · `codex` · `gemini` · `cursor` · `windsurf` · `opencode` · `kilocode` ·
`antigravity` · `hermes` · `kiro` · `droid` · `vibe` · `pi` · `copilot` · `cline`

```bash
bash install.sh --list-agents          # what was detected
bash install.sh --agents claude,codex  # force a list
```

### Hermes installation and integration

With automatic detection, MEGABRAIN also installs Hermes if it is absent, using
the [official stable source installer](https://hermes-agent.nousresearch.com/docs/getting-started/installation)
with `--non-interactive`. This includes Hermes' default browser/computer-use
dependencies. `--skip hermes` skips this bootstrap and core setup; an explicit
`--agents` list is authoritative, so include `hermes` when you want it configured.

```bash
bash install.sh -y --agents hermes --only hermes --only ai-memory --only vault --only skills-auto
# Add any other desired components, e.g. --only playwright --only firecrawl
hermes mcp list
hermes skills list
ai-memory doctor
```

The core integration registers installed graft and codebase-memory MCPs. Selected
Playwright/Firecrawl components also register with Hermes. The compatible curated
Markdown collections, Mimic and Mac runner skills install into `~/.hermes/skills`;
Open Code Review uses its CLI and a Hermes skill. Native Claude/Codex plugins
(including Knowledge Work) are not loaded into Hermes. ai-memory configures
Hermes hooks and MCP through its supported interfaces. It installs the Hermes
skills and preserves Hermes' hook acceptance setting. If Hermes asks to accept
the hooks, approve them when it starts. Codex may mark its hooks as untrusted.
Open Codex, run `/hooks`, and trust the ai-memory hooks before capture can start.

The `megabrain` skill points Hermes at your selected vault and instructs it to
retrieve only relevant notes from the knowledge vault. Agent memory is managed
by ai-memory. The old scheduled mirror stops during migration. Existing vault
notes and archived mirror files stay in place. `HERMES_HOME` is respected.

Authentication remains a user login: use `hermes auth add PROVIDER`, then
`hermes model` to choose the model. A new runtime disables adoption of other
CLIs' logins; existing provider settings and credentials are preserved. Installing
MEGABRAIN does not make a model request, authorize paid usage or start a messaging
gateway. Skill-selection guidance is appended to Hermes' existing `SOUL.md`.

Uninstall removes only unchanged MCP settings and skills that MEGABRAIN created.
It removes Hermes itself only if MEGABRAIN installed it and its launcher/version
still match; Hermes' normal uninstall keeps configuration, memories and logins.

## The knowledge vault

Always created — with or without Obsidian — at `~/.megabrain/vault` (a hidden folder).
It is just Markdown, so it works with Obsidian, VS Code, Logseq, or `cat`.

```
~/.megabrain/vault/
├── 00-Inbox/            quick capture
├── 01-Projetos/         work with a beginning and an end
├── 02-Áreas/            ongoing responsibilities
├── 03-Recursos/IA/      ← your curated AI references and archived mirror files
├── 04-Arquivo/          finished
├── Diário/Logs de IA/   what each AI session did
├── Templates/           project, AI-log and spec templates
├── .obsidian/           graph view pre-configured
└── MAPA.md  AGENTS.md  README.md
```

Agent memory runs through ai-memory. The vault remains an independent Markdown
knowledge store. Migration stops the old 48-hour mirror and keeps its existing
files in place.

To open it in Obsidian: **Open folder as vault → `~/.megabrain/vault` → Graph view**.

## Already installed? Uninstall

Run the installer again (or `megabrain`). MEGABRAIN knows it is installed and asks
what you want to do:

```
  MEGABRAIN already installed
  v1.1.0 · installed 2026-10-21 · claude, codex
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
| Existing vault notes and archived mirror files | **kept** |

## Options

| Option | Description |
|---|---|
| `uninstall` · `status` · `version` | subcommands |
| `--agents a,b` | skip detection, use this list |
| `--skip <item>` / `--only <item>` | `ai-memory hermes rtk graft cbm rea superpowers ecc text-to-cad claude-code-setup playwright firecrawl mimic open-code-review mac-agent security-audit claude-red skills-auto vault deps obsidian` |
| `--obsidian yes\|no` | answer the Obsidian question without asking |
| `--vault-dir <dir>` | vault location (default `~/.megabrain/vault`) |
| `--language <lang>` | answer language for Claude Code |
| `--force` | reinstall even if already installed |
| `--purge-vault` | with `uninstall`: also delete the vault |
| `--no-deps` | never install system dependencies or bootstrap uv; selected tool packages still install |
| `--no-anim` | plain text output |
| `--dry-run` | show what would happen, change nothing |
| `-y`, `--yes` | no confirmations |

## Browser, web and review integrations

The new integrations use the native **Codex and Claude Code CLIs**. They do not
edit Claude Desktop configuration. Add the complete set to an existing install:

```bash
bash install.sh --force --agents claude,codex \
  --only playwright --only firecrawl --only mimic --only open-code-review \
  --only mac-agent --only security-audit --only claude-red --only skills-auto
```

Playwright MCP is pinned to `0.0.83`. It uses an existing Chrome/Chromium when
available; otherwise the installer downloads matching Chromium. On minimal Linux
systems, missing browser system libraries may need to be installed separately.
It registers headless, isolated sessions; no existing browser profile is imported.
This installs the MCP server, not a `@playwright/test` dependency in your projects.

Firecrawl uses `https://mcp.firecrawl.dev/v2/mcp`, with keyless Search, Scrape and
Parse within daily limits. Sign in to Firecrawl separately for the full tool set
or higher limits. No account credentials are embedded in this project.

Mimic installs from a fixed Git revision using `uv`, with Python 3.13 downloaded
when necessary. The mitmproxy runtime is cached, but no proxy, traffic capture,
certificate installation or app instrumentation starts during installation.
Use existing HAR/cURL data when appropriate. For Codex, `mimic gen HOST --har FILE
--prompt-only` lets the current agent generate the client; Claude generation also
works through Mimic's CLI. Capture and replay still require task authorization.

Open Code Review installs CLI `1.13.2` and the official Codex/Claude plugins from
Alibaba's marketplace. Plugins follow that marketplace's revision. Delegated
review uses the host agent; a separate LLM endpoint is optional. Existing commands,
registrations and plugins are preserved. Native ownership and their installation
signatures are recorded in `state/integrations.json`; uninstall keeps modified
entries. Shared dependencies, browser caches and marketplace catalogs are retained.

## Run tasks on your Mac

The installer sets up the **local client and skill only**. Enable Remote Login
on your Mac and establish key-based SSH access using an alias in `~/.ssh/config`.
Test `ssh YOUR_SSH_ALIAS` yourself first; do not disable host-key checks. The Mac
needs Python 3.8+, Git, and authenticated Codex/Claude Code commands in
`~/.local/bin`, Homebrew's bin directory, or its SSH PATH.

```bash
megabrain mac configure YOUR_SSH_ALIAS
megabrain mac setup             # explicitly copies the public worker to the Mac
megabrain mac doctor            # confirms installed agents and authentication
megabrain mac start codex --prompt 'Implement the requested change' --context-file context.md
megabrain mac start claude --prompt 'Review the implementation' --cwd /remote/project
megabrain mac status JOB_ID
megabrain mac logs JOB_ID
megabrain mac result JOB_ID
megabrain mac resume JOB_ID --prompt 'Now run the relevant checks'
megabrain mac fetch JOB_ID --output ./new-task-export
megabrain mac stop JOB_ID
```

`mac-agent` is also installed as a convenience command if that name is free.
`megabrain mac` always selects MEGABRAIN's own runtime. The alias is stored locally
in `~/.config/megabrain/mac-agent.json`; no SSH keys or account tokens are copied.
Use `configure --python /path/to/python3 YOUR_SSH_ALIAS` for another remote Python.

Each job starts in a new remote Git workspace unless you give an existing Mac
directory with `--cwd`. Prompts and explicit context files travel as JSON over
SSH. There is no automatic chat-history or source-tree synchronization. Use Git
and separate worktrees for parallel code edits. `fetch` exports task records, not
project files. Claude accepts edits but still requires permission for commands;
`--allow-tool 'Bash(npm test*)'` can authorize a specific pattern for a task. Codex
uses its workspace-write sandbox; neither agent bypasses all permissions.

Jobs persist after SSH disconnects. The Mac must remain awake and connected.
Builds and tests use the Mac's CPU/RAM; hosted model inference still runs at the
provider. Uninstall removes only managed local files and keeps your SSH settings,
local host configuration, remote worker and remote jobs.

## Security skills and automatic selection

The `security-audit`, `claude-red`, and `skills-auto` components are installed for
detected Codex and Claude Code clients. To add just these components to an existing
MEGABRAIN installation:

```bash
bash install.sh --force --agents claude,codex \
  --only security-audit --only claude-red --only skills-auto --no-anim
```

Use `--skip security-audit`, `--skip claude-red`, or `--skip skills-auto` to omit a
component. These steps require **Python 3.8+** and use only its standard library.
The installer downloads public, commit-pinned archives; it never executes their
skill content. Missing or oversized discovery headers in the pinned Claude-Red
collection are adapted locally while retaining the upstream text. Complete skill
directories and upstream licenses are kept in MEGABRAIN's state directory and
linked into the supported clients' skill roots. Existing skills are preserved.

`skills-auto` adds a bounded instruction block to the agents' global instructions,
enables implicit invocation in installed personal/enabled-plugin skill metadata,
and raises Claude Code's skill-catalog budget to at least 3%. It honors
`CODEX_HOME` and keeps built-in `.system` skills and disabled plugins unchanged.
No model endpoint or API key is required for this configuration.

Skills are selected **when relevant to a task**, rather than executing every
installed skill on every prompt. Selection remains an agent decision. Full audits
follow the audit skill's triggering conditions; installing a skill does not start
a scan, capture, exploit, or remote operation. Normal permissions still apply.
Start a new agent session to load the updated catalog and instructions.

The separate ownership ledger, `~/.megabrain/state/skills.json`, survives forced
and selected-component reinstalls. Uninstall removes unchanged managed copies and
links, restores unchanged configuration from private backups, and keeps modified
files. The log reports `kept_modified` when manual reconciliation is needed;
backups and the ownership ledger are retained in that case.

## Privacy and safety

- **No private machine state is distributed.** No chat history, memories, tokens,
  indexes or personal host details are part of this project. Mac jobs transmit
  only the prompts/context explicitly supplied through the remote client.
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
- **REA setup:** after the MEGABRAIN confirmation, `rea setup --yes --all-detected`
  configures detected supported clients. MEGABRAIN does not install Hopper. On
  uninstall, `rea uninstall` runs only if MEGABRAIN configured REA; pre-existing
  REA registrations and skills are left untouched, and REA data is kept.
- **Security skills:** only public skill definitions are downloaded. No local
  projects, findings, accounts, histories, or credentials are included or uploaded.
  `skills-auto` changes selection metadata and routing guidance, not execution
  permissions. Existing and subsequently modified skills are preserved.
- Read the engine and Python helpers before running them: [`install.sh`](install.sh)
  and [`lib/`](lib/).

## Compatibility

| System | Status |
|---|---|
| Fedora / Nobara (dnf) | tested end-to-end in a sandbox |
| Debian / Ubuntu (apt) · Arch (pacman) · openSUSE (zypper) · Alpine (apk) · Void (xbps) | supported by design, not yet verified — [issues welcome](https://github.com/eduardoruisjbv/Megabrain/issues) |
| macOS Intel (Homebrew) | tested end-to-end by the author |
| macOS Apple Silicon | supported by design, not yet verified |
| Windows | use WSL |
| Immutable systems (rpm-ostree, NixOS) | system packages are not installed automatically; install `curl git nodejs` yourself |

Requirements: `bash`, `curl`, `git`. Modern `node`/`npm` (Node 20+ recommended) are
needed for graft, REA, Playwright, Open Code Review and
Claude plugins; the corresponding Codex or Claude Code CLI is needed for its plugins.
`uv` downloads text-to-cad's CAD runtime on first use. Python 3.8+ is required for
the new integration, security-skill and automatic-selection components. Mimic
requires `uv` (bootstrapped unless `--no-deps`) and a managed Python 3.13. SSH is
required when using the Mac client. Python is also used by the
optional animation (plain text is used otherwise).
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
Pin the memory migration release with `MEGABRAIN_REF=v1.2.0` after publication.

## Credits

MEGABRAIN stands on the shoulders of [RTK](https://github.com/rtk-ai/rtk),
[graft](https://www.npmjs.com/package/@nanonets/graft),
[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp),
[ai-memory](https://github.com/akitaonrails/ai-memory),
[superpowers](https://github.com/anthropics/claude-plugins-official),
[ECC](https://github.com/affaan-m/ECC),
[text-to-cad](https://github.com/earthtojake/text-to-cad),
[claude-code-setup](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-code-setup),
[REA](https://github.com/morluto/rea),
[Playwright MCP](https://github.com/microsoft/playwright-mcp),
[Firecrawl](https://www.firecrawl.dev/),
[Mimic](https://github.com/littledivy/mimic),
[Open Code Review](https://github.com/alibaba/open-code-review),
[Cloudflare Security Audit](https://github.com/cloudflare/security-audit-skill),
[Claude-Red](https://github.com/SnailSploit/claude-red), and [Obsidian](https://obsidian.md).
It orchestrates their public installers and skill definitions; all credit belongs
to their authors.

## License

[MIT](LICENSE) © 2026 eduardoruisjbv
