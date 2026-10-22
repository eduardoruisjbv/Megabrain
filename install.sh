#!/usr/bin/env bash
# MEGABRAIN - universal installer / uninstaller
# https://github.com/eduardoruisjbv/Megabrain
#
# Detects the coding agents installed on this machine (Claude Code, Codex,
# Gemini, Cursor, ...) and sets up a token-saving + memory stack for all of
# them: ai-memory, RTK, graft, codebase-memory-mcp, REA, text-to-cad for Codex
# and Claude Code, plus plugins and setup guidance. Always creates a separate
# plain-Markdown knowledge vault and then offers Obsidian.
#
# Privacy: no private state is imported from another machine. The script only
# checks that agent commands/folders EXIST, installs public tools and lets each
# one generate its own configuration. No history, memories, tokens or personal
# paths are ever included.
#
# Usage:
#   bash install.sh                  install (or show status if already installed)
#   bash install.sh uninstall        remove what MEGABRAIN installed
#   bash install.sh status           show what is installed
#   megabrain mac --help              run persistent Codex/Claude jobs on your Mac
#   bash install.sh --list-agents    show detected agents and exit
#
# Options:
#   --agents a,b,c       skip detection and use this list (e.g. claude,codex)
#   --skip <item>        skip: ai-memory hermes rtk graft cbm rea superpowers ecc text-to-cad claude-code-setup playwright firecrawl mimic open-code-review mac-agent security-audit claude-red design-skills writing-skills workflow-skills skills-auto vault deps obsidian
#   --only <item>        install only this item (repeatable)
#   --language <lang>    answer language for Claude Code (default: unchanged)
#   --vault-dir <dir>    vault location (default: ~/.megabrain/vault, hidden)
#   --obsidian yes|no    answer the Obsidian question without asking
#   --purge-vault        uninstall: also delete the memory vault
#   --force              install even if MEGABRAIN is already installed
#   --no-deps            do not install system dependencies or bootstrap uv
#   --no-anim            plain text output (no animation)
#   --dry-run            show what would happen, change nothing
#   -y, --yes            do not ask for confirmation
#   --version            print the version
#   -h, --help           this help

set -uo pipefail

MB_VERSION="1.2.0"
AI_MEMORY_VERSION="3.1.0"
MB_REPO="eduardoruisjbv/Megabrain"
MB_REF="${MEGABRAIN_REF:-main}"
MB_RAW="https://raw.githubusercontent.com/${MB_REPO}/${MB_REF}"
MB_HOME="${MEGABRAIN_HOME:-$HOME/.megabrain}"
MANIFEST="$MB_HOME/manifest.env"

RTK_INSTALLER="https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh"
CBM_INSTALLER="https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh"

# ---------- locate ourselves (works when piped, run directly or via symlink) ----------
SELF=""; SELF_DIR=""
_src="${BASH_SOURCE[0]:-}"
if [ -n "$_src" ] && [ -f "$_src" ]; then
  while [ -L "$_src" ]; do
    _t="$(readlink "$_src")"
    case "$_t" in /*) _src="$_t" ;; *) _src="$(dirname "$_src")/$_t" ;; esac
  done
  SELF="$_src"; SELF_DIR="$(cd "$(dirname "$_src")" 2>/dev/null && pwd)"
  [ -f "$SELF_DIR/VERSION" ] && MB_VERSION="$(head -1 "$SELF_DIR/VERSION" | tr -d '[:space:]')"
fi

# ---------- options ----------
CMD="install"; DRY=0; YES=0; FORCE=0; NO_ANIM=0; LIST_ONLY=0; PURGE_VAULT=0
LANGUAGE=""; AGENTS_OVERRIDE=""; OBSIDIAN_MODE="ask"; SKIP=" "; ONLY=" "
VAULT_DIR="${MEGABRAIN_VAULT:-$MB_HOME/vault}"
VAULT_DIR_OVERRIDE=0
[ -n "${MEGABRAIN_VAULT:-}" ] && VAULT_DIR_OVERRIDE=1

MAC_ARGS=()
if [ "${1:-}" = mac ]; then
  CMD=mac; shift; MAC_ARGS=("$@"); set --
fi
if [ $# -gt 0 ]; then
  case "$1" in
    install|uninstall|status|sync|version|help|mark-installed) CMD="$1"; shift ;;
  esac
fi
while [ $# -gt 0 ]; do
  case "$1" in
    --uninstall) CMD="uninstall" ;;
    --status) CMD="status" ;;
    --version|-V) CMD="version" ;;
    --mark-installed) CMD="mark-installed" ;;
    --list-agents) LIST_ONLY=1 ;;
    --agents) AGENTS_OVERRIDE="$(printf '%s' "${2:-}" | tr ',' ' ')"; shift ;;
    --skip) SKIP="$SKIP${2:-} "; shift ;;
    --only) ONLY="$ONLY${2:-} "; shift ;;
    --language) LANGUAGE="${2:-}"; shift ;;
    --vault-dir) VAULT_DIR="${2:-}"; VAULT_DIR_OVERRIDE=1; shift ;;
    --obsidian) OBSIDIAN_MODE="${2:-ask}"; shift ;;
    --purge-vault) PURGE_VAULT=1 ;;
    --force) FORCE=1 ;;
    --no-deps) SKIP="${SKIP}deps " ;;
    --no-anim) NO_ANIM=1 ;;
    --dry-run) DRY=1 ;;
    -y|--yes) YES=1 ;;
    -h|--help) CMD="help" ;;
    *) echo "Unknown option: $1 (try --help)" >&2; exit 2 ;;
  esac
  shift
done

want() { # want <item>
  [[ "$SKIP" == *" $1 "* ]] && return 1
  [ "$ONLY" = " " ] && return 0
  [[ "$ONLY" == *" $1 "* ]]
}

# ---------- logging / UI plumbing ----------
UI_ON=0; UI_PID=""; EV=""; ANS=""; LIB_DIR=""; SKILLS_LIB=""; INTEGRATIONS_LIB=""; CUR=""; STEP_FAILED=0
FAILED=""; LOGFILE="/dev/null"; PATH_ADDED=0

have() { command -v "$1" >/dev/null 2>&1; }
now_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }
emit() { [ "$UI_ON" = 1 ] || return 0; ( IFS=$'\t'; printf '%s\n' "$*" ) >> "$EV"; }
tolog() { printf '[%s] %s\n' "$(now_iso)" "$*" >> "$LOGFILE" 2>/dev/null; }

c() { # c <code> <text>   (colour only when plain output goes to a terminal)
  if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then printf '\033[%sm%s\033[0m' "$1" "$2"; else printf '%s' "$2"; fi
}
say()  { tolog "== $*"; [ "$UI_ON" = 1 ] && return 0; printf '\n%s\n' "$(c '1;36' "==> $*")"; }
ok()   { tolog "ok: $*";    emit log "$CUR" "$*"; [ "$UI_ON" = 1 ] || printf '    %s  %s\n' "$(c 32 ok)" "$*"; }
warn() { tolog "warn: $*";  emit log "$CUR" "$*"; [ "$UI_ON" = 1 ] || printf '    %s  %s\n' "$(c 33 warn)" "$*"; }
fail() { tolog "FAIL: $*";  emit log "$CUR" "x $*"; STEP_FAILED=1; FAILED="$FAILED$*"$'\n'
         [ "$UI_ON" = 1 ] || printf '    %s  %s\n' "$(c 31 fail)" "$*"; }

S_begin() { # S_begin <key> <label> [context]
  CUR="$1"; STEP_FAILED=0; emit begin "$1" "${3:-}"; say "$2"
}
S_end()  { if [ "$STEP_FAILED" = 1 ]; then emit fail "$CUR"; else emit done "$CUR"; fi; }
S_skip() { emit skip "$1" "${2:-skipped}"; tolog "skip $1: ${2:-}"
           [ "$UI_ON" = 1 ] || printf '\n%s  %s\n' "$(c 2 "-- $1")" "${2:-skipped}"; }

run_logged() { # run a command, send its output to the log, never touch the screen
  if [ "$DRY" = 1 ]; then tolog "[dry-run] $*"; printf '    %s %s\n' "$(c 2 '[dry-run]')" "$*"; return 0; fi
  tolog "\$ $*"
  "$@" >>"$LOGFILE" 2>&1 </dev/null
}

fetch_and_run() { # fetch_and_run <url> <interpreter> [args...]
  local url="$1" interp="$2"; shift 2
  if [ "$DRY" = 1 ]; then printf '    %s download %s and run with %s\n' "$(c 2 '[dry-run]')" "$url" "$interp"; return 0; fi
  local tmp rc; tmp="$(mktemp "${TMPDIR:-/tmp}/megabrain-dl.XXXXXX")" || return 1
  if curl -fsSL --max-time 120 "$url" -o "$tmp" >>"$LOGFILE" 2>&1; then
    "$interp" "$tmp" "$@" >>"$LOGFILE" 2>&1 </dev/null; rc=$?
  else rc=1; fi
  rm -f "$tmp"; return $rc
}

tty_ok() { [ -r /dev/tty ] && ( : </dev/tty ) 2>/dev/null; }

ask_toggle() { # ask_toggle <question> <default yes|no>  -> 0 = yes
  tty_ok || return 1
  local choice=0 key rest q="$1"
  [ "${2:-no}" = yes ] && choice=1
  while true; do
    if [ "$choice" = 1 ]; then
      printf '\r    %s  \033[1;7;32m[ ● Yes ]\033[0m  \033[2m[ ○ No ]\033[0m   ' "$q" >/dev/tty
    else
      printf '\r    %s  \033[2m[ ○ Yes ]\033[0m  \033[1;7;33m[ ● No ]\033[0m   ' "$q" >/dev/tty
    fi
    IFS= read -rsn1 key </dev/tty
    case "$key" in
      $'\x1b') IFS= read -rsn2 -t 0.1 rest </dev/tty; case "$rest" in '[C'|'[D'|'OC'|'OD') choice=$((1 - choice)) ;; esac ;;
      y|Y|s|S) choice=1 ;;
      n|N)     choice=0 ;;
      ' '|$'\t') choice=$((1 - choice)) ;;
      '') break ;;
    esac
  done
  printf '\n' >/dev/tty
  [ "$choice" = 1 ]
}

ui_wait_answer() { # ui_wait_answer <id> <default>
  local id="$1" def="$2" v=""
  while :; do
    if [ -s "$ANS" ]; then
      v="$(grep -E "^${id}"$'\t' "$ANS" 2>/dev/null | tail -1 | cut -f2)"
      [ -n "$v" ] && { printf '%s' "$v"; return; }
    fi
    kill -0 "$UI_PID" 2>/dev/null || { printf '%s' "$def"; return; }
    sleep 0.1
  done
}

ask_yes_no() { # ask_yes_no <id> <headline> <line1> <line2> <question> <default>  -> 0 = yes
  local id="$1" head="$2" l1="$3" l2="$4" q="$5" def="$6"
  if [ "$UI_ON" = 1 ]; then
    emit ask "$id" "$head" "$l1" "$l2" "$q" "$def"
    [ "$(ui_wait_answer "$id" "$def")" = yes ]
  else
    printf '\n  %s\n  %s\n  %s\n' "$(c 1 "$head")" "$l1" "$(c 2 "$l2")"
    ask_toggle "$q" "$def"
  fi
}

start_ui() { # start_ui <mode>
  [ "$UI_ON" = 1 ] && { emit mode "$1"; return 0; }
  [ "$DRY" = 0 ] && [ "$NO_ANIM" = 0 ] && [ -n "$LIB_DIR" ] || return 0
  [ -t 1 ] && have python3 && tty_ok && [ "${TERM:-dumb}" != dumb ] || return 0
  EV="$(mktemp "${TMPDIR:-/tmp}/megabrain-ev.XXXXXX")"; ANS="$(mktemp "${TMPDIR:-/tmp}/megabrain-an.XXXXXX")"
  python3 "$LIB_DIR/ui.py" --events "$EV" --answers "$ANS" --version "$MB_VERSION" --watch-pid $$ &
  UI_PID=$!; UI_ON=1
  emit mode "$1"
}
stop_ui() {
  [ "$UI_ON" = 1 ] || return 0
  wait "$UI_PID" 2>/dev/null
  UI_ON=0; rm -f "$EV" "$ANS"
}
abort_ui() {
  if [ "$UI_ON" = 1 ]; then emit quit; sleep 0.2; kill "$UI_PID" 2>/dev/null; wait "$UI_PID" 2>/dev/null; UI_ON=0; fi
}
on_signal() { abort_ui; printf '\nInterrupted. Run again to resume.\n' >&2; exit 130; }
trap on_signal INT TERM

ensure_lib() { # find (or download) ui.py + brain_energize.py
  local d
  for d in "$SELF_DIR/lib" "$SELF_DIR" "$MB_HOME/lib"; do
    if [ -n "$d" ] && [ -f "$d/ui.py" ] && [ -f "$d/brain_energize.py" ]; then LIB_DIR="$d"; return 0; fi
  done
  have curl || return 1
  local tmp; tmp="$(mktemp -d "${TMPDIR:-/tmp}/megabrain-lib.XXXXXX")" || return 1
  if curl -fsSL --max-time 30 "$MB_RAW/lib/ui.py" -o "$tmp/ui.py" 2>/dev/null \
     && curl -fsSL --max-time 30 "$MB_RAW/lib/brain_energize.py" -o "$tmp/brain_energize.py" 2>/dev/null; then
    LIB_DIR="$tmp"; return 0
  fi
  rm -rf "$tmp"; return 1
}

ensure_skills_lib() {
  local d tmp
  for d in "$SELF_DIR/lib" "$SELF_DIR" "$LIB_DIR" "$MB_HOME/lib"; do
    if [ -n "$d" ] && [ -f "$d/skills.py" ]; then SKILLS_LIB="$d/skills.py"; return 0; fi
  done
  have curl || return 1
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/megabrain-skills-lib.XXXXXX")" || return 1
  if curl -fsSL --max-time 30 "$MB_RAW/lib/skills.py" -o "$tmp/skills.py" >>"$LOGFILE" 2>&1; then
    SKILLS_LIB="$tmp/skills.py"; return 0
  fi
  rm -rf "$tmp"; return 1
}

ensure_integrations_lib() {
  local d tmp name complete
  for d in "$SELF_DIR/lib" "$SELF_DIR" "$MB_HOME/lib"; do
    [ -n "$d" ] || continue
    complete=1
    for name in integrations.py skills.py mac_agent.py mac_worker.py; do
      [ -f "$d/$name" ] || complete=0
    done
    if [ "$complete" = 1 ]; then INTEGRATIONS_LIB="$d/integrations.py"; SKILLS_LIB="$d/skills.py"; return 0; fi
  done
  have curl || return 1
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/megabrain-integrations-lib.XXXXXX")" || return 1
  for name in integrations.py skills.py mac_agent.py mac_worker.py; do
    if ! curl -fsSL --max-time 30 "$MB_RAW/lib/$name" -o "$tmp/$name" >>"$LOGFILE" 2>&1; then
      rm -rf "$tmp"; return 1
    fi
  done
  INTEGRATIONS_LIB="$tmp/integrations.py"; SKILLS_LIB="$tmp/skills.py"
}

copy_atomic() { # copy_atomic <src> <dest>   a new inode, so a running copy of a script keeps working
  [ "$1" = "$2" ] && return 0
  local tmp; tmp="$(mktemp "$(dirname "$2")/.mb-copy.XXXXXX")" || return 1
  cp "$1" "$tmp" || { rm -f "$tmp"; return 1; }
  chmod "$(stat -c %a "$1" 2>/dev/null || stat -f %Lp "$1")" "$tmp" 2>/dev/null
  mv "$tmp" "$2"
}

# ---------- manifest (how MEGABRAIN knows it is installed) ----------
mf_get() { [ -f "$MANIFEST" ] || return 0; sed -n "s/^$1=//p" "$MANIFEST" | head -1 | sed 's/^"//; s/"$//'; }
KEEP_OWNED=0
mf_put() { # mf_put KEY VALUE
  [ "$DRY" = 1 ] && return 0
  # On a reinstall or update, "already installed" must not erase the record
  # that an earlier MEGABRAIN run installed it, or uninstall would leave it.
  if [ "$KEEP_OWNED" = 1 ] && [ "$2" = 0 ]; then
    case "$1" in MANAGED_*) [ "$(mf_get "$1")" = 1 ] && return 0 ;; esac
  fi
  mkdir -p "$MB_HOME"
  local value="$2" agent
  if [ "$KEEP_OWNED" = 1 ] && [ "$1" = AGENTS ]; then
    for agent in $(mf_get AGENTS); do
      [[ " $value " == *" $agent "* ]] || value="$value $agent"
    done
  fi
  local tmp; tmp="$(mktemp "$MB_HOME/.manifest.XXXXXX")"
  { [ -f "$MANIFEST" ] && grep -v "^$1=" "$MANIFEST"; printf '%s="%s"\n' "$1" "$value"; } > "$tmp"
  mv "$tmp" "$MANIFEST"
}
mf_put_exact() { # mf_put_exact KEY VALUE, including an intentional ownership reset
  local keep="$KEEP_OWNED"
  KEEP_OWNED=0; mf_put "$1" "$2"; KEEP_OWNED="$keep"
}
is_installed() { [ -f "$MANIFEST" ] && [ "$(mf_get STATUS)" = "complete" ]; }

mf_reset_keep_owned() { # start a fresh manifest, carrying over what MEGABRAIN owns
  [ "$DRY" = 1 ] && return 0
  mkdir -p "$MB_HOME"
  local tmp; tmp="$(mktemp "$MB_HOME/.manifest.XXXXXX")"
  if [ -f "$MANIFEST" ]; then
    grep -E '^(MANAGED_[A-Za-z_]+|MCPADD_[A-Za-z_]+)="1"$|^(AGENTS|VAULT_DIR|SYNC_METHOD|UPDATE_METHOD|AUTO_UPDATE)=' "$MANIFEST" > "$tmp"
  fi
  mv "$tmp" "$MANIFEST"
}

SKILL_COMPONENTS="security-audit claude-red design-skills writing-skills workflow-skills"
INTEGRATIONS="ai-memory playwright firecrawl mimic open-code-review mac-agent hermes"

if [ "$VAULT_DIR_OVERRIDE" = 0 ] && [ -n "$(mf_get VAULT_DIR)" ]; then
  VAULT_DIR="$(mf_get VAULT_DIR)"
fi

present_list() {
  local out="environment,agents" k
  for k in ai_memory hermes rtk graft cbm rea_cli rea_setup claude_mem superpowers ecc text_to_cad claude_code_setup playwright firecrawl mimic open_code_review mac_agent knowledge_work security_audit claude_red design_skills writing_skills workflow_skills skills_auto vault wiring; do
    [ "$(mf_get "PRESENT_$k")" = 1 ] && out="$out,$(printf '%s' "$k" | tr '_' '-')"
  done
  printf '%s' "$out"
}

# ---------- system / agents ----------
OS_NAME="$(uname -s 2>/dev/null)"; ARCH="$(uname -m 2>/dev/null)"
DISTRO="$OS_NAME"
[ -r /etc/os-release ] && DISTRO="$(. /etc/os-release; printf '%s' "${PRETTY_NAME:-$NAME}")"

PM=""
for _p in apt-get dnf yum pacman zypper apk xbps-install brew; do have "$_p" && { PM="$_p"; break; }; done
[ -z "$PM" ] && have rpm-ostree && PM="rpm-ostree"
[ -z "$PM" ] && have nix-env && PM="nix"
SUDO=""; [ "$(id -u)" != 0 ] && have sudo && SUDO="sudo"

agent_probe() { # sets P_CMDS / P_DIRS (existence checks only, contents are never read)
  P_CMDS=""; P_DIRS=""
  case "$1" in
    claude)      P_CMDS="claude";              P_DIRS="$HOME/.claude" ;;
    codex)       P_CMDS="codex";               P_DIRS="$HOME/.codex" ;;
    gemini)      P_CMDS="gemini";              P_DIRS="$HOME/.gemini" ;;
    cursor)      P_CMDS="cursor cursor-agent"; P_DIRS="$HOME/.cursor" ;;
    windsurf)    P_CMDS="windsurf";            P_DIRS="$HOME/.codeium/windsurf" ;;
    opencode)    P_CMDS="opencode";            P_DIRS="$HOME/.config/opencode" ;;
    kilocode)    P_CMDS="kilocode";            P_DIRS="$HOME/.kilocode" ;;
    antigravity) P_CMDS="antigravity";         P_DIRS="$HOME/.gemini/antigravity" ;;
    hermes)      P_CMDS="hermes";              P_DIRS="$HOME/.hermes" ;;
    kiro)        P_CMDS="kiro";                P_DIRS="$HOME/.kiro" ;;
    droid)       P_CMDS="droid";               P_DIRS="$HOME/.factory" ;;
    vibe)        P_CMDS="vibe";                P_DIRS="$HOME/.vibe" ;;
    pi)          P_CMDS="pi";                  P_DIRS="$HOME/.pi" ;;
    copilot)     P_CMDS="copilot";             P_DIRS="$HOME/.copilot" ;;
    cline)       P_CMDS="";                    P_DIRS="$HOME/.cline" ;;
    *) return 1 ;;
  esac
}
ALL_AGENTS="claude codex gemini cursor windsurf opencode kilocode antigravity hermes kiro droid vibe pi copilot cline"
DETECTED=""
detect_agents() {
  DETECTED=""
  if [ -n "$AGENTS_OVERRIDE" ]; then DETECTED="$AGENTS_OVERRIDE"; return; fi
  local a x found
  for a in $ALL_AGENTS; do
    agent_probe "$a" || continue; found=0
    for x in $P_CMDS; do have "$x" && found=1; done
    for x in $P_DIRS; do [ -d "$x" ] && found=1; done
    [ "$found" = 1 ] && DETECTED="$DETECTED $a"
  done
  DETECTED="${DETECTED# }"
}
has_agent() { [[ " $DETECTED " == *" $1 "* ]]; }

install_pkgs() { # generic names: curl git node npm python3
  local real="" x
  for x in "$@"; do
    case "$PM:$x" in
      brew:npm|xbps-install:npm) ;;
      pacman:python3) real="$real python" ;;
      *:node) real="$real nodejs" ;;
      *) real="$real $x" ;;
    esac
  done
  # shellcheck disable=SC2086
  case "$PM" in
    apt-get) $SUDO apt-get update && $SUDO apt-get install -y ca-certificates $real ;;
    dnf|yum) $SUDO "$PM" install -y $real ;;
    pacman)  $SUDO pacman -Sy --noconfirm $real ;;
    zypper)  $SUDO zypper --non-interactive install $real ;;
    apk)     $SUDO apk add $real ;;
    xbps-install) $SUDO xbps-install -Sy $real ;;
    brew)    brew install ${real//nodejs/node} ;;
    *) return 1 ;;
  esac
}

# ---------- vault + memory sync ----------
put() { # put <file>   content on stdin, never overwrites an existing file
  if [ -e "$1" ]; then cat >/dev/null; return 0; fi
  mkdir -p "$(dirname "$1")" && cat > "$1"
}

create_vault() {
  local d
  for d in "00-Inbox/Importados" "01-Projetos" "02-Áreas" "03-Recursos/IA" "04-Arquivo" \
           "Diário/Logs de IA" "Templates" "Anexos" ".obsidian"; do
    mkdir -p "$VAULT_DIR/$d"
  done

  put "$VAULT_DIR/README.md" <<'EOF'
# Memory vault

A folder of plain Markdown notes. It works with Obsidian, VS Code, Logseq or
any editor. This vault holds personal notes and project references. Agent
memory uses ai-memory and stays separate from this vault.

- `MAPA.md` explains the layout (PARA method).
- In Obsidian: *Open folder as vault* and choose this folder.
- To see the graph: Obsidian → Graph view.
EOF

  put "$VAULT_DIR/MAPA.md" <<'EOF'
# Vault map

| Folder | Purpose |
|---|---|
| `00-Inbox` | quick capture; triage later |
| `01-Projetos` | work with a beginning and an end |
| `02-Áreas` | ongoing responsibilities |
| `03-Recursos` | reference material and curated resources |
| `04-Arquivo` | what is finished |
| `Diário/Logs de IA` | what each AI session did |
| `Templates` | note templates |
| `Anexos` | images and files |
EOF

  put "$VAULT_DIR/AGENTS.md" <<'EOF'
# Instructions for AI agents

- This vault is long-term memory. Read `MAPA.md` before creating notes.
- Do not delete notes; move them to `04-Arquivo`.
- Log what you did in `Diário/Logs de IA/` using `Templates/Log-de-IA.md`.
- Never store secrets (passwords, tokens, keys) here.
EOF

  put "$VAULT_DIR/.claudignore" <<'EOF'
.obsidian/
.trash/
Anexos/
EOF

  put "$VAULT_DIR/Templates/Projeto.md" <<'EOF'
---
tipo: projeto
status: ativo
criado: {{date}}
---
# {{title}}

## Objetivo

## Próximos passos
- [ ]

## Notas
EOF

  put "$VAULT_DIR/Templates/Log-de-IA.md" <<'EOF'
---
tipo: log-ia
data: {{date}}
agente:
---
# Log {{date}}

## O que foi feito

## Decisões

## Pendências
EOF

  put "$VAULT_DIR/Templates/Especificacao.md" <<'EOF'
---
tipo: especificacao
criado: {{date}}
---
# {{title}}

## Problema

## Requisitos

## Critérios de aceite
EOF

  put "$VAULT_DIR/.obsidian/app.json" <<'EOF'
{
  "alwaysUpdateLinks": true,
  "newFileLocation": "folder",
  "newFileFolderPath": "00-Inbox",
  "attachmentFolderPath": "Anexos"
}
EOF

  put "$VAULT_DIR/.obsidian/appearance.json" <<'EOF'
{
  "baseFontSize": 16
}
EOF

  put "$VAULT_DIR/.obsidian/core-plugins.json" <<'EOF'
{
  "file-explorer": true,
  "global-search": true,
  "switcher": true,
  "graph": true,
  "backlink": true,
  "outgoing-link": true,
  "tag-pane": true,
  "page-preview": true,
  "templates": true,
  "daily-notes": true,
  "outline": true,
  "word-count": true
}
EOF

  put "$VAULT_DIR/.obsidian/graph.json" <<'EOF'
{
  "search": "",
  "showTags": true,
  "showAttachments": false,
  "hideUnresolved": false,
  "showOrphans": true,
  "showArrow": false,
  "colorGroups": [],
  "scale": 1,
  "close": false
}
EOF
}

SYNC_BIN="$MB_HOME/bin/sync-memories.sh"
SYNC_METHOD=""

unschedule_sync() {
  case "$(mf_get SYNC_METHOD)" in
    systemd)
      systemctl --user disable --now megabrain-sync.timer >/dev/null 2>&1 || return 1
      rm -f "$HOME/.config/systemd/user/megabrain-sync.timer" "$HOME/.config/systemd/user/megabrain-sync.service"
      systemctl --user daemon-reload >/dev/null 2>&1 || return 1 ;;
    launchd)
      launchctl unload "$HOME/Library/LaunchAgents/com.megabrain.sync.plist" >/dev/null 2>&1 || return 1
      rm -f "$HOME/Library/LaunchAgents/com.megabrain.sync.plist" || return 1 ;;
    cron)
      ( crontab -l 2>/dev/null | grep -v 'megabrain/bin/sync-memories.sh' ) | crontab - 2>/dev/null || return 1 ;;
  esac
  rm -f "$SYNC_BIN" || return 1
}

install_cli() { # keep a copy so `megabrain` works from anywhere
  local dest="$MB_HOME/lib" name
  mkdir -p "$dest" "$HOME/.local/bin"
  # Atomic copies preserve a running installer while its installed copy is refreshed.
  if [ -n "$LIB_DIR" ]; then
    for name in ui.py brain_energize.py; do copy_atomic "$LIB_DIR/$name" "$dest/$name"; done
  fi
  [ -n "$SKILLS_LIB" ] && copy_atomic "$SKILLS_LIB" "$dest/skills.py"
  if [ -n "$INTEGRATIONS_LIB" ]; then
    local source; source="$(dirname "$INTEGRATIONS_LIB")"
    for name in integrations.py mac_agent.py mac_worker.py; do
      copy_atomic "$source/$name" "$dest/$name"
    done
  fi
  if [ -n "$SELF" ] && [ -f "$SELF" ]; then copy_atomic "$SELF" "$dest/install.sh"
  else
    local tmp; tmp="$(mktemp "$dest/.mb-copy.XXXXXX")" || return 1
    curl -fsSL --max-time 30 "$MB_RAW/install.sh" -o "$tmp" && mv "$tmp" "$dest/install.sh" || { rm -f "$tmp"; return 1; }
  fi
  printf '%s\n' "$MB_VERSION" > "$dest/VERSION"
  chmod +x "$dest/install.sh"
  ln -sf "$dest/install.sh" "$HOME/.local/bin/megabrain"
}

# ---------- Obsidian (optional; the vault exists either way) ----------
obsidian_installed() {
  have obsidian && return 0
  have flatpak && flatpak list --app 2>/dev/null | grep -q 'md.obsidian.Obsidian' && return 0
  have snap && snap list obsidian >/dev/null 2>&1 && return 0
  [ -d /Applications/Obsidian.app ] || [ -d "$HOME/Applications/Obsidian.app" ]
}
OB_METHOD=""; OB_CMD=""
obsidian_method() {
  OB_METHOD=""; OB_CMD=""
  if [ "$OS_NAME" = "Darwin" ] && have brew; then OB_METHOD=brew;    OB_CMD="brew install --cask obsidian"
  elif have flatpak;                      then OB_METHOD=flatpak; OB_CMD="flatpak install -y --user flathub md.obsidian.Obsidian"
  elif have snap;                         then OB_METHOD=snap;    OB_CMD="${SUDO:+$SUDO }snap install obsidian --classic"
  elif [ "$PM" = "pacman" ];              then OB_METHOD=pacman;  OB_CMD="${SUDO:+$SUDO }pacman -S --noconfirm obsidian"
  fi
}
obsidian_run() {
  case "$OB_METHOD" in
    flatpak)
      run_logged flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
      run_logged flatpak install -y --user flathub md.obsidian.Obsidian ;;
    brew)   run_logged brew install --cask obsidian ;;
    snap)   run_logged $SUDO snap install obsidian --classic ;;
    pacman) run_logged $SUDO pacman -S --noconfirm obsidian ;;
    *) return 1 ;;
  esac
}

# ---------- commands ----------
cmd_help() { sed -n '2,/^set -uo pipefail/p' "${SELF:-$0}" 2>/dev/null | sed '$d; s/^# \{0,1\}//'; }

cmd_status() {
  if [ ! -f "$MANIFEST" ]; then echo "MEGABRAIN is not installed on this machine."; return 1; fi
  echo "MEGABRAIN $(mf_get MEGABRAIN_VERSION) · status: $(mf_get STATUS) · source: $(mf_get SOURCE)"
  echo "installed: $(mf_get INSTALLED_AT)"
  echo "agents:    $(mf_get AGENTS)"
  echo "vault:     $(mf_get VAULT_DIR)"
  if have ai-memory; then echo "memory:    $(ai-memory --version 2>/dev/null)  (independent of the Markdown vault)"
  else echo "memory:    not available"; fi
  local k
  for k in ai_memory hermes rtk graft cbm rea_cli rea_setup claude_mem superpowers ecc claude_code_setup playwright firecrawl mimic open_code_review mac_agent knowledge_work security_audit claude_red design_skills writing_skills workflow_skills skills_auto; do
    printf '  %-14s present=%s  managed-by-megabrain=%s\n' "$k" "$(mf_get "PRESENT_$k")" "$(mf_get "MANAGED_$k")"
  done
  printf '  %-14s present=%s  Claude-managed=%s  Codex-managed=%s\n' "text-to-cad" "$(mf_get PRESENT_text_to_cad)" "$(mf_get MANAGED_text_to_cad_claude)" "$(mf_get MANAGED_text_to_cad_codex)"
}

cmd_sync() {
  echo "The agent memory mirror is retired. ai-memory manages agent memory. The Markdown vault remains unchanged."
}

# Mark this machine as already installed WITHOUT installing or changing anything.
# Everything is recorded as pre-existing (managed=0) so uninstall never removes it.
cmd_mark_installed() {
  if is_installed && [ "$FORCE" = 0 ]; then echo "Already marked as installed (use --force to rewrite)."; return 0; fi
  detect_agents
  mkdir -p "$MB_HOME"; rm -f "$MANIFEST"
  mf_put MEGABRAIN_VERSION "$MB_VERSION"; mf_put INSTALLED_AT "$(now_iso)"
  mf_put SOURCE "marked"; mf_put AGENTS "$DETECTED"; mf_put OS "$DISTRO"
  have rtk && mf_put PRESENT_rtk 1;                      mf_put MANAGED_rtk 0
  have graft && mf_put PRESENT_graft 1;                  mf_put MANAGED_graft 0
  have codebase-memory-mcp && mf_put PRESENT_cbm 1;      mf_put MANAGED_cbm 0
  if have claude; then
    local list; list="$(claude plugin list --json 2>/dev/null)"
    grep -q '"id": "claude-mem@' <<<"$list"   && mf_put PRESENT_claude_mem 1
    grep -q '"id": "superpowers@' <<<"$list"  && mf_put PRESENT_superpowers 1
    grep -q '"id": "ecc@' <<<"$list"          && mf_put PRESENT_ecc 1
    grep -q '"id": "claude-code-setup@' <<<"$list" && mf_put PRESENT_claude_code_setup 1
    grep -q '"id": "text-to-cad@' <<<"$list" && mf_put PRESENT_text_to_cad 1
  fi
  if have codex; then
    local codex_plugins; codex_plugins="$(codex plugin list --json 2>/dev/null)"
    grep -q '"pluginId": "text-to-cad@' <<<"$codex_plugins" && mf_put PRESENT_text_to_cad 1
  fi
  if have rea; then
    mf_put PRESENT_rea_cli 1; mf_put MANAGED_rea_cli 0
    rea_setup_present && { mf_put PRESENT_rea_setup 1; mf_put MANAGED_rea_setup 0; }
  else
    mf_put MANAGED_rea_cli 0; mf_put MANAGED_rea_setup 0
  fi
  mf_put MANAGED_claude_mem 0; mf_put MANAGED_superpowers 0; mf_put MANAGED_ecc 0
  mf_put MANAGED_claude_code_setup 0; mf_put MANAGED_text_to_cad_claude 0; mf_put MANAGED_text_to_cad_codex 0
  if [ -d "$VAULT_DIR" ] && [ "$VAULT_DIR" != "$MB_HOME/vault" ]; then
    mf_put VAULT_DIR "$VAULT_DIR"; mf_put PRESENT_vault 1
  fi
  mf_put MANAGED_vault 0; mf_put MANAGED_sync 0; mf_put MANAGED_cli 0
  mf_put PRESENT_wiring 1
  mf_put STATUS "complete"
  echo "Marked as installed (nothing was installed or changed)."
  cmd_status
}

# ---------- install ----------
preflight() {
  say "System"; CUR=""
  ok "$DISTRO ($ARCH) · package manager: ${PM:-none detected}"
  case "$OS_NAME" in MINGW*|MSYS*|CYGWIN*) fail "Windows shell detected: use WSL (Ubuntu) and run this there"; return 1 ;; esac
  case "$ARCH" in x86_64|amd64|aarch64|arm64) ;; *) warn "architecture $ARCH: some prebuilt binaries may not exist" ;; esac
  detect_agents
  # Hermes can bootstrap a new machine; an explicit --agents list wins.
  if want hermes && [ -z "$AGENTS_OVERRIDE" ] && ! has_agent hermes; then
    DETECTED="${DETECTED:+$DETECTED }hermes"
  fi
  if [ -z "$DETECTED" ]; then
    warn "no coding agent found. Install one (e.g. Claude Code) or force with --agents claude,codex"
    return 1
  fi
  local a; for a in $DETECTED; do ok "agent: $a"; done

  local need="" x
  for x in curl git; do have "$x" || need="$need $x"; done
  local item needs_python=0
  for item in $SKILL_COMPONENTS $INTEGRATIONS skills-auto; do want "$item" && needs_python=1; done
  if [ -n "$DETECTED" ] && [ "$needs_python" = 1 ]; then
    have python3 || need="$need python3"
  fi
  if want graft || want rea || want claude-mem || want superpowers || want ecc || want playwright || want open-code-review || [ -n "$LANGUAGE" ]; then
    have node || need="$need node"
    if want graft || want rea || want playwright || want open-code-review; then have npm || need="$need npm"; fi
  fi
  need="${need# }"
  if [ -n "$need" ]; then
    warn "missing: $need"
    if want deps && [ -n "$PM" ] && [ "$PM" != rpm-ostree ] && [ "$PM" != nix ]; then
      if [ "$YES" = 0 ] && [ "$DRY" = 0 ]; then
        ask_toggle "Install $need with $PM (${SUDO:-root})?" yes || { echo "    Cancelled. Install them and run again."; return 1; }
      fi
      if [ "$DRY" = 1 ]; then printf '    %s install %s via %s\n' "$(c 2 '[dry-run]')" "$need" "$PM"
      else
        # shellcheck disable=SC2086
        install_pkgs $need && ok "dependencies installed" || { fail "could not install: $need"; return 1; }
        hash -r
      fi
    else
      fail "install manually: $need (immutable system, no package manager, or --no-deps)"; return 1
    fi
  fi
  have curl || [ "$DRY" = 1 ] || return 1
  if have npm; then
    local prefix; prefix="$(npm config get prefix 2>/dev/null)"
    if [ -n "$prefix" ] && [ ! -w "$prefix" ]; then export npm_config_prefix="$HOME/.local"; fi
  fi
  return 0
}

plugin_present() { have claude && claude plugin list --json 2>/dev/null | grep -q "\"id\": \"$1\""; }
codex_plugin_present() { have codex && codex plugin list --json 2>/dev/null | grep -q "\"pluginId\": \"$1\""; }

rea_setup_present() {
  have rea || return 1
  local report
  report="$(rea doctor --json 2>/dev/null)" || true
  [ -n "$report" ] || return 0
  node -e 'try {
    const d=JSON.parse(process.argv[1]);
    const present=s=>typeof s==="string" && s!=="missing";
    const registration=Array.isArray(d.registrations) && d.registrations.some(x=>present(x.state));
    const skill=d.skill && present(d.skill.state);
    process.exit(registration || skill ? 0 : 1);
  } catch (_) { process.exit(0); }' "$report"
}

install_plugin() { # install_plugin <key> <label> <marketplace-src> <plugin@marketplace> <mf-key>
  local key="$1" label="$2" src="$3" id="$4" mk="$5"
  want "$key" || { S_skip "$key" "skipped (--skip/--only)"; return; }
  if ! has_agent claude; then S_skip "$key" "Claude Code not detected"; return; fi
  S_begin "$key" "$label"
  if [ "$DRY" = 0 ] && plugin_present "$id"; then
    ok "already installed: $id"; mf_put "MANAGED_$mk" 0; mf_put "PRESENT_$mk" 1
  else
    run_logged claude plugin marketplace add "$src" || true
    if run_logged claude plugin install "$id"; then
      ok "installed: $id"; mf_put "MANAGED_$mk" 1; mf_put "PRESENT_$mk" 1
    else fail "plugin $id"; fi
  fi
  S_end
}

install_claude_code_setup() {
  local id="claude-code-setup@claude-plugins-official" key="claude-code-setup"
  want "$key" || { S_skip "$key" "skipped (--skip/--only)"; return; }
  if ! has_agent claude; then S_skip "$key" "Claude Code not detected"; return; fi
  S_begin "$key" "Claude Code setup recommendations"
  if [ "$DRY" = 0 ] && plugin_present "$id"; then
    ok "already installed: $id"; mf_put MANAGED_claude_code_setup 0; mf_put PRESENT_claude_code_setup 1
  else
    run_logged claude plugin marketplace add anthropics/claude-plugins-official || true
    if run_logged claude plugin install "$id"; then
      ok "installed: $id"; mf_put MANAGED_claude_code_setup 1; mf_put PRESENT_claude_code_setup 1
    else fail "plugin $id"; fi
  fi
  S_end
}

install_text_to_cad() {
  local key="text-to-cad" id="text-to-cad@earthtojake" found=0
  want "$key" || { S_skip "$key" "skipped (--skip/--only)"; return; }
  has_agent claude && found=1
  has_agent codex && found=1
  if [ "$found" = 0 ]; then S_skip "$key" "Codex or Claude Code not detected"; return; fi
  S_begin "$key" "text-to-cad (local CAD tools)"
  if has_agent claude; then
      if [ "$DRY" = 0 ] && ! have claude; then fail "Claude Code CLI is unavailable"
    elif [ "$DRY" = 0 ] && plugin_present "$id"; then
      ok "already installed for Claude Code"; mf_put MANAGED_text_to_cad_claude 0; mf_put PRESENT_text_to_cad 1
    else
      run_logged claude plugin marketplace add earthtojake/text-to-cad#latest || true
      if run_logged claude plugin install "$id"; then
        ok "installed for Claude Code"; mf_put MANAGED_text_to_cad_claude 1; mf_put PRESENT_text_to_cad 1
      else fail "text-to-cad for Claude Code"; fi
    fi
  fi
  if has_agent codex; then
      if [ "$DRY" = 0 ] && ! have codex; then fail "Codex CLI is unavailable"
    elif [ "$DRY" = 0 ] && codex_plugin_present "$id"; then
      ok "already installed for Codex"; mf_put MANAGED_text_to_cad_codex 0; mf_put PRESENT_text_to_cad 1
    else
      run_logged codex plugin marketplace add earthtojake/text-to-cad --ref latest || true
      if run_logged codex plugin add "$id"; then
        ok "installed for Codex"; mf_put MANAGED_text_to_cad_codex 1; mf_put PRESENT_text_to_cad 1
      else fail "text-to-cad for Codex"; fi
    fi
  fi
  S_end
}

install_rea() {
  local key=rea setup_existed=0
  want "$key" || { S_skip "$key" "skipped (--skip/--only)"; return; }
  S_begin "$key" "REA (reverse engineering tools)"
  if have rea; then
    ok "already installed: $(rea --version 2>/dev/null | tr -d '[:space:]')"
    mf_put MANAGED_rea_cli 0; mf_put PRESENT_rea_cli 1
    if rea_setup_present; then setup_existed=1; fi
  elif have npm || [ "$DRY" = 1 ]; then
    if run_logged npm install -g rea-agents; then
      ok "CLI installed"; hash -r; mf_put MANAGED_rea_cli 1; mf_put PRESENT_rea_cli 1
    else fail "npm install -g rea-agents"; fi
  else fail "REA needs npm"; fi

  if [ "$DRY" = 1 ]; then
    run_logged rea setup --yes --all-detected
  elif have rea; then
    if [ "$setup_existed" = 1 ]; then
      ok "existing REA registrations and skills left unchanged"
      mf_put PRESENT_rea_setup 1; mf_put MANAGED_rea_setup 0
      # Keep a newly installed CLI if pre-existing configs depend on it.
      mf_put MANAGED_rea_cli 0
    else
      mf_put MANAGED_rea_setup 1
      if run_logged rea setup --yes --all-detected; then
        ok "REA integrations and skill configured for detected clients"
        mf_put PRESENT_rea_setup 1; mf_put MANAGED_rea_setup 1
      else fail "rea setup"; fi
    fi
  fi
  S_end
}

install_integration() {
  local key="$1" label="$2" mk="${1//-/_}" managed=0
  want "$key" || { S_skip "$key" "skipped (--skip/--only)"; return; }
  if [ "$key" != ai-memory ] && ! has_agent claude && ! has_agent codex && ! has_agent hermes; then S_skip "$key" "No supported agent detected"; return; fi
  if [ "$key" = hermes ] && ! has_agent hermes; then S_skip "$key" "Hermes excluded by --agents"; return; fi
  S_begin "$key" "$label"
  if [ "$DRY" = 1 ]; then
    if [ "$key" = hermes ]; then
      ok "[dry-run] would install Hermes from its official stable installer (--non-interactive), wire repository MCPs and the vault skill; provider login stays interactive"
    elif [ "$key" = ai-memory ]; then
      ok "[dry-run] would install ai-memory $AI_MEMORY_VERSION and configure detected supported agents; existing vault notes stay unchanged"
    else
      ok "[dry-run] would configure $key for supported detected clients; existing integrations preserved"
    fi
  elif ! have python3 || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))'; then
    fail "$key requires Python 3.8 or later"
  elif ! ensure_integrations_lib; then
    fail "could not load the integration installer"
  else
    if [ "$key" = mimic ] && ! have uv; then
      if want deps && fetch_and_run https://astral.sh/uv/install.sh sh; then hash -r
      else fail "Mimic needs uv: install it first, or allow dependencies"; S_end; return; fi
    fi
    if run_logged python3 "$INTEGRATIONS_LIB" install "$key" --agents "$DETECTED" --state-dir "$MB_HOME/state" --vault-dir "$VAULT_DIR"; then
      python3 "$INTEGRATIONS_LIB" owned "$key" --state-dir "$MB_HOME/state" && managed=1
      mf_put "MANAGED_$mk" "$managed"; mf_put "PRESENT_$mk" 1
      ok "$key ready; ownership recorded"
      if [ "$key" = ai-memory ] && has_agent claude && plugin_present claude-mem@thedotmack; then
        if run_logged claude plugin uninstall claude-mem@thedotmack --keep-data; then
          ok "replaced legacy Claude memory plugin; its data stays on disk"
          mf_put_exact MANAGED_claude_mem 0; mf_put PRESENT_claude_mem 0
        else fail "could not replace the legacy Claude memory plugin"; fi
      fi
    else fail "$key installation (see $LOGFILE)"; fi
  fi
  S_end
}

install_skills_component() { # install_skills_component <component> <label>
  local key="$1" label="$2" mk="${1//-/_}" managed=0
  want "$key" || { S_skip "$key" "skipped (--skip/--only)"; return; }
  if ! has_agent claude && ! has_agent codex && ! has_agent hermes; then S_skip "$key" "No supported agent detected"; return; fi
  S_begin "$key" "$label"
  if [ "$DRY" = 1 ]; then
    ok "[dry-run] would configure $key for Codex/Claude/Hermes clients (existing skills preserved)"
  elif ! have python3 || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 8))'; then
    fail "$key requires Python 3.8 or later"
  elif ! ensure_skills_lib; then
    fail "could not load the skills installer"
  elif run_logged python3 "$SKILLS_LIB" install "$key" --agents "$DETECTED" --state-dir "$MB_HOME/state"; then
    python3 "$SKILLS_LIB" owned "$key" --state-dir "$MB_HOME/state" && managed=1
    mf_put "MANAGED_$mk" "$managed"; mf_put "PRESENT_$mk" 1
    ok "$key ready; ownership recorded; no security workflow was executed"
  else fail "$key installation (see $LOGFILE)"; fi
  S_end
}

do_install() {
  local ts; ts="$(date +%Y%m%d-%H%M%S)"
  if [ "$DRY" = 0 ]; then mkdir -p "$MB_HOME/logs"; LOGFILE="$MB_HOME/logs/install-$ts.log"; : > "$LOGFILE"; fi
  ensure_lib || true
  [ "$DRY" = 1 ] || mkdir -p "$HOME/.local/bin"
  case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) export PATH="$HOME/.local/bin:$PATH"; PATH_ADDED=1 ;; esac

  # --- plain pre-flight (may need sudo, so it runs before the animation) ---
  preflight || { echo; echo "Fix the items above and run again."; return 1; }

  if [ "$YES" = 0 ] && [ "$DRY" = 0 ]; then
    printf '\n    Install for: %s\n    An existing settings.json is backed up first.\n' "$DETECTED"
    ask_toggle "Continue?" yes || { echo "    Cancelled."; return 0; }
  fi
  if [ -f "$HOME/.claude/settings.json" ] && [ "$DRY" = 0 ]; then
    cp "$HOME/.claude/settings.json" "$HOME/.claude/settings.json.bak-$ts"
  fi

  # --- animation starts here ---
  start_ui install
  if [ "$DRY" = 0 ]; then
    mf_reset_keep_owned; KEEP_OWNED=1
    mf_put MEGABRAIN_VERSION "$MB_VERSION"; mf_put INSTALLED_AT "$(now_iso)"
    mf_put SOURCE "install"; mf_put AGENTS "$DETECTED"; mf_put OS "$DISTRO"
    # Record the selected components and targets for installation diagnostics.
    mf_put INSTALL_SKIP "$(printf '%s' "$SKIP" | xargs)"; mf_put INSTALL_ONLY "$(printf '%s' "$ONLY" | xargs)"
    mf_put INSTALL_AGENTS "$AGENTS_OVERRIDE"; mf_put INSTALL_LANGUAGE "$LANGUAGE"
    mf_put STATUS "partial"
  fi

  S_begin environment "Environment" "curl, git, node, npm, disk space"
  ok "curl, git detected"; have node && ok "node $(node --version 2>/dev/null)"
  S_end
  S_begin agents "Agents" "scanning for coding agents"
  ok "detected: $DETECTED"; S_end

  # Hermes must exist before tools that detect it configure their hooks/MCPs.
  install_integration hermes "Hermes Agent (official stable runtime, memory and vault skill)"

  # RTK
  if want rtk; then
    S_begin rtk "RTK (command output compression)" "token-optimized command proxy"
    if have rtk; then ok "already installed: $(rtk --version 2>/dev/null)"; mf_put MANAGED_rtk 0
    else
      if fetch_and_run "$RTK_INSTALLER" sh; then ok "installed"; hash -r; mf_put MANAGED_rtk 1
      else fail "RTK installer failed (see $LOGFILE)"; fi
    fi
    if have rtk || [ "$DRY" = 1 ]; then
      local a flags
      for a in $DETECTED; do
        case "$a" in
          claude) flags="" ;; codex) flags="--codex" ;; gemini) flags="--gemini" ;;
          opencode) flags="--opencode" ;; copilot) flags="--copilot" ;;
          cursor|windsurf|cline|kilocode|antigravity|hermes|droid|vibe|pi) flags="--agent $a" ;;
          *) warn "RTK: no known support for $a"; continue ;;
        esac
        # shellcheck disable=SC2086
        run_logged rtk init -g $flags --auto-patch && ok "hooks -> $a" || fail "rtk init ($a)"
      done
      mf_put PRESENT_rtk 1
    fi
    S_end
  else S_skip rtk "skipped (--skip/--only)"; fi

  # graft
  if want graft; then
    S_begin graft "graft (repository context graph)" "repository context graph"
    if have graft; then ok "already installed: $(graft --version 2>/dev/null)"; mf_put MANAGED_graft 0
    elif have npm || [ "$DRY" = 1 ]; then
      if run_logged npm install -g @nanonets/graft; then ok "installed"; hash -r; mf_put MANAGED_graft 1
      else fail "npm install -g @nanonets/graft"; fi
    else fail "graft needs npm"; fi
    if have graft && [ "$DRY" = 0 ]; then
      if has_agent claude && have claude; then
        if claude mcp list 2>/dev/null | grep -q '^graft'; then ok "MCP already registered (claude)"
        elif run_logged claude mcp add --scope user graft -- graft mcp; then ok "MCP -> claude"; mf_put MCPADD_graft_claude 1
        else fail "claude mcp add graft"; fi
      fi
      if has_agent codex && have codex; then
        if codex mcp list 2>/dev/null | grep -q 'graft'; then ok "MCP already registered (codex)"
        elif run_logged codex mcp add graft -- graft mcp; then ok "MCP -> codex"; mf_put MCPADD_graft_codex 1
        else warn "codex: run  codex mcp add graft -- graft mcp"; fi
      fi
      mf_put PRESENT_graft 1
    fi
    ok "per project: run 'graft init' inside each repo"
    S_end
  else S_skip graft "skipped (--skip/--only)"; fi

  # codebase-memory-mcp
  if want cbm; then
    S_begin cbm "codebase-memory-mcp (structural graph)" "structural graph · sqlite engine"
    if have codebase-memory-mcp; then ok "already installed: $(codebase-memory-mcp --version 2>/dev/null)"; mf_put MANAGED_cbm 0
    else
      if fetch_and_run "$CBM_INSTALLER" bash; then ok "installed"; hash -r; mf_put MANAGED_cbm 1
      else fail "codebase-memory-mcp installer failed (see $LOGFILE)"; fi
    fi
    if have codebase-memory-mcp || [ "$DRY" = 1 ]; then
      run_logged codebase-memory-mcp install -y && ok "MCP + hooks wired for detected clients" || fail "codebase-memory-mcp install"
      mf_put PRESENT_cbm 1
    fi
    ok "index each project once: ask your agent to run index_repository"
    S_end
  else S_skip cbm "skipped (--skip/--only)"; fi

  # Agent memory
  install_integration ai-memory "ai-memory (shared agent memory)"
  # Plugins
  install_rea
  install_plugin superpowers "superpowers (process skills)" anthropics/claude-plugins-official superpowers@claude-plugins-official superpowers
  install_plugin ecc "ECC (agents, skills, hooks)" https://github.com/affaan-m/ECC.git ecc@ecc ecc
  install_text_to_cad
  install_claude_code_setup
  install_integration playwright "Playwright browser MCP"
  install_integration firecrawl "Firecrawl web extraction MCP"
  install_integration mimic "Mimic API client tools and skill"
  install_integration open-code-review "Open Code Review CLI and plugins"
  install_integration mac-agent "Mac SSH task runner and skill"
  install_skills_component security-audit "Cloudflare security audit skill"
  install_skills_component claude-red "Claude-Red security skill library"
  install_skills_component design-skills "Design skills (awwwards, jury, antislop, logo-design, motionmaxxing)"
  install_skills_component writing-skills "Writing skills (humanizer, no-ai-slop)"
  install_skills_component workflow-skills "Workflow skills (find-skills, grill-me)"
  install_skills_component skills-auto "Automatic relevant-skill selection"

  # vault
  if want vault; then
    S_begin vault "Memory vault (Markdown backup)" "hidden memory backup vault"
    if [ "$DRY" = 1 ]; then ok "[dry-run] would create $VAULT_DIR"
    else
      local existed=0; [ -d "$VAULT_DIR" ] && existed=1
      if create_vault; then
        ok "vault at $VAULT_DIR"
        mf_put VAULT_DIR "$VAULT_DIR"; mf_put PRESENT_vault 1
        if [ "$existed" = 0 ]; then mf_put MANAGED_vault 1; else mf_put MANAGED_vault 0; fi
      else fail "could not create the vault"; fi
    fi
    S_end
  else S_skip vault "skipped (--skip/--only)"; fi

  # wiring: sync, CLI, preferences, manifest
  S_begin wiring "Wiring (memory migration, CLI, manifest)" "memory migration, CLI and manifest"
  if [ "$DRY" = 1 ]; then
    ok "[dry-run] would stop the legacy mirror timer, preserve the vault path and install the megabrain command"
  else
    # Stop the old mirror timer but keep every existing vault note.
    if [ "$(mf_get MANAGED_sync)" = 1 ]; then
      if unschedule_sync; then
        mf_put SYNC_METHOD "disabled"
        ok "legacy memory mirror stopped; vault notes kept"
      else fail "could not stop the legacy memory mirror"; fi
    fi
    # Repository tools may have been installed after the first Hermes pass.
    if want hermes && has_agent hermes && have hermes && ensure_integrations_lib; then
      run_logged python3 "$INTEGRATIONS_LIB" install hermes --agents hermes --state-dir "$MB_HOME/state" --vault-dir "$VAULT_DIR" \
        && ok "Hermes repository tools connected" || fail "Hermes tool wiring"
    fi
    if install_cli; then ok "command installed: megabrain"; mf_put MANAGED_cli 1
    else warn "could not install the megabrain command"; fi
    if [ -n "$LANGUAGE" ] && has_agent claude && have node; then
      node -e '
        const fs=require("fs"),path=require("path");
        const p=process.argv[1], lang=process.argv[2];
        let d={}; try{ d=JSON.parse(fs.readFileSync(p,"utf8")); }catch(e){}
        d.language=lang;
        fs.mkdirSync(path.dirname(p),{recursive:true});
        fs.writeFileSync(p, JSON.stringify(d,null,2));
      ' "$HOME/.claude/settings.json" "$LANGUAGE" && ok "language = $LANGUAGE" || fail "write language"
    fi
    mf_put PRESENT_wiring 1
    mf_put STATUS "complete"
    ok "manifest written"
  fi
  S_end

  emit meta present "$(present_list)"

  # --- Obsidian (optional) ---
  local ob_line="" final_head="✔ MEGABRAIN installed"
  if want obsidian; then
    obsidian_method
    CUR=""
    if [ "$DRY" = 1 ]; then
      ob_line="[dry-run] would ask: install Obsidian? (${OB_CMD:-manual install})"
    elif obsidian_installed; then
      ob_line="Obsidian already installed: open folder as vault -> $VAULT_DIR"
    elif [ -z "$OB_METHOD" ]; then
      ob_line="Get Obsidian at https://obsidian.md/download (no automatic method here)"
    else
      local do_ob=0
      case "$OBSIDIAN_MODE" in
        yes) do_ob=1 ;;
        no)  do_ob=0 ;;
        *)   if [ "$YES" = 1 ]; then do_ob=0
             elif ask_yes_no obsidian "✔ Installation complete" "Obsidian (optional) · $DISTRO" "$OB_CMD" "Install Obsidian now?" yes; then do_ob=1
             fi ;;
      esac
      if [ "$do_ob" = 1 ]; then
        emit task "Installing Obsidian" "$OB_CMD"
        emit tasklog "resolving package source"
        if obsidian_run; then emit tasklog "installed"; emit taskdone; ob_line="Obsidian installed: open folder as vault -> $VAULT_DIR"
        else emit taskdone; FAILED="${FAILED}Obsidian install"$'\n'; ob_line="Obsidian install failed. Run: $OB_CMD"; fi
      else
        ob_line="Obsidian not installed. Install later: $OB_CMD"
      fi
    fi
  fi

  local style=ok
  if [ -n "$FAILED" ]; then style=warn; final_head="MEGABRAIN installed with warnings"; fi
  if [ "$DRY" = 1 ]; then final_head="Dry run finished (nothing was changed)"; fi
  emit final "$style" "$final_head" "  agents: $DETECTED" "  vault: $VAULT_DIR" "  ${ob_line:-}" "  run 'megabrain' any time to check or uninstall"
  stop_ui

  # --- plain summary (stays in the terminal scrollback) ---
  echo
  echo "$(c '1;32' "$final_head")  v$MB_VERSION"
  echo "  agents : $DETECTED"
  echo "  vault  : $VAULT_DIR"
  [ -n "$ob_line" ] && echo "  note   : $ob_line"
  [ "$DRY" = 0 ] && echo "  log    : $LOGFILE"
  if [ -n "$FAILED" ]; then echo; echo "Items with problems:"; printf '%s' "$FAILED" | sed 's/^/  - /'; fi
  [ "$PATH_ADDED" = 1 ] && echo "  PATH   : add  export PATH=\"\$HOME/.local/bin:\$PATH\"  to your shell rc"
  echo
  echo "Next: restart your agents (hooks/MCPs load on new sessions) · run 'graft init' in each repo · 'rtk gain' to see savings."
  [ -z "$FAILED" ]
}

# ---------- uninstall ----------
uninstall_rtk() {
  local a flags
  for a in $(mf_get AGENTS); do
    case "$a" in
      claude) flags="" ;; codex) flags="--codex" ;; gemini) flags="--gemini" ;;
      opencode) flags="--opencode" ;; copilot) flags="--copilot" ;;
      cursor|windsurf|cline|kilocode|antigravity|hermes|droid|vibe|pi) flags="--agent $a" ;;
      *) continue ;;
    esac
    # shellcheck disable=SC2086
    run_logged rtk init -g $flags --uninstall --auto-patch && ok "hooks removed: $a"
  done
  local bin; bin="$(command -v rtk 2>/dev/null)"
  case "$bin" in
    "$HOME"/*) rm -f "$bin" && ok "binary removed" ;;
    "") ;;
    *) warn "binary at $bin left in place (not under \$HOME)" ;;
  esac
}

do_uninstall() {
  local ts; ts="$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$MB_HOME/logs"; LOGFILE="$MB_HOME/logs/uninstall-$ts.log"; : > "$LOGFILE"
  emit mode uninstall

  # sync
  CUR=sync; STEP_FAILED=0
  if [ "$(mf_get MANAGED_sync)" = 1 ]; then
    emit begin sync
    if unschedule_sync; then ok "timer removed, script deleted"; else fail "legacy sync cleanup"; fi
    S_end
  else emit skip sync "not installed by MEGABRAIN"; fi

  # rtk
  CUR=rtk; STEP_FAILED=0
  if [ "$(mf_get MANAGED_rtk)" = 1 ] && have rtk; then emit begin rtk; uninstall_rtk; S_end
  else emit skip rtk "not installed by MEGABRAIN (left untouched)"; fi

  # graft
  CUR=graft; STEP_FAILED=0
  if [ "$(mf_get MANAGED_graft)" = 1 ] || [ "$(mf_get MCPADD_graft_claude)" = 1 ] || [ "$(mf_get MCPADD_graft_codex)" = 1 ]; then
    emit begin graft
    if [ "$(mf_get MCPADD_graft_claude)" = 1 ] && have claude; then
      run_logged claude mcp remove graft -s user && ok "MCP removed (claude)"
    fi
    if [ "$(mf_get MCPADD_graft_codex)" = 1 ] && have codex; then
      run_logged codex mcp remove graft && ok "MCP removed (codex)"
    fi
    if [ "$(mf_get MANAGED_graft)" = 1 ] && have npm; then
      run_logged npm uninstall -g @nanonets/graft && ok "package removed"
    fi
    ok "per-repo graft/ folders were left alone"
    S_end
  else emit skip graft "not installed by MEGABRAIN (left untouched)"; fi

  # codebase-memory-mcp
  CUR=cbm; STEP_FAILED=0
  if [ "$(mf_get MANAGED_cbm)" = 1 ] && have codebase-memory-mcp; then
    emit begin cbm
    if run_logged codebase-memory-mcp uninstall -n; then ok "binary and agent configs removed"; else fail "codebase-memory-mcp uninstall"; fi
    ok "your indexes were kept"
    S_end
  else emit skip cbm "not installed by MEGABRAIN (left untouched)"; fi

  # REA integrations (only when this installation configured them)
  CUR=rea; STEP_FAILED=0
  if [ "$(mf_get MANAGED_rea_setup)" = 1 ]; then
    emit begin rea
    if have rea; then
      if run_logged rea uninstall; then
        ok "REA registrations and skill removed; REA data kept"
        mf_put MANAGED_rea_setup 0
        if [ "$(mf_get MANAGED_rea_cli)" = 1 ] && have npm; then
          if run_logged npm uninstall -g rea-agents; then ok "REA CLI removed"; mf_put MANAGED_rea_cli 0
          else fail "npm uninstall -g rea-agents"; fi
        fi
      else
        fail "rea uninstall; REA CLI kept so existing integrations can still work"
      fi
    else
      warn "REA CLI is missing; its configured integration state could not be cleaned up"
      fail "REA uninstall unavailable"
    fi
    S_end
  elif [ "$(mf_get MANAGED_rea_cli)" = 1 ]; then
    emit begin rea
    if have npm && run_logged npm uninstall -g rea-agents; then ok "REA CLI removed"
    else fail "npm uninstall -g rea-agents"; fi
    S_end
  else emit skip rea "not installed by MEGABRAIN (left untouched)"; fi

  # plugins
  local pair key mk id extra rest
  for pair in "claude-mem:claude_mem:claude-mem@thedotmack:--keep-data" "superpowers:superpowers:superpowers@claude-plugins-official:" "ecc:ecc:ecc@ecc:" "claude-code-setup:claude_code_setup:claude-code-setup@claude-plugins-official:"; do
    key="${pair%%:*}"; rest="${pair#*:}"; mk="${rest%%:*}"; rest="${rest#*:}"; id="${rest%%:*}"; extra="${rest#*:}"
    CUR="$key"; STEP_FAILED=0
    if [ "$(mf_get "MANAGED_$mk")" = 1 ] && have claude; then
      emit begin "$key"
      # shellcheck disable=SC2086
      if run_logged claude plugin uninstall "$id" $extra; then ok "plugin removed"; else fail "plugin $id"; fi
      S_end
    else emit skip "$key" "not installed by MEGABRAIN (left untouched)"; fi
  done

  CUR=text-to-cad; STEP_FAILED=0
  if [ "$(mf_get MANAGED_text_to_cad_claude)" = 1 ] || [ "$(mf_get MANAGED_text_to_cad_codex)" = 1 ]; then
    emit begin text-to-cad
    if [ "$(mf_get MANAGED_text_to_cad_claude)" = 1 ] && have claude; then
      run_logged claude plugin uninstall text-to-cad@earthtojake && ok "Claude Code plugin removed" || fail "text-to-cad Claude Code uninstall"
    fi
    if [ "$(mf_get MANAGED_text_to_cad_codex)" = 1 ] && have codex; then
      run_logged codex plugin remove text-to-cad@earthtojake && ok "Codex plugin removed" || fail "text-to-cad Codex uninstall"
    fi
    S_end
  else emit skip text-to-cad "not installed by MEGABRAIN (left untouched)"; fi

  # Restore routing/metadata before checking the owned skill directories.
  # The separate ledger survives --force and selected-component reinstalls.
  local skill_component
  for skill_component in skills-auto $SKILL_COMPONENTS; do
    CUR="$skill_component"; STEP_FAILED=0
    if [ -f "$MB_HOME/state/skills.json" ]; then
      emit begin "$skill_component"
      if have python3 && ensure_skills_lib; then
        if run_logged python3 "$SKILLS_LIB" uninstall "$skill_component" --state-dir "$MB_HOME/state"; then
          ok "unchanged MEGABRAIN-owned files removed/restored; modified files kept (see log)"
        else fail "$skill_component cleanup; ownership ledger and backups kept"; fi
      else fail "$skill_component cleanup needs Python and skills.py; ownership ledger kept"; fi
      S_end
    else emit skip "$skill_component" "not installed by MEGABRAIN (left untouched)"; fi
  done

  local integration
  for integration in $INTEGRATIONS; do
    CUR="$integration"; STEP_FAILED=0
    if grep -qs "\"component\": \"$integration\"" "$MB_HOME/state/integrations.json" "$MB_HOME/state/skills.json"; then
      emit begin "$integration"
      if have python3 && ensure_integrations_lib; then
        run_logged python3 "$INTEGRATIONS_LIB" uninstall "$integration" --state-dir "$MB_HOME/state" \
          && ok "owned unchanged integrations removed; existing/modified items kept" \
          || fail "$integration cleanup; ownership ledger kept"
      else fail "$integration cleanup needs Python and the integration helper"; fi
      S_end
    else emit skip "$integration" "not installed by MEGABRAIN (left untouched)"; fi
  done

  # vault (your data: kept unless explicitly purged)
  CUR=vault; STEP_FAILED=0
  local vdir purged=0 purge
  vdir="$(mf_get VAULT_DIR)"
  if [ "$(mf_get MANAGED_vault)" = 1 ] && [ -n "$vdir" ] && [ -d "$vdir" ]; then
    emit begin vault
    purge=$PURGE_VAULT
    if [ "$purge" = 0 ] && [ "$YES" = 0 ]; then
      if ask_yes_no vault_purge "Your memory vault" "$vdir" "plain Markdown · default is to keep it" "Delete the vault too?" no; then purge=1; fi
    fi
    if [ "$purge" = 1 ]; then
      if [ "$vdir" != "$HOME" ] && [ "$vdir" != "/" ] && [ -f "$vdir/MAPA.md" ] && [ -d "$vdir/.obsidian" ]; then
        rm -rf "$vdir" && ok "vault deleted" && purged=1
      else warn "refused to delete $vdir (not a MEGABRAIN vault)"; fi
    else ok "vault kept at $vdir"; fi
    S_end
  else emit skip vault "kept (not created by MEGABRAIN)"; fi

  # marker + CLI
  CUR=marker; emit begin marker
  local had_cli; had_cli="$(mf_get MANAGED_cli)"
  rm -f "$MANIFEST" "$MB_HOME/state/last-sync"
  if [ "$had_cli" = 1 ]; then
    [ "$(readlink "$HOME/.local/bin/megabrain" 2>/dev/null)" = "$MB_HOME/lib/install.sh" ] && rm -f "$HOME/.local/bin/megabrain"
    rm -rf "$MB_HOME/lib" "$MB_HOME/bin"
  fi
  rmdir "$MB_HOME/state" "$MB_HOME/bin" 2>/dev/null
  ok "manifest removed"
  emit done marker

  emit final ok "✔ MEGABRAIN uninstalled" \
       "  vault: $([ "$purged" = 1 ] && echo deleted || echo "kept${vdir:+ at $vdir}")" \
       "  log: $LOGFILE" "  reinstall any time with install.sh"
  stop_ui
  echo
  echo "$(c '1;32' '✔ MEGABRAIN uninstalled.')"
  echo "  Only what MEGABRAIN installed was removed; everything already on this machine was left alone."
  if [ "$purged" = 0 ] && [ -n "$vdir" ]; then echo "  Your vault was kept: $vdir"; fi
  echo "  Log: $LOGFILE"
  return 0
}

# ---------- "already installed" flow ----------
flow_installed() { # shown when MEGABRAIN is installed and the user runs it again
  ensure_lib || true
  local ver date agents
  ver="$(mf_get MEGABRAIN_VERSION)"; date="$(mf_get INSTALLED_AT)"; agents="$(mf_get AGENTS)"
  start_ui installed
  emit meta present "$(present_list)"
  if [ "$CMD" = uninstall ] && [ "$YES" = 1 ]; then
    do_uninstall; return
  fi
  local detail="v${ver:-?} · installed ${date%%T*} · ${agents// /, }"
  if ask_yes_no uninstall "MEGABRAIN already installed" "$detail" \
       "removes only what MEGABRAIN installed · your vault is kept" "Uninstall MEGABRAIN?" no; then
    do_uninstall
  else
    emit final ok "✔ Nothing changed" "  run 'megabrain uninstall' whenever you want" \
         "  or 'install.sh --force' to reinstall/update"
    stop_ui
    echo
    echo "$(c '1;32' 'MEGABRAIN already installed')  v${ver:-?} · ${date%%T*}"
    echo "  agents: $agents"
    echo "  Nothing changed. Uninstall with: megabrain uninstall"
  fi
}

# ---------- entry point ----------
# tools installed by MEGABRAIN live in ~/.local/bin: make sure every command sees them
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) export PATH="$HOME/.local/bin:$PATH" ;; esac

main() {
  case "$CMD" in
    help) cmd_help; return 0 ;;
    version) echo "MEGABRAIN $MB_VERSION"; return 0 ;;
    status) cmd_status; return $? ;;
    sync) cmd_sync; return $? ;;
    mac)
      local client="$MB_HOME/state/mac-runtime/mac_agent.py"
      if [ ! -f "$client" ]; then
        echo "Install the mac-agent component first: bash install.sh --force --only mac-agent" >&2; return 1
      fi
      python3 "$client" ${MAC_ARGS[@]+"${MAC_ARGS[@]}"}; return $? ;;
    mark-installed) cmd_mark_installed; return $? ;;
    uninstall)
      if ! [ -f "$MANIFEST" ]; then echo "MEGABRAIN is not installed on this machine."; return 1; fi
      flow_installed; return $? ;;
    install)
      if [ "$LIST_ONLY" = 1 ]; then detect_agents; echo "${DETECTED:-none}"; return 0; fi
      if is_installed && [ "$FORCE" = 0 ]; then flow_installed; return $?; fi
      do_install; return $? ;;
  esac
}

main
exit $?
