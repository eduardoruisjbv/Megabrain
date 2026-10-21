#!/usr/bin/env python3
"""Persistent agent jobs over an existing, key-authenticated SSH alias."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

REMOTE = ".local/share/megabrain/mac_worker.py"
LOADER = "from pathlib import Path; import runpy; runpy.run_path(str(Path.home()/" + repr(REMOTE) + "),run_name='__main__')"
BOOTSTRAP = """import json,os; from pathlib import Path
os.umask(0o077)
p=Path.home()/'.local/share/megabrain/mac_worker.py'
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.load(__import__('sys').stdin)['source'],encoding='utf-8')
print(json.dumps({'ok':True,'data':{'installed':str(p)}}))
"""


def ssh_request(config, payload, setup=False):
    host = config["host"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@:-]*", host):
        raise ValueError("Use an SSH alias or user@host, without shell syntax")
    command = " ".join(shlex.quote(x) for x in [config.get("python", "/usr/bin/python3"), "-c", BOOTSTRAP if setup else LOADER])
    # Prompts and context travel as JSON on stdin, never as shell arguments.
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, command],
                            input=json.dumps(payload), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True, timeout=90)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "SSH failed; test key authentication first")
    response = json.loads(result.stdout)
    if not response.get("ok"):
        raise RuntimeError(response.get("error", "Remote worker failed"))
    return response["data"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path.home() / ".config/megabrain/mac-agent.json")
    commands = parser.add_subparsers(dest="action", required=True)
    configure = commands.add_parser("configure", help="save an existing SSH alias; does not connect")
    configure.add_argument("host")
    configure.add_argument("--python", default="/usr/bin/python3")
    commands.add_parser("setup", help="copy the public worker to your Mac over SSH")
    commands.add_parser("doctor", help="check Mac tools and authentication")
    commands.add_parser("list")
    for action in ["start", "resume"]:
        command = commands.add_parser(action)
        if action == "start":
            command.add_argument("agent", choices=["claude", "codex"])
        else:
            command.add_argument("id")
        command.add_argument("--prompt", required=True)
        command.add_argument("--context-file", type=Path)
        command.add_argument("--cwd", help="existing path on the Mac; default is an isolated job workspace")
        command.add_argument("--allow-tool", action="append", default=[], help="Claude only: explicit allowed tool pattern")
    for action in ["status", "logs", "result", "fetch", "stop"]:
        command = commands.add_parser(action)
        command.add_argument("id")
        if action == "fetch":
            command.add_argument("--output", type=Path, required=True)
        if action == "logs":
            command.add_argument("--lines", type=int, default=80)
    args = parser.parse_args(argv)
    if args.action == "configure":
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@:-]*", args.host):
            raise ValueError("Invalid SSH alias")
        args.config.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        args.config.write_text(json.dumps({"host": args.host, "python": args.python}, indent=2) + "\n")
        args.config.chmod(0o600)
        print("Saved. Next: megabrain mac setup, then megabrain mac doctor")
        return 0
    if not args.config.exists():
        raise ValueError("Configure first: megabrain mac configure YOUR_SSH_ALIAS")
    config = json.loads(args.config.read_text())
    payload = {"action": args.action}
    if hasattr(args, "id"):
        payload["id"] = args.id
    if args.action in ["start", "resume"]:
        agent = args.agent if args.action == "start" else ssh_request(config, {"action": "status", "id": args.id})["agent"]
        payload = {"action": "start", "agent": agent, "prompt": args.prompt,
                   "context": args.context_file.read_text() if args.context_file else "",
                   "cwd": args.cwd, "allowed_tools": args.allow_tool}
        if args.action == "resume":
            payload["parent"] = args.id
    if args.action == "logs":
        if not 1 <= args.lines <= 1000:
            raise ValueError("--lines must be between 1 and 1000")
        payload["lines"] = args.lines
    if args.action == "setup":
        payload = {"source": Path(__file__).with_name("mac_worker.py").read_text()}
    data = ssh_request(config, payload, setup=args.action == "setup")
    if args.action == "fetch":
        # Refuse accidental overwrite of a previous export or a symlink target.
        args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
        for name, value in data.items():
            if name not in {"job.json", "prompt.md", "context.md", "result.md", "stderr.log", "events.jsonl"}:
                raise ValueError("Unexpected remote artifact")
            path = args.output / name
            path.write_text(value, encoding="utf-8")
            path.chmod(0o600)
        print(str(args.output))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("MEGABRAIN Mac: " + str(error), file=sys.stderr)
        sys.exit(1)
