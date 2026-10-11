#!/usr/bin/python3
"""Single-worker persistent task queue, controlled through paired SSH."""
import argparse
from contextlib import contextmanager
import json
import os
import resource
import signal
import sqlite3
import subprocess
import time
import uuid
from pathlib import Path

HOME = Path('/home/companion')
STATE = HOME / '.local/state/gamehack-worker'


@contextmanager
def database():
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(STATE / 'jobs.sqlite', timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, command TEXT, state TEXT, created REAL, finished REAL, exit_code INTEGER, cancel INTEGER DEFAULT 0)')
    db.commit()
    try:
        with db:
            yield db
    finally:
        db.close()


def submit(command):
    if not command or len(command) > 2048 or '\x00' in command:
        raise ValueError('Task must contain 1–2048 characters')
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute("SELECT count(*) FROM jobs WHERE state IN ('queued','running')").fetchone()[0] >= 20:
            raise ValueError('Queue full (20 active jobs)')
        identifier = uuid.uuid4().hex
        db.execute('INSERT INTO jobs (id,command,state,created) VALUES (?,?,?,?)', (identifier, command, 'queued', time.time()))
    return identifier


def job_id(value):
    if len(value) != 32 or any(char not in '0123456789abcdef' for char in value):
        raise ValueError('Invalid job ID')
    return value


def stop(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
    except ProcessLookupError:
        pass


def task_limits():
    resource.setrlimit(resource.RLIMIT_FSIZE, (262144, 262144))


def daemon():
    with database() as db:
        db.execute("UPDATE jobs SET state='interrupted',finished=? WHERE state='running'", (time.time(),))
    while True:
        with database() as db:
            db.execute("UPDATE jobs SET state='cancelled',finished=? WHERE state='queued' AND cancel=1", (time.time(),))
            row = db.execute("SELECT * FROM jobs WHERE state='queued' ORDER BY created LIMIT 1").fetchone()
            if row:
                db.execute("UPDATE jobs SET state='running' WHERE id=?", (row['id'],))
        if not row:
            time.sleep(1)
            continue
        process = None
        state, code = 'failed', 1
        try:
            with (STATE / (row['id'] + '.log')).open('wb') as output:
                process = subprocess.Popen(['/bin/sh', '-c', row['command']], cwd=HOME / 'shared', stdout=output, stderr=subprocess.STDOUT, start_new_session=True, preexec_fn=task_limits)
                start = time.monotonic()
                state = 'done'
                while process.poll() is None:
                    with database() as db:
                        cancelled = db.execute('SELECT cancel FROM jobs WHERE id=?', (row['id'],)).fetchone()[0]
                    if cancelled:
                        state = 'cancelled'
                    elif time.monotonic() - start > 120:
                        state = 'timed-out'
                    elif output.tell() > 262144:
                        state = 'output-limit'
                    if state != 'done':
                        stop(process)
                        break
                    time.sleep(0.2)
                code = process.wait()
                if state == 'done' and code:
                    state = 'failed'
            # Fast producers can overshoot between polls: truncate saved output.
            with (STATE / (row['id'] + '.log')).open('r+b') as output:
                output.truncate(min(output.seek(0, 2), 262144))
        except Exception as exc:
            if process and process.poll() is None:
                stop(process)
            (STATE / (row['id'] + '.log')).write_text(str(exc))
        with database() as db:
            db.execute('UPDATE jobs SET state=?,finished=?,exit_code=? WHERE id=?', (state, time.time(), code, row['id']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['daemon', 'submit', 'jobs', 'result', 'cancel'])
    parser.add_argument('value', nargs='?')
    args = parser.parse_args()
    if args.action == 'daemon':
        daemon()
    elif args.action == 'submit':
        print(json.dumps({'job': submit(args.value or ''), 'state': 'queued'}))
    elif args.action == 'jobs':
        with database() as db:
            print(json.dumps([dict(row) for row in db.execute('SELECT id,state,created,finished,exit_code,cancel FROM jobs ORDER BY created DESC LIMIT 50')], indent=2))
    else:
        identifier = job_id(args.value or '')
        with database() as db:
            row = db.execute('SELECT * FROM jobs WHERE id=?', (identifier,)).fetchone()
            if not row:
                raise ValueError('Job not found')
            if args.action == 'cancel':
                db.execute('UPDATE jobs SET cancel=1 WHERE id=?', (identifier,))
                print('Cancellation requested; worker stops the task process group.')
            else:
                print(json.dumps({key: row[key] for key in ('id', 'state', 'exit_code')}, indent=2))
                output = STATE / (identifier + '.log')
                if output.exists():
                    with output.open('rb') as stream:
                        print(stream.read(12000).decode(errors='replace'))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        print('Worker error:', exc)
        raise SystemExit(1)
