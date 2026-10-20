#!/usr/bin/env python3
"""MEGABRAIN terminal UI.

Renders the animated brain + progress panel and drives the interactive
Yes/No selector. It is a pure *renderer*: it never installs, downloads or
deletes anything. The installer (install.sh) streams events to it.

Real mode (used by install.sh):
    ui.py --events FILE --answers FILE [--version X] [--watch-pid PID]

Preview mode (nothing is installed, nothing is written):
    ui.py --demo                 install flow with the Obsidian question
    ui.py --demo --installed     "already installed" + uninstall flow
    ui.py --demo --fast          shorter timings
    ui.py --demo --yes | --no    answer the questions automatically

Event protocol: one tab-separated line per event, see docs/ARCHITECTURE.md.
Standard library only (Python 3.6+).
"""
import argparse
import os
import platform
import select
import shutil
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brain_energize import frame as brain_frame, prepare  # noqa: E402

FPS = 12
RIGHT_W = 62
GAP = 4
BAR_W = 16
HEIGHT = 24
AUTHOR_TAG = "by VONKOENIG.EDUARDORUI"
TITLE_TEXT = "M E G A  ·  B R A I N"
TITLE_RULE = "━" * len(TITLE_TEXT)

CODES = {"bold": "1", "dim": "2", "inverse": "7", "red": "31", "green": "32",
         "yellow": "33", "cyan": "36"}

# (key, label, context shown while running)
INSTALL_STEPS = [
    ("environment", "Environment", "curl, git, node, npm, disk space"),
    ("agents", "Agents", "scanning for coding agents"),
    ("rtk", "RTK", "token-optimized command proxy"),
    ("graft", "graft", "repository context graph"),
    ("cbm", "codebase-memory", "structural graph · sqlite engine"),
    ("rea", "REA", "reverse engineering tools · MCP + agent skill"),
    ("claude-mem", "claude-mem", "persistent memory · worker + vector store"),
    ("superpowers", "superpowers", "process skills pack"),
    ("ecc", "ECC", "agents, skills and hooks · profile standard"),
    ("text-to-cad", "text-to-cad", "local CAD tools for Codex and Claude Code"),
    ("claude-code-setup", "Claude Code setup", "project-specific automation recommendations"),
    ("vault", "Vault", "memory backup vault"),
    ("wiring", "Wiring", "memory sync, CLI and manifest"),
]
UNINSTALL_STEPS = [
    ("sync", "Sync timer", "stopping the 48h memory sync"),
    ("rtk", "RTK", "removing hooks and binary"),
    ("graft", "graft", "removing MCP server and package"),
    ("cbm", "codebase-memory", "removing binary and agent configs"),
    ("rea", "REA", "removing MEGABRAIN-managed registrations and skill"),
    ("claude-mem", "claude-mem", "removing plugin (data kept)"),
    ("superpowers", "superpowers", "removing plugin"),
    ("ecc", "ECC", "removing plugin"),
    ("claude-code-setup", "Claude Code setup", "removing plugin"),
    ("text-to-cad", "text-to-cad", "removing Codex and Claude Code plugins"),
    ("vault", "Vault", "your memories are kept unless you say so"),
    ("marker", "Marker", "removing manifest and CLI"),
]


# --------------------------------------------------------------------------
# colour
# --------------------------------------------------------------------------
INTERACTIVE = sys.stdout.isatty()
COLOR = INTERACTIVE and not os.environ.get("NO_COLOR")


def paint(parts):
    plain = "".join(t for t, _ in parts)
    if not COLOR:
        return plain, plain
    out = ""
    for text, style in parts:
        if style:
            out += "\033[%sm%s\033[0m" % (";".join(CODES[s] for s in style.split()), text)
        else:
            out += text
    return plain, out


BLANK = paint([("", "")])


def bar_text(f):
    n = int(round(BAR_W * f))
    return "█" * n + "░" * (BAR_W - n)


def mmss(s):
    s = int(s)
    return "%02d:%02d" % (s // 60, s % 60)


# --------------------------------------------------------------------------
# state
# --------------------------------------------------------------------------
class Step(object):
    def __init__(self, key, label, ctx):
        self.key, self.label, self.ctx = key, label, ctx
        self.state = "pending"      # pending | running | done | skipped | failed
        self.disp = 0.0
        self.t0 = 0.0


class State(object):
    def __init__(self, version):
        self.version = version
        self.mode = "install"       # install | uninstall | installed
        self.steps = [Step(*s) for s in INSTALL_STEPS]
        self.meta = {}
        self.log = []
        self.ask = None             # dict while a question is open
        self.task = None            # dict while a bottom task (Obsidian) runs
        self.final = None           # list of (text, style) rows
        self.t_start = 0.0
        self.t_final = None
        self.quit = False
        self.present = set()

    # -- events ------------------------------------------------------------
    def apply(self, ev, now):
        cmd, args = ev[0], ev[1:]
        if cmd == "mode" and args:
            self.mode = args[0]
            catalog = UNINSTALL_STEPS if self.mode == "uninstall" else INSTALL_STEPS
            self.steps = [Step(*s) for s in catalog]
            self.log, self.final, self.task, self.ask = [], None, None, None
            self.t_start = now
        elif cmd == "meta" and len(args) >= 2:
            self.meta[args[0]] = args[1]
            if args[0] == "present":
                self.present = set(x for x in args[1].split(",") if x)
        elif cmd == "begin" and args:
            st = self._step(args[0])
            if st:
                st.state, st.t0 = "running", now
                if len(args) > 1 and args[1]:
                    st.ctx = args[1]
        elif cmd == "log" and len(args) >= 2:
            self.log.append("%s: %s" % (self._label(args[0]), args[1]))
            self.log = self.log[-12:]
        elif cmd == "done" and args:
            st = self._step(args[0])
            if st:
                st.state = "done"
        elif cmd == "skip" and args:
            st = self._step(args[0])
            if st:
                st.state = "skipped"
            if len(args) > 1 and args[1]:
                self.log.append("%s: %s" % (self._label(args[0]), args[1]))
        elif cmd == "fail" and args:
            st = self._step(args[0])
            if st:
                st.state = "failed"
            if len(args) > 1 and args[1]:
                self.log.append("%s: ✖ %s" % (self._label(args[0]), args[1]))
        elif cmd == "ask" and len(args) >= 6:
            self.ask = {"id": args[0], "headline": args[1], "line1": args[2],
                        "line2": args[3], "question": args[4],
                        "choice": args[5] == "yes"}
        elif cmd == "task" and args:
            self.task = {"title": args[0], "detail": args[1] if len(args) > 1 else "",
                         "msg": "", "disp": 0.0, "done": False, "t0": now}
        elif cmd == "tasklog" and args and self.task:
            self.task["msg"] = args[0]
        elif cmd == "taskdone" and self.task:
            self.task["done"] = True
        elif cmd == "final" and len(args) >= 2:
            style = {"ok": "green bold", "warn": "yellow bold", "fail": "red bold"}.get(args[0], "bold")
            rows = [(args[1], style)]
            rows += [(t, "dim") for t in args[2:6]]
            self.final, self.t_final, self.task, self.ask = rows, now, None, None
        elif cmd == "quit":
            self.quit = True

    def _step(self, key):
        for s in self.steps:
            if s.key == key:
                return s
        return None

    def _label(self, key):
        st = self._step(key)
        return st.label if st else key

    # -- animation ---------------------------------------------------------
    def tick(self, now):
        for s in self.steps:
            if s.state == "running":
                target = 0.93 * (1.0 - 2.718 ** (-(now - s.t0) / 2.2))
            elif s.state in ("done", "skipped", "failed"):
                target = 1.0
            else:
                target = 0.0
            s.disp += (target - s.disp) * 0.28
            if abs(target - s.disp) < 0.004:
                s.disp = target
        if self.task:
            t = self.task
            target = 1.0 if t["done"] else 0.9 * (1.0 - 2.718 ** (-(now - t["t0"]) / 2.5))
            t["disp"] += (target - t["disp"]) * 0.28


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
def toggle_row(question, yes):
    return paint([
        ("  %s   " % question, ""),
        ("[ ● Yes ]" if yes else "[ ○ Yes ]", "green bold inverse" if yes else "dim"),
        ("  ", ""),
        ("[ ● No ]" if not yes else "[ ○ No ]", "yellow bold inverse" if not yes else "dim"),
    ])


def bottom_rows(st, now):
    if st.final:
        rows = [paint([(t[:RIGHT_W], s)]) for t, s in st.final]
    elif st.ask:
        a = st.ask
        head_style = "yellow bold" if st.mode == "uninstall" else "green bold"
        rows = [
            paint([(a["headline"][:RIGHT_W], head_style)]),
            paint([(a["line1"][:RIGHT_W - 2], "bold")]),
            paint([("  " + a["line2"][:RIGHT_W - 4], "dim")]),
            toggle_row(a["question"], a["choice"]),
            paint([("  ← → / Tab / y n to choose · Enter to confirm", "dim")]),
        ]
    elif st.task:
        t = st.task
        rows = [
            paint([("✔ Installation complete", "green bold")]),
            paint([(t["title"][:RIGHT_W - 2], "bold")]),
            paint([("  " + t["detail"][:RIGHT_W - 4], "dim")]),
            paint([("  ", ""), ("[%s] " % bar_text(t["disp"]), "cyan"),
                   ("%3d%%" % round(t["disp"] * 100), "")]),
            paint([("  " + t["msg"][:RIGHT_W - 4], "dim")]),
        ]
    else:
        last = st.log[-3:]
        while len(last) < 3:
            last.insert(0, "")
        rows = [paint([("log · %s" % mmss(max(0.0, now - st.t_start)), "dim")])]
        for m in last:
            rows.append(paint([("  " + m[:RIGHT_W - 4], "dim")] if m else [("", "")]))
        done_all = all(s.state in ("done", "skipped", "failed") for s in st.steps)
        word = "Removal" if st.mode == "uninstall" else "Installation"
        rows.append(paint([("✔ %s complete" % word, "green bold")] if done_all else [("", "")]))
    while len(rows) < 5:
        rows.append(BLANK)
    return rows[:5]


def right_panel(st, now):
    label = {"install": "installer", "uninstall": "uninstaller", "installed": "status"}[st.mode]
    sub = {
        "install": "token-saving + memory stack · memory backup vault",
        "uninstall": "removes only what MEGABRAIN installed · data kept",
        "installed": "MEGABRAIN is set up on this machine",
    }[st.mode]
    rows = [
        paint([(TITLE_TEXT, "cyan bold")]),
        paint([(TITLE_RULE, "cyan"), ("  " + AUTHOR_TAG, "dim")]),
        BLANK,
        paint([(label, "bold"), ("  ·  v%s" % st.version, "dim")]),
        paint([(sub, "dim")]),
        BLANK,
    ]
    context = ""
    present = 0
    for s in st.steps:
        if st.mode == "installed":
            is_present = s.key in st.present
            present += 1 if is_present else 0
            sym, sym_style = ("✔", "green") if is_present else ("·", "dim")
            f = 1.0 if is_present else 0.0
            rows.append(paint([
                (" %s " % sym, sym_style),
                ("%-17s" % s.label, "bold" if is_present else "dim"),
                ("[%s] " % bar_text(f), "cyan" if is_present else "dim"),
                ("%3d%%" % round(f * 100), ""),
            ]))
            continue
        if s.state == "running":
            context = s.ctx
        sym, sym_style = {
            "done": ("✔", "green"), "running": ("▸", "cyan"), "pending": ("·", "dim"),
            "skipped": ("–", "dim"), "failed": ("✖", "red"),
        }[s.state]
        active = s.state in ("done", "running", "failed")
        tail = " skip" if s.state == "skipped" else "%3d%%" % round(s.disp * 100)
        rows.append(paint([
            (" %s " % sym, sym_style),
            ("%-17s" % s.label, "bold" if active else "dim"),
            ("[%s] " % bar_text(s.disp), "cyan" if active else "dim"),
            (tail, "dim" if s.state == "skipped" else ""),
        ]))

    rows += [BLANK] * max(0, 16 - len(rows))      # keep the layout stable
    rows = rows[:16]
    rows.append(paint([("   → " + context, "dim")] if context else [("", "")]))
    if st.mode == "installed":
        rows.append(paint([(" Components        ", "bold"),
                           ("%d / %d installed" % (present, len(st.steps)), "")]))
    else:
        overall = sum(s.disp for s in st.steps) / float(len(st.steps))
        rows.append(paint([(" Overall          ", "bold"),
                           ("[%s] " % bar_text(overall), "cyan"),
                           ("%3d%%" % round(overall * 100), "")]))
    rows.append(BLANK)
    rows += bottom_rows(st, now)
    return rows[:HEIGHT] + [BLANK] * max(0, HEIGHT - len(rows))


def compose(n, st, now, dots, dist, cols):
    text = right_panel(st, now)
    brain = brain_frame(dots, dist, n)
    brain_w = len(dots[0]) // 2
    if cols >= brain_w + GAP + RIGHT_W:
        out = []
        for i in range(HEIGHT):
            b = brain[i] if i < len(brain) else ""
            _, colored = text[i]
            out.append(b + " " * (brain_w - len(b) + GAP) + colored)
        return out
    return brain + [""] + [c for _, c in text]    # narrow terminal: stacked


# --------------------------------------------------------------------------
# event sources
# --------------------------------------------------------------------------
class FileSource(object):
    def __init__(self, events_path, answers_path):
        self.path, self.answers, self.pos, self.buf = events_path, answers_path, 0, b""

    def poll(self, now):
        try:
            with open(self.path, "rb") as f:
                f.seek(self.pos)
                data = f.read()
        except (IOError, OSError):
            return []
        self.pos += len(data)
        self.buf += data
        parts = self.buf.split(b"\n")
        self.buf = parts.pop()
        return [p.decode("utf-8", "replace").split("\t") for p in parts if p]

    def answer(self, qid, yes):
        try:
            with open(self.answers, "a") as f:
                f.write("%s\t%s\n" % (qid, "yes" if yes else "no"))
        except (IOError, OSError):
            pass


class DemoSource(object):
    """Scripted timeline that mimics what install.sh would emit."""

    def __init__(self, scenario, scale, agents, os_label, obsidian_cmd):
        self.scale = scale
        self.agents, self.os_label, self.obsidian_cmd = agents, os_label, obsidian_cmd
        self.gen = self._install() if scenario == "install" else self._installed()
        self.wake = 0.0
        self.waiting = False
        self.reply = None

    def answer(self, qid, yes):
        self.reply = yes

    def poll(self, now):
        out = []
        while True:
            try:
                if self.waiting:
                    if self.reply is None:
                        return out
                    reply, self.reply, self.waiting = self.reply, None, False
                    step = self.gen.send(reply)
                elif now < self.wake:
                    return out
                else:
                    step = next(self.gen)
            except StopIteration:
                return out
            kind = step[0]
            if kind == "emit":
                out.append(step[1])
            elif kind == "wait":
                self.wake = now + step[1] * self.scale
                return out
            elif kind == "ask":
                out.append(["ask"] + list(step[1]))
                self.waiting = True
                return out

    # -- scripts -----------------------------------------------------------
    @staticmethod
    def _run_steps(steps):
        for key, dur, logs in steps:
            yield ("emit", ["begin", key])
            spent = 0.0
            for frac, msg in logs:
                yield ("wait", dur * (frac - spent))
                spent = frac
                yield ("emit", ["log", key, msg])
            yield ("wait", dur * (1 - spent))
            yield ("emit", ["done", key])

    def _install(self):
        ag = ", ".join(self.agents)
        yield ("emit", ["mode", "install"])
        steps = [
            ("environment", 1.8, [(0.4, "curl, git, node, npm detected"), (0.85, "disk check: space available")]),
            ("agents", 2.0, [(0.4, "detected: " + ag), (0.85, "plan: install for all detected agents")]),
            ("rtk", 2.3, [(0.3, "fetching rtk binary"), (0.6, "installing to ~/.local/bin/rtk"), (0.85, "rtk init -g: hooks registered")]),
            ("graft", 2.8, [(0.3, "npm install -g @nanonets/graft"), (0.6, "mcp server graft registered"), (0.85, "statusline + hooks ready")]),
            ("cbm", 3.2, [(0.3, "fetching codebase-memory-mcp"), (0.6, "verifying checksum: ok"), (0.85, "hook-augment wired for detected clients")]),
            ("rea", 2.4, [(0.3, "installing rea-agents CLI if needed"), (0.65, "configuring detected clients"), (0.9, "MCP registrations and skill ready")]),
            ("claude-mem", 2.8, [(0.3, "adding marketplace thedotmack/claude-mem"), (0.6, "starting worker and vector store"), (0.85, "memory database initialized (empty)")]),
            ("superpowers", 1.8, [(0.4, "adding marketplace claude-plugins-official"), (0.85, "plugin superpowers enabled")]),
            ("ecc", 2.6, [(0.3, "adding marketplace affaan-m/ECC"), (0.6, "resolving agents and skills"), (0.85, "hook profile: standard")]),
            ("text-to-cad", 2.8, [(0.3, "adding official marketplace for detected agents"), (0.65, "installing CAD tools and viewer plugin"), (0.9, "ready on first Codex or Claude Code session")]),
            ("claude-code-setup", 1.8, [(0.4, "adding Anthropic marketplace"), (0.85, "read-only setup recommendations enabled")]),
            ("vault", 3.2, [(0.15, "creating hidden vault ~/.megabrain/vault"), (0.4, "PARA tree: Inbox · Projetos · Áreas · Recursos · Arquivo"),
                            (0.65, "seeding MAPA.md, AGENTS.md, Templates/"), (0.88, "writing .obsidian/graph.json")]),
            ("wiring", 2.5, [(0.25, "installing memory sync script"), (0.5, "sync timer armed: every 48h"),
                             (0.75, "installing the `megabrain` command"), (0.92, "manifest written")]),
        ]
        for step in self._run_steps(steps):
            yield step
        yes = yield ("ask", ["obsidian", "✔ Installation complete",
                             "Obsidian (optional) · " + self.os_label,
                             self.obsidian_cmd, "Install Obsidian now?", "yes"])
        if yes:
            yield ("emit", ["task", "Installing Obsidian", self.obsidian_cmd])
            for msg in ["resolving package source", "downloading Obsidian",
                        "installing runtime and app", "registering desktop entry"]:
                yield ("wait", 1.0)
                yield ("emit", ["tasklog", msg])
            yield ("wait", 0.8)
            yield ("emit", ["taskdone"])
            yield ("wait", 0.8)
            yield ("emit", ["final", "ok", "✔ Obsidian installed",
                            "  vault: ~/.megabrain/vault (hidden)",
                            "  open Obsidian → Open folder as vault → Graph view",
                            "  run `megabrain` any time to check or uninstall"])
        else:
            yield ("emit", ["final", "warn", "Obsidian skipped",
                            "  install later: " + self.obsidian_cmd,
                            "  vault is ready at ~/.megabrain/vault",
                            "  plain Markdown: use it with any app you like"])

    def _installed(self):
        yield ("emit", ["mode", "installed"])
        yield ("emit", ["meta", "present",
                        "environment,agents,rtk,graft,cbm,rea,claude-mem,superpowers,ecc,text-to-cad,claude-code-setup,vault,wiring"])
        yes = yield ("ask", ["uninstall", "MEGABRAIN already installed",
                             "v1.0.2 · installed 2026-10-20 · " + ", ".join(self.agents),
                             "removes only what MEGABRAIN installed · vault is kept",
                             "Uninstall MEGABRAIN?", "no"])
        if not yes:
            yield ("emit", ["final", "ok", "✔ Nothing changed",
                            "  run `megabrain uninstall` whenever you want"])
            return
        yield ("emit", ["mode", "uninstall"])
        steps = [
            ("sync", 1.4, [(0.5, "systemd timer disabled")]),
            ("rtk", 1.8, [(0.4, "rtk init --uninstall: claude"), (0.8, "binary removed")]),
            ("graft", 1.8, [(0.4, "mcp server removed"), (0.8, "npm uninstall -g @nanonets/graft")]),
            ("cbm", 1.8, [(0.5, "agent configs removed"), (0.8, "indexes kept")]),
            ("rea", 1.6, [(0.4, "managed registrations and skill removed"), (0.8, "REA data kept")]),
            ("claude-mem", 1.6, [(0.5, "plugin removed (data kept)")]),
            ("superpowers", 1.2, [(0.5, "plugin removed")]),
            ("ecc", 1.4, [(0.5, "plugin removed")]),
            ("claude-code-setup", 1.2, [(0.5, "plugin removed")]),
            ("text-to-cad", 1.6, [(0.3, "Claude Code plugin removed when managed"), (0.75, "Codex plugin removed when managed")]),
        ]
        for step in self._run_steps(steps):
            yield step
        purge = yield ("ask", ["vault_purge", "Your memory vault", "~/.megabrain/vault",
                               "plain Markdown · default is to keep it",
                               "Delete the vault too?", "no"])
        yield ("emit", ["begin", "vault"])
        yield ("wait", 1.0)
        yield ("emit", ["log", "vault", "deleted" if purge else "kept"])
        yield ("emit", ["done", "vault"])
        yield ("emit", ["begin", "marker"])
        yield ("wait", 1.0)
        yield ("emit", ["done", "marker"])
        yield ("wait", 0.6)
        yield ("emit", ["final", "ok", "✔ MEGABRAIN uninstalled",
                        "  vault: " + ("deleted" if purge else "kept at ~/.megabrain/vault"),
                        "  indexes kept in ~/.cache/codebase-memory-mcp",
                        "  reinstall any time with install.sh"])


# --------------------------------------------------------------------------
# keyboard + detection helpers
# --------------------------------------------------------------------------
def parse_keys(data):
    """Turn raw bytes into a list of key names. One read() may hold several keys
    (fast typing, paste, slow frame), so every byte must be consumed."""
    keys, i = [], 0
    while i < len(data):
        chunk = data[i:i + 3]
        if chunk in (b"\x1b[D", b"\x1bOD"):
            keys.append("left"); i += 3
        elif chunk in (b"\x1b[C", b"\x1bOC"):
            keys.append("right"); i += 3
        elif data[i:i + 1] == b"\x1b":
            i += 1                                   # lone ESC / unsupported sequence
        else:
            b = data[i:i + 1]; i += 1
            if b == b"\x03":
                raise KeyboardInterrupt
            if b in (b"h",):
                keys.append("left")
            elif b in (b"l",):
                keys.append("right")
            elif b in (b"\t", b" "):
                keys.append("toggle")
            elif b in (b"y", b"Y", b"s", b"S"):
                keys.append("yes")
            elif b in (b"n", b"N"):
                keys.append("no")
            elif b in (b"\r", b"\n"):
                keys.append("enter")
    return keys


def read_keys(fd, timeout):
    ready, _, _ = select.select([fd], [], [], timeout)
    if not ready:
        return []
    return parse_keys(os.read(fd, 64))


def detect_agents():
    probes = [("claude", "claude", ".claude"), ("codex", "codex", ".codex"),
              ("gemini", "gemini", ".gemini"), ("cursor", "cursor", ".cursor"),
              ("opencode", "opencode", ".config/opencode")]
    home, found = os.path.expanduser("~"), []
    for name, cmd, folder in probes:
        if shutil.which(cmd) or os.path.isdir(os.path.join(home, folder)):
            found.append(name)
    return found or ["claude"]


def detect_os():
    system = platform.system()
    if system == "Darwin":
        return "macOS", "brew install --cask obsidian"
    label = "Linux"
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    label = line.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    label = label.replace(" (GNOME Edition)", "")[:30]
    if shutil.which("flatpak"):
        return label, "flatpak install -y --user flathub md.obsidian.Obsidian"
    if shutil.which("snap"):
        return label, "snap install obsidian --classic"
    return label, "download Obsidian from obsidian.md/download"


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------
# main loop
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="MEGABRAIN terminal UI (renderer only)")
    ap.add_argument("--events")
    ap.add_argument("--answers")
    ap.add_argument("--version", default="1.0.2")
    ap.add_argument("--watch-pid", type=int, default=0)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--installed", action="store_true")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--no", action="store_true")
    args = ap.parse_args()

    auto = True if args.yes else (False if args.no else None)
    scale = 0.15 if args.fast else 1.0
    hold = 0.8 if args.fast else 2.5

    if args.demo:
        label, cmd = detect_os()
        source = DemoSource("installed" if args.installed else "install", scale,
                            detect_agents(), label, cmd)
    elif args.events and args.answers:
        source = FileSource(args.events, args.answers)
    else:
        ap.error("use --demo, or --events and --answers")

    dots, dist = prepare(1)
    cols = shutil.get_terminal_size((130, 40)).columns
    st = State(args.version)

    if not INTERACTIVE:        # piped output: print a single representative frame
        if args.demo:
            now = 0.0
            for _ in range(400):
                now += 1000.0
                for ev in source.poll(now):
                    st.apply(ev, now)
                if st.ask or st.final:
                    break
            for _ in range(80):
                st.tick(now)
        print("\n".join(compose(0, st, 0.0, dots, dist, cols)))
        return 0

    fd, saved = None, None
    try:
        import termios
        import tty
        fd = os.open("/dev/tty", os.O_RDONLY)
        saved = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    except Exception:
        fd = None

    def restore():
        try:
            if saved is not None and fd is not None:
                import termios
                termios.tcsetattr(fd, termios.TCSADRAIN, saved)
        except Exception:
            pass
        sys.stdout.write("\033[0m\033[?25h\n")
        sys.stdout.flush()

    def on_term(signum, _frame):
        restore()
        os._exit(1)

    signal.signal(signal.SIGTERM, on_term)

    sys.stdout.write("\033[?25l\033[2J\033[3J\033[H")
    n = 0
    t0 = time.time()
    auto_at = None
    try:
        while True:
            now = time.time() - t0
            for ev in source.poll(now):
                st.apply(ev, now)
            st.tick(now)

            if st.ask and auto is not None:
                auto_at = auto_at or now + 0.7 * max(scale, 0.3)
                if now >= auto_at:
                    st.ask["choice"] = auto
                    source.answer(st.ask["id"], auto)
                    st.ask, auto_at = None, None
            elif st.ask and fd is None:       # no keyboard available: take the default
                source.answer(st.ask["id"], st.ask["choice"])
                st.ask = None

            lines = compose(n, st, now, dots, dist, cols)
            sys.stdout.write("\033[H" + "".join("%s\033[K\n" % l for l in lines) + "\033[J")
            sys.stdout.flush()
            n += 1

            if st.quit:
                break
            if st.final and now - st.t_final >= hold:
                break
            if args.watch_pid and not st.final and not alive(args.watch_pid):
                break

            if st.ask and fd is not None:
                for key in read_keys(fd, 1.0 / FPS):
                    a = st.ask
                    if a is None:
                        break
                    if key in ("left", "right", "toggle"):
                        a["choice"] = not a["choice"]
                    elif key == "yes":
                        a["choice"] = True
                    elif key == "no":
                        a["choice"] = False
                    elif key == "enter":
                        source.answer(a["id"], a["choice"])
                        st.ask = None
            else:
                time.sleep(1.0 / FPS)
    except KeyboardInterrupt:
        pass
    finally:
        restore()
    return 0


if __name__ == "__main__":
    sys.exit(main())
