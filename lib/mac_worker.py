#!/usr/bin/python3
"""Run persistent Claude/Codex jobs behind the user's SSH connection."""
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path.home() / 'Developer' / 'AgentTasks'
os.environ['PATH'] = str(Path.home() / '.local/bin') + ':/opt/homebrew/bin:/usr/local/bin:' + os.environ.get('PATH', '')
os.umask(0o077)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, data):
    temporary = path.with_name(path.name + '.tmp-' + str(os.getpid()))
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    os.replace(str(temporary), str(path))


def job_dir(job_id):
    if not re.fullmatch(r'[0-9]{8}-[0-9]{6}-[a-f0-9]{8}', job_id):
        raise ValueError('Invalid job ID')
    directory = ROOT / job_id
    if not (directory / 'job.json').is_file():
        raise ValueError('Job not found: ' + job_id)
    return directory


def command_output(args, timeout=20):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return {'exit_code': result.returncode, 'output': (result.stdout + result.stderr).strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'exit_code': -1, 'output': str(exc)}


def doctor():
    tools = {}
    for name in ['codex', 'claude']:
        executable = shutil.which(name)
        info = {'executable': executable, 'authenticated': False}
        if executable:
            info['version'] = command_output([executable, '--version'])
            args = [executable, 'login', 'status'] if name == 'codex' else [executable, 'auth', 'status']
            auth = command_output(args)
            if name == 'claude':
                try:
                    info['authenticated'] = bool(json.loads(auth['output']).get('loggedIn'))
                except ValueError:
                    pass
            else:
                info['authenticated'] = auth['exit_code'] == 0
            # Do not return account identifiers or credentials.
            info['auth_exit_code'] = auth['exit_code']
        tools[name] = info
    memory = command_output(['/usr/sbin/sysctl', '-n', 'hw.memsize'])
    return {'host': command_output(['/bin/hostname'])['output'], 'home': str(Path.home()),
            'tasks_root': str(ROOT), 'memory_bytes': memory['output'], 'tools': tools}


def owns_runner(pid, job_id):
    result = command_output(['/bin/ps', '-p', str(pid), '-o', 'command='])
    command = result['output']
    return (result['exit_code'] == 0 and str(Path(__file__).resolve()) in command
            and '--run ' + job_id in command)


def status(job_id):
    directory = job_dir(job_id)
    meta = json.loads((directory / 'job.json').read_text())
    if meta['status'] in ['queued', 'running'] and meta.get('pid') and not owns_runner(meta['pid'], job_id):
        meta['status'] = 'interrupted'
        meta['error'] = 'Supervisor is no longer running; inspect the logs.'
        save(directory / 'job.json', meta)
    return meta


def start(request):
    agent = request['agent']
    if agent not in ['claude', 'codex']:
        raise ValueError('Agent must be claude or codex')
    executable = shutil.which(agent)
    if not executable:
        raise ValueError(agent + ' is not installed in the SSH PATH')
    prompt = request.get('prompt', '').strip()
    if not prompt:
        raise ValueError('A nonempty prompt is required')
    parent = status(request['parent']) if request.get('parent') else None
    if parent:
        if parent['status'] in ['queued', 'running']:
            raise ValueError('The previous turn is still running')
        if parent['agent'] != agent or not parent.get('session_id'):
            raise ValueError('The previous turn has no resumable session for this agent')
    job_id = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-') + uuid.uuid4().hex[:8]
    directory = ROOT / job_id
    cwd_value = request.get('cwd') or (parent['cwd'] if parent else '')
    if cwd_value:
        cwd = Path(cwd_value).expanduser().resolve()
        if not cwd.is_dir():
            raise ValueError('Remote working directory does not exist: ' + str(cwd))
    else:
        cwd = directory / 'workspace'
    directory.mkdir(parents=True)
    if not cwd_value:
        cwd.mkdir()
        subprocess.run(['/usr/bin/git', 'init', '-q', str(cwd)], check=True)
    context = request.get('context', '')
    if not context and parent:
        context = (job_dir(parent['id']) / 'context.md').read_text()
    (directory / 'prompt.md').write_text(prompt + '\n')
    (directory / 'context.md').write_text(context)
    meta = {'id': job_id, 'agent': agent, 'status': 'queued', 'created_at': now(),
            'cwd': str(cwd), 'directory': str(directory), 'parent': request.get('parent'),
            'resume_session': parent.get('session_id') if parent else None,
            'allowed_tools': request.get('allowed_tools', [])}
    save(directory / 'job.json', meta)
    with (directory / 'supervisor.log').open('ab') as log:
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--run', job_id],
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   start_new_session=True, close_fds=True)
    # The runner writes its own PID. Do not race its metadata write here.
    meta['launched_pid'] = process.pid
    return meta


def parse_events(directory, agent):
    session_id = None
    result = None
    agent_error = None
    for line in (directory / 'events.jsonl').read_text(errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        session_id = event.get('session_id') or event.get('thread_id') or session_id
        if agent == 'claude' and event.get('type') == 'result':
            result = event.get('result') or '\n'.join(event.get('errors', []))
            if event.get('is_error'):
                agent_error = result or event.get('subtype', 'Claude reported an error')
        if agent == 'codex' and event.get('type') in ['turn.failed', 'error']:
            agent_error = event.get('error') or event.get('message') or event
    if result:
        (directory / 'result.md').write_text(result + '\n')
    return session_id, agent_error


def run(job_id):
    directory = job_dir(job_id)
    meta = json.loads((directory / 'job.json').read_text())
    meta.update(status='running', pid=os.getpid(), started_at=now())
    save(directory / 'job.json', meta)
    cancelled = False

    def cancel(signum, frame):
        nonlocal cancelled
        cancelled = True

    signal.signal(signal.SIGTERM, cancel)
    signal.signal(signal.SIGINT, cancel)
    context = (directory / 'context.md').read_text()
    prompt = (directory / 'prompt.md').read_text()
    payload = ('Shared project context from the PC:\n' + context + '\n\n' if context else '') + prompt
    executable = shutil.which(meta['agent'])
    if meta['agent'] == 'codex':
        command = [executable, '-a', 'never', '-s', 'workspace-write', 'exec']
        if meta.get('resume_session'):
            command += ['resume', meta['resume_session']]
        command += ['--json',
                    '--output-last-message', str(directory / 'result.md'), '-']
    else:
        command = [executable, '-p', '--output-format', 'stream-json', '--verbose',
                   '--permission-mode', 'acceptEdits']
        if meta.get('resume_session'):
            command += ['--resume', meta['resume_session']]
        for tool in meta['allowed_tools']:
            command += ['--allowedTools', tool]
    meta['command'] = command
    save(directory / 'job.json', meta)
    exit_code = -1
    try:
        with (directory / 'events.jsonl').open('wb') as output, (directory / 'stderr.log').open('wb') as error:
            process = subprocess.Popen(command, cwd=meta['cwd'], stdin=subprocess.PIPE,
                                       stdout=output, stderr=error, close_fds=True)
            process.stdin.write(payload.encode())
            process.stdin.close()
            while process.poll() is None:
                if cancelled:
                    process.terminate()
                    try:
                        process.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        process.kill()
                time.sleep(0.2)
            exit_code = process.wait()
        session_id, agent_error = parse_events(directory, meta['agent'])
        meta['session_id'] = session_id
        if agent_error:
            meta['error'] = agent_error
        meta['status'] = 'cancelled' if cancelled else ('completed' if exit_code == 0 and not agent_error else 'failed')
    except Exception as exc:
        meta['status'] = 'cancelled' if cancelled else 'failed'
        meta['error'] = str(exc)
    meta.update(exit_code=exit_code, ended_at=now())
    save(directory / 'job.json', meta)


def read_tail(path, lines=80):
    if not path.exists():
        return ''
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size - 131072))
        return '\n'.join(stream.read().decode(errors='replace').splitlines()[-lines:])


def dispatch(request):
    action = request['action']
    if action == 'doctor':
        return doctor()
    if action == 'start':
        return start(request)
    if action == 'list':
        jobs = []
        for path in sorted(ROOT.glob('*/job.json'), reverse=True):
            try:
                jobs.append(status(path.parent.name))
            except (ValueError, KeyError, OSError):
                continue  # not a MEGABRAIN job directory, or unreadable metadata
            if len(jobs) == 50:
                break
        return jobs
    directory = job_dir(request['id'])
    meta = status(request['id'])
    if action == 'status':
        return meta
    if action == 'logs':
        return {name: read_tail(directory / name, request.get('lines', 80))
                for name in ['events.jsonl', 'stderr.log', 'supervisor.log']}
    if action == 'result':
        return {'job': meta, 'result': (directory / 'result.md').read_text() if (directory / 'result.md').exists() else ''}
    if action == 'fetch':
        names = ['job.json', 'prompt.md', 'context.md', 'result.md', 'stderr.log', 'events.jsonl']
        return {name: (directory / name).read_text(errors='replace') for name in names if (directory / name).is_file()}
    if action == 'stop':
        if meta['status'] in ['queued', 'running']:
            pid = meta.get('pid')
            if not pid:
                raise ValueError('Job is still starting; retry stop shortly')
            # Only signal the detached process group created by this runner.
            if not owns_runner(pid, meta['id']) or os.getpgid(pid) != pid:
                raise ValueError('Supervisor process group changed; refusing to signal')
            os.killpg(pid, signal.SIGTERM)
            return {'id': meta['id'], 'status': 'stop_requested'}
        return meta
    raise ValueError('Unknown action: ' + action)


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--run':
        run(sys.argv[2])
    else:
        try:
            response = {'ok': True, 'data': dispatch(json.load(sys.stdin))}
        except Exception as exc:
            response = {'ok': False, 'error': str(exc)}
        print(json.dumps(response, ensure_ascii=False))
