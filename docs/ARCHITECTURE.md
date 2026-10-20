# Architecture

MEGABRAIN is deliberately small: one Bash engine, one Python renderer.

```
install.sh        engine: detection, install, vault, sync, manifest, uninstall
lib/ui.py         renderer: animation, progress panel, Yes/No selector (no side effects)
lib/brain_energize.py   braille brain frames used by the renderer
uninstall.sh      wrapper for `install.sh uninstall`
VERSION           single source of truth for the version
```

## Flow

```
install.sh
 ├─ detect OS, package manager, agents      (existence checks only)
 ├─ pre-flight: curl/git/node/npm            (plain text, may ask for sudo)
 ├─ start lib/ui.py                          (if TTY + python3; otherwise plain mode)
 ├─ steps: environment → agents → rtk → graft → cbm → rea → claude-mem
 │         → superpowers → ecc → text-to-cad
 │         → claude-code-setup → vault → wiring
 ├─ optional: Obsidian question
 └─ final screen + plain summary

install.sh (already installed)
 └─ "MEGABRAIN already installed" → Uninstall? [Yes/No] → uninstall steps
```

Every command the engine runs has its output redirected to
`~/.megabrain/logs/<install|uninstall>-<timestamp>.log`, so the animation is never
corrupted and failures can always be diagnosed afterwards.

## Engine ⇄ UI protocol

The engine appends tab-separated lines to an *events* file; the UI tails it. The UI
writes answers to an *answers* file, which the engine polls.

| Event | Fields | Meaning |
|---|---|---|
| `mode` | `install` \| `uninstall` \| `installed` | switch the step catalog / screen |
| `meta` | `key`, `value` | metadata (`present` = comma-separated installed steps) |
| `begin` | `step`, `[context]` | step started |
| `log` | `step`, `message` | line for the live log |
| `done` / `fail` | `step`, `[message]` | step finished |
| `skip` | `step`, `[reason]` | step intentionally not run |
| `ask` | `id`, `headline`, `line1`, `line2`, `question`, `default` | open a Yes/No selector |
| `task` / `tasklog` / `taskdone` | `title`, `detail` / `message` | bottom progress task (Obsidian) |
| `final` | `ok`\|`warn`\|`fail`, `headline`, `line…` | closing screen |
| `quit` | | exit immediately |

Answers: `<id>\t<yes|no>`.

If the engine process disappears, the UI notices (`--watch-pid`) and exits, restoring
the terminal.

## Manifest

`~/.megabrain/manifest.env` is a flat `KEY="value"` file. It answers two questions:
*is MEGABRAIN installed?* and *what did MEGABRAIN itself install?*

| Key | Meaning |
|---|---|
| `STATUS` | `complete` or `partial` (interrupted run) |
| `SOURCE` | `install` or `marked` (machine marked as installed without installing) |
| `MEGABRAIN_VERSION`, `INSTALLED_AT`, `AGENTS`, `OS`, `VAULT_DIR`, `SYNC_METHOD` | informational |
| `PRESENT_<item>` | the item exists on the machine |
| `MANAGED_<item>` | MEGABRAIN installed it, so MEGABRAIN may remove it |
| `MCPADD_graft_<agent>` | MEGABRAIN registered the graft MCP server for that agent |
| `MANAGED_text_to_cad_<agent>` | MEGABRAIN installed text-to-cad for `claude` or `codex` |
| `MANAGED_rea_cli` | MEGABRAIN installed the REA CLI package |
| `MANAGED_rea_setup` | MEGABRAIN configured REA registrations and skill; uninstall may run `rea uninstall` |

## Safety invariants

1. **Uninstall only removes `MANAGED_*` items.** Anything that was already present
   when the installer ran is recorded with `MANAGED=0` and is left alone.
2. **The vault is user data.** It is kept by default; deletion needs an explicit
   answer or `--purge-vault`, and only if the folder contains the MEGABRAIN seed
   files (`MAPA.md` and `.obsidian/`).
3. **Existing config is never overwritten.** `settings.json` is backed up first and
   vault seed files are written only if missing.
4. **The installer does not upload user data.** It downloads public installers
   and packages. Third-party tools can have their own telemetry policies; the
   README documents text-to-cad's default telemetry and opt-out command.
5. **Existence checks only.** Agent detection checks that commands/folders exist; it
   never reads their contents.
6. **Protected tool uninstallers run non-destructively.** `codebase-memory-mcp
   uninstall` is invoked with `-n` so that your code indexes are kept.
7. **Plugin ownership is tracked per agent.** Uninstall removes text-to-cad from
   Codex and Claude Code only when MEGABRAIN installed that copy.
8. **REA setup is ownership-aware.** Existing REA registrations or skill are
   preserved. For MEGABRAIN-managed setup, uninstall runs `rea uninstall` without
   data-purge options; it never installs Hopper.

## Extending

- New agent: add a branch to `agent_probe` and the RTK flag mapping in `install.sh`.
- New step: add a `S_begin … S_end` block in `do_install`, and the step to
  `INSTALL_STEPS` in `lib/ui.py`.
