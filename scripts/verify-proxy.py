"""Run through stdin inside proxy; no secret contents or DB records printed."""
import os
import sqlite3
from pathlib import Path

assert os.getuid() == 10001
assert os.access('/run/secrets/kis_env', os.R_OK), 'secret_unreadable'
assert not os.access('/run/secrets/kis_env', os.W_OK), 'secret_writable'
assert not Path('/knowledge/trading').exists(), 'wiki_visible'
assert not Path('/workspace/trading-agent').exists(), 'repo_visible'
assert not Path('/var/run/docker.sock').exists(), 'docker_socket_visible'
assert not any(key.startswith('KIS_') for key in os.environ), 'secret_in_environment'
with sqlite3.connect('/state/ledger.sqlite3') as db:
    assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
print('Proxy user, secret mount, isolation and SQLite integrity checks passed.')
