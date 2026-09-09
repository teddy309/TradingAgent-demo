"""Narrow VTS-only client. Never forward upstream bodies or exception strings."""
import json
import re
import threading
import time
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

BASE = 'https://openapivts.koreainvestment.com:29443'
ROUTES = {
    'quote': ('/uapi/domestic-stock/v1/quotations/inquire-price', 'FHKST01010100'),
    'candles': ('/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice', 'FHKST03010100'),
    'balance': ('/uapi/domestic-stock/v1/trading/inquire-balance', 'VTTC8434R'),
}


class SafeError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise SafeError('upstream_redirect_blocked')


def settings(path):
    result = {}
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            key, sep, value = line.partition('=')
            if not sep or key in result:
                raise SafeError('invalid_settings')
            result[key.strip()] = value.strip()
    if result.get('KIS_ENV') != 'vts':
        raise SafeError('vts_required')
    return result


def number(value):
    value = str(value)
    if not re.fullmatch(r'-?\d{1,20}(\.\d{1,8})?', value):
        raise SafeError('invalid_upstream_number')
    return str(Decimal(value))


class KIS:
    def __init__(self, config):
        if config.get('KIS_ENV') != 'vts':
            raise SafeError('vts_required')
        self.config = config
        self.lock = threading.RLock()
        self.token = None
        self.expires = 0
        self.last_request = 0
        self.next_auth = 0
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def ready(self):
        return (all(self.config.get(k) for k in ('KIS_APP_KEY', 'KIS_APP_SECRET'))
                and bool(re.fullmatch(r'\d{8}', self.config.get('KIS_CANO', '')))
                and bool(re.fullmatch(r'\d{2}', self.config.get('KIS_PRODUCT_CODE', ''))))

    def exchange(self, path, params, headers, post=False):
        # Only called with code-owned routes. No caller-controlled host, path or headers.
        time.sleep(max(0, 1.1 - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        body = json.dumps(params).encode() if post else None
        url = BASE + path + (('?' + urlencode(params)) if not post else '')
        req = Request(url, data=body, headers={'Content-Type': 'application/json', **headers})
        try:
            with self.opener.open(req, timeout=15) as response:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise SafeError('upstream_too_large')
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise SafeError('upstream_schema_error')
                return data, response.headers.get('tr_cont', '')
        except HTTPError as exc:
            raise SafeError('upstream_rate_limited' if exc.code == 429 else 'upstream_http_error') from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise SafeError('upstream_unavailable') from None

    def authenticate(self):
        with self.lock:
            if not self.ready():
                raise SafeError('configuration_required')
            if self.token and time.time() < self.expires:
                return
            if time.monotonic() < self.next_auth:
                raise SafeError('authentication_cooldown')
            self.next_auth = time.monotonic() + 65
            data, _ = self.exchange('/oauth2/tokenP', {
                'grant_type': 'client_credentials',
                'appkey': self.config['KIS_APP_KEY'],
                'appsecret': self.config['KIS_APP_SECRET'],
            }, {}, post=True)
            token_value = data.get('access_token')
            lifetime = int(data.get('expires_in', 0))
            if not isinstance(token_value, str) or lifetime <= 120:
                raise SafeError('authentication_failed')
            self.token = token_value
            self.expires = time.time() + min(lifetime, 86400) - 120

    def fetch(self, kind, symbol=''):
        with self.lock:
            if kind not in ROUTES:
                raise SafeError('route_not_allowed')
            if kind != 'balance' and not re.fullmatch(r'\d{6}', symbol):
                raise SafeError('six_digit_symbol_required')
            self.authenticate()
            params = {'FID_COND_MRKT_DIV_CODE': 'J', 'FID_INPUT_ISCD': symbol}
            if kind == 'candles':
                today = date.today()
                params.update(FID_INPUT_DATE_1=(today-timedelta(days=90)).strftime('%Y%m%d'),
                              FID_INPUT_DATE_2=today.strftime('%Y%m%d'),
                              FID_PERIOD_DIV_CODE='D', FID_ORG_ADJ_PRC='0')
            if kind == 'balance':
                params = dict(CANO=self.config['KIS_CANO'],
                              ACNT_PRDT_CD=self.config['KIS_PRODUCT_CODE'], AFHR_FLPR_YN='N',
                              OFL_YN='', INQR_DVSN='02', UNPR_DVSN='01', FUND_STTL_ICLD_YN='N',
                              FNCG_AMT_AUTO_RDPT_YN='N', PRCS_DVSN='00',
                              CTX_AREA_FK100='', CTX_AREA_NK100='')
            path, transaction = ROUTES[kind]
            headers = {'authorization': 'Bearer ' + self.token,
                       'appkey': self.config['KIS_APP_KEY'],
                       'appsecret': self.config['KIS_APP_SECRET'], 'tr_id': transaction, 'custtype': 'P'}
            data, continuation = self.exchange(path, params, headers)
            if data.get('rt_cd') != '0':
                if data.get('msg_cd') in ('EGW00123', 'EGW00121'):
                    self.token = None
                raise SafeError('kis_request_rejected')
            if kind == 'quote':
                row = data['output']
                return {'symbol': symbol, 'price': number(row['stck_prpr']),
                        'volume': number(row['acml_vol']), 'market_timestamp': None}
            if kind == 'candles':
                rows = []
                for row in data['output2']:
                    day = row['stck_bsop_date']
                    if not re.fullmatch(r'\d{8}', day):
                        raise SafeError('invalid_upstream_date')
                    rows.append({'date': day, **{k: number(row[v]) for k, v in {
                        'open': 'stck_oprc', 'high': 'stck_hgpr', 'low': 'stck_lwpr',
                        'close': 'stck_clpr', 'volume': 'acml_vol'}.items()}})
                return {'symbol': symbol, 'adjusted': True, 'candles': rows,
                        'scope': 'single_page_last_90_calendar_days_max_100_rows'}
            # Balance stays in the service: only connectivity/page completeness is exposed.
            if not isinstance(data.get('output1'), list) or not isinstance(data.get('output2'), list):
                raise SafeError('upstream_schema_error')
            return {'connected': True, 'complete': continuation not in ('F', 'M'),
                    'scope': 'connectivity_only_no_holdings_or_pnl_exported'}
