"""Agent-side client: contains no brokerage authentication handling."""
import argparse
import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = 'http://kis-proxy:8080'


def request(route, body=None):
    payload = json.dumps(body).encode() if body is not None else None
    req = Request(BASE + route, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=90) as response:
            return json.load(response)
    except HTTPError as exc:
        # Proxy owns sanitized errors; never print exception URL or arbitrary bodies.
        try:
            code = json.load(exc).get('error', 'proxy_error')
            if not isinstance(code, str) or not code.replace('_', '').isalnum():
                code = 'proxy_error'
        except Exception:
            code = 'proxy_error'
        raise SystemExit(code) from None
    except (URLError, TimeoutError):
        raise SystemExit('proxy_unavailable') from None


def publish(wiki, report):
    root = Path(wiki).resolve(strict=True)
    folder = root / '40_Daily' / 'Generated'
    folder.mkdir(parents=True, exist_ok=True)
    if not folder.resolve().is_relative_to(root):
        raise ValueError('wiki_path_escape')
    destination = folder / (report['date'] + '.md')
    if destination.is_symlink():
        raise ValueError('report_symlink_blocked')
    # Only machine-generated reports are replaced. Manual review notes are separate.
    handle, temporary = tempfile.mkstemp(dir=folder, prefix='.report-')
    try:
        with os.fdopen(handle, 'w', encoding='utf-8') as stream:
            stream.write(report['markdown'])
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return str(destination)


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    commands.add_parser('kis-readonly-smoke')
    commands.add_parser('balance-check')
    for name in ('quote', 'candles'):
        commands.add_parser(name).add_argument('--symbol', required=True)
    item = commands.add_parser('record-proposal')
    item.add_argument('--file', required=True)
    item = commands.add_parser('report')
    item.add_argument('--date', default=datetime.now(timezone(timedelta(hours=9))).date().isoformat())
    item.add_argument('--wiki', default='/knowledge/trading')
    args = parser.parse_args()
    routes = {'status': '/health', 'kis-readonly-smoke': '/smoke', 'balance-check': '/balance'}
    if args.command in routes:
        result = request(routes[args.command])
    elif args.command in ('quote', 'candles'):
        result = request('/' + args.command + '?' + urlencode({'symbol': args.symbol}))
    elif args.command == 'record-proposal':
        with open(args.file, encoding='utf-8') as stream:
            result = request('/proposals', json.load(stream))
    else:
        report = request('/report?' + urlencode({'date': args.date}))
        result = {'path': publish(args.wiki, report), 'events': report['events']}
    print(json.dumps(result, ensure_ascii=False))
    if args.command == 'kis-readonly-smoke' and not result.get('passed'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
