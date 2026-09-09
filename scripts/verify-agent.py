"""Run inside Hermes. Checks metadata only; never opens secret files."""
import os
from pathlib import Path
from trading_agent.cli import request

assert not Path('/run/secrets/kis_env').exists(), 'kis_secret_visible'
assert not Path('/state/ledger.sqlite3').exists(), 'ledger_visible'
assert not Path('/var/run/docker.sock').exists(), 'docker_socket_visible'
assert not any(key.startswith('KIS_') for key in os.environ), 'kis_environment_visible'
assert Path('/workspace/trading-agent/infra/sandbox/.env').stat().st_size == 0, 'sandbox_env_unmasked'
assert not os.access('/workspace/trading-agent/src', os.W_OK), 'source_writable'
assert Path('/knowledge/trading/AGENTS.md').is_file(), 'wiki_instructions_missing'
status = request('/health')
assert status['environment'] == 'vts' and not status['orders_enabled']
print('Agent mount, environment, code-write and private-service checks passed.')
