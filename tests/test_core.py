import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from http.server import HTTPServer
from unittest.mock import patch

from trading_agent.kis import KIS, SafeError, NoRedirect
from trading_agent.ledger import Ledger, now
from trading_agent.service import handler, proposal
from trading_agent.cli import publish


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Ledger(str(Path(self.temp.name) / 'test.sqlite3'))

    def test_append_only_and_idempotency(self):
        first = self.db.add('test', {'value': 'synthetic'}, 'run1')
        self.assertEqual(first, self.db.add('test', {'value': 'synthetic'}, 'run1'))
        with self.assertRaises(ValueError):
            self.db.add('test', {'value': 'changed'}, 'run1')
        with self.db.connect() as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute('DELETE FROM events')

    def test_proposal_requires_snapshot_and_cannot_order(self):
        body = dict(request_id='run', strategy_id='draft-v1', strategy_hash='a'*64,
                    note_id='note', snapshot_id='missing', action='HOLD', model='test', prompt_version='v1')
        with self.assertRaises(SafeError):
            proposal(body, self.db)
        body['snapshot_id'] = self.db.add('quote', {'symbol': '000000', 'price': '1'})
        self.assertFalse(proposal(body, self.db)['order_enabled'])
        body['action'] = 'BUY'
        with self.assertRaises(SafeError):
            proposal(body, self.db)

    def test_report_rebuild_preserves_manual_note(self):
        root = Path(self.temp.name)
        manual = root / 'manual.md'
        manual.write_text('keep')
        self.db.add('quote', {'symbol': '000000', 'price': '1.25'})
        report = self.db.report(now()[:10])
        target = publish(root, report)
        self.assertEqual(target, publish(root, report))
        self.assertIn('1.25', Path(target).read_text(encoding='utf-8'))
        self.assertEqual('keep', manual.read_text())
        self.assertIn('산출하지 않음', report['markdown'])

    def test_vts_only(self):
        for value in ('', 'real', 'prod'):
            with self.assertRaises(SafeError):
                KIS({'KIS_ENV': value})
        client = KIS({'KIS_ENV': 'vts'})
        with self.assertRaises(SafeError):
            client.fetch('order')
        with self.assertRaises(SafeError):
            client.fetch('quote', '../secrets')
        with self.assertRaises(SafeError):
            NoRedirect().redirect_request(None, None, None, None, None, None)

    def client(self):
        return KIS(dict(KIS_ENV='vts', KIS_APP_KEY='SYNTHETIC_KEY',
                        KIS_APP_SECRET='SYNTHETIC_SECRET', KIS_CANO='00000000', KIS_PRODUCT_CODE='00'))

    def test_normalization_never_returns_upstream_secrets(self):
        client = self.client()
        def exchange(path, *args, **kwargs):
            if 'tokenP' in path:
                return {'access_token': 'SYNTHETIC_TOKEN', 'expires_in': 3600}, ''
            return {'rt_cd': '0', 'output': {'stck_prpr': '12.50', 'acml_vol': '2',
                                           'private': 'SYNTHETIC_SECRET'}}, ''
        with patch.object(client, 'exchange', side_effect=exchange) as calls:
            result = client.fetch('quote', '000000')
            client.fetch('quote', '000000')
        self.assertNotIn('SYNTHETIC', json.dumps(result))
        self.assertEqual(3, calls.call_count)  # one token for two reads

    def test_auth_failure_cooldown(self):
        client = self.client()
        with patch.object(client, 'exchange', side_effect=SafeError('upstream_unavailable')) as calls:
            with self.assertRaises(SafeError):
                client.authenticate()
            with self.assertRaisesRegex(SafeError, 'authentication_cooldown'):
                client.authenticate()
        self.assertEqual(1, calls.call_count)

    def test_upstream_timeout_and_429_are_sanitized(self):
        for failure, expected in (
            (TimeoutError('SYNTHETIC_SECRET'), 'upstream_unavailable'),
            (URLError('SYNTHETIC_SECRET'), 'upstream_unavailable'),
            (HTTPError('https://example.invalid', 429, 'SYNTHETIC_SECRET', {}, None), 'upstream_rate_limited'),
        ):
            client = self.client()
            with patch.object(client.opener, 'open', side_effect=failure):
                with self.assertRaisesRegex(SafeError, '^' + expected + '$'):
                    client.exchange('/oauth2/tokenP', {}, {}, post=True)

    def test_expired_token_is_renewed(self):
        client = self.client()
        client.token = 'expired'
        client.expires = 0
        with patch.object(client, 'exchange', return_value=({'access_token': 'new-synthetic', 'expires_in': 3600}, '')) as calls:
            client.authenticate()
            client.authenticate()
        self.assertEqual(1, calls.call_count)

    def test_balance_is_connectivity_only_and_marks_partial(self):
        client = self.client()
        with patch.object(client, 'authenticate'), patch.object(client, 'exchange', return_value=(
            {'rt_cd': '0', 'output1': [{'private': 'SYNTHETIC_SECRET'}], 'output2': []}, 'M')):
            client.token = 'SYNTHETIC_TOKEN'
            result = client.fetch('balance')
        self.assertFalse(result['complete'])
        self.assertNotIn('SYNTHETIC', json.dumps(result))

    def test_http_rejects_order_and_sanitizes_exception(self):
        client = KIS({'KIS_ENV': 'vts'})
        server = HTTPServer(('127.0.0.1', 0), handler(client, self.db))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = 'http://127.0.0.1:' + str(server.server_port)
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(base + '/orders', data=b'{}'))
            self.assertEqual(404, error.exception.code)
            with patch.object(client, 'fetch', side_effect=RuntimeError('SYNTHETIC_SECRET')):
                with self.assertRaises(HTTPError) as error:
                    urlopen(base + '/quote?symbol=000000')
            self.assertEqual({'error': 'request_failed'}, json.load(error.exception))
            with urlopen(base + '/health') as response:
                self.assertFalse(json.load(response)['configured'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
