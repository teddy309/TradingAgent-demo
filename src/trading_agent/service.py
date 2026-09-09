"""Private Docker-network service: allowlisted queries and unapproved proposals."""
import json
import os
import re
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qs
from .kis import KIS, SafeError, settings
from .ledger import Ledger, now


def proposal(body, ledger):
    fields = {'request_id', 'strategy_id', 'strategy_hash', 'note_id', 'snapshot_id', 'action', 'model', 'prompt_version'}
    if not isinstance(body, dict) or set(body) != fields:
        raise SafeError('proposal_schema_error')
    for key in fields - {'action'}:
        if not isinstance(body[key], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', body[key]):
            raise SafeError('proposal_identifier_error')
    if not re.fullmatch(r'[a-f0-9]{64}', body['strategy_hash']):
        raise SafeError('strategy_hash_required')
    if body['action'] not in ('BUY_CANDIDATE', 'SELL_CANDIDATE', 'HOLD'):
        raise SafeError('proposal_action_error')
    if not ledger.snapshot_exists(body['snapshot_id']):
        raise SafeError('snapshot_not_found')
    return {'event_id': ledger.add('proposal', body, body['request_id']),
            'order_enabled': False, 'approval': 'unverified', 'source': 'llm_proposal_not_execution'}


def handler(kis, ledger):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(20)

        def log_message(self, *args):
            pass

        def respond(self, status, body):
            raw = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(raw)

        def dispatch(self):
            if self.headers.get('Origin'):
                raise SafeError('browser_requests_blocked')
            parsed = urlsplit(self.path)
            query = parse_qs(parsed.query)
            if self.command == 'POST':
                if parsed.path != '/proposals' or parsed.query:
                    return 404, {'error': 'route_not_allowed'}
                if self.headers.get_content_type() != 'application/json':
                    raise SafeError('json_required')
                size = int(self.headers.get('Content-Length', '0'))
                if size < 1 or size > 4096:
                    raise SafeError('invalid_body_size')
                return 200, proposal(json.loads(self.rfile.read(size)), ledger)
            if parsed.path == '/health':
                return 200, {'status': 'ok', 'configured': kis.ready(), 'environment': 'vts',
                             'orders_enabled': False, 'mode': 'readonly'}
            if parsed.path == '/smoke':
                symbol = kis.config.get('KIS_TEST_SYMBOL', '')
                if not re.fullmatch(r'\d{6}', symbol):
                    raise SafeError('test_symbol_required')
                checks = {}
                for kind in ('auth', 'quote', 'candles', 'balance'):
                    try:
                        if kind == 'auth':
                            kis.authenticate()
                        else:
                            data = kis.fetch(kind, symbol)
                            if kind == 'candles' and not data['candles']:
                                raise SafeError('empty_candles')
                        checks[kind] = 'ok'
                    except SafeError as exc:
                        checks[kind] = str(exc)
                        break
                return 200, {'checks': checks, 'passed': len(checks) == 4 and all(v == 'ok' for v in checks.values()), 'orders_enabled': False}
            if parsed.path in ('/quote', '/candles', '/balance'):
                if set(query) - {'symbol'} or any(len(v) != 1 for v in query.values()):
                    raise SafeError('invalid_query')
                kind = parsed.path[1:]
                data = kis.fetch(kind, query.get('symbol', [''])[0])
                data['fetched_at'] = now()
                data['event_id'] = ledger.add(kind, data)
                return 200, data
            if parsed.path == '/report':
                day = query.get('date', [''])[0]
                if date.fromisoformat(day).isoformat() != day:
                    raise SafeError('invalid_date')
                return 200, ledger.report(day)
            return 404, {'error': 'route_not_allowed'}

        def do_GET(self):
            try:
                status, body = self.dispatch()
            except SafeError as exc:
                status, body = 400, {'error': str(exc)}
            except Exception:
                # Exception text / upstream payload / configuration must never leave service.
                status, body = 500, {'error': 'request_failed'}
            self.respond(status, body)

        do_POST = do_GET
    return Handler


def main():
    os.umask(0o077)
    try:
        kis = KIS(settings('/run/secrets/kis_env'))
        ledger = Ledger('/state/ledger.sqlite3')
    except Exception:
        raise SystemExit('service_initialization_failed') from None
    server = HTTPServer(('0.0.0.0', 8080), handler(kis, ledger))
    server.timeout = 20
    server.serve_forever()


if __name__ == '__main__':
    main()
