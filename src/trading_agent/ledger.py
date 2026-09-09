"""Append-only research ledger; broker orders/fills remain unavailable."""
import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))


def now():
    return datetime.now(KST).isoformat(timespec='seconds')


class Ledger:
    def __init__(self, path):
        self.path = path
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY, created_at TEXT NOT NULL,
                    kind TEXT NOT NULL, payload TEXT NOT NULL,
                    request_id TEXT UNIQUE, request_hash TEXT);
                CREATE TRIGGER IF NOT EXISTS no_update BEFORE UPDATE ON events
                    BEGIN SELECT RAISE(ABORT, 'append_only'); END;
                CREATE TRIGGER IF NOT EXISTS no_delete BEFORE DELETE ON events
                    BEGIN SELECT RAISE(ABORT, 'append_only'); END;
                PRAGMA user_version=1;
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def add(self, kind, payload, request_id=None):
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        digest = hashlib.sha256((kind + raw).encode()).hexdigest()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if request_id:
                old = db.execute('SELECT id,request_hash FROM events WHERE request_id=?', (request_id,)).fetchone()
                if old:
                    if old[1] != digest:
                        raise ValueError('idempotency_conflict')
                    return old[0]
            event = uuid.uuid4().hex
            db.execute('INSERT INTO events VALUES (?,?,?,?,?,?)',
                       (event, now(), kind, raw, request_id, digest))
            return event

    def snapshot_exists(self, event):
        with self.connect() as db:
            return db.execute("SELECT 1 FROM events WHERE id=? AND kind='quote'", (event,)).fetchone() is not None

    def report(self, day):
        with self.connect() as db:
            rows = db.execute('SELECT id,created_at,kind,payload FROM events WHERE substr(created_at,1,10)=? ORDER BY created_at,id', (day,)).fetchall()
        lines = [f'# {day} 조회·판단 기록', '', '모드: 조회 전용 / 전략 미승인 / 주문 비활성화',
                 '손익·수익률: 산출하지 않음. 체결 연동이 아직 없으며 외부 거래 유무도 확인하지 않음.',
                 '기준 시간대: Asia/Seoul. 가격은 조회 시점 값이며 거래소 체결 시각과 다를 수 있음.', '',
                 '## 원장 기록', '']
        for event, created, kind, raw in rows:
            item = json.loads(raw)
            lines.append(f'- `{event}` | {created} | {kind}')
            if kind == 'quote':
                lines.append(f"  - 종목: {item['symbol']}, 조회가격: {item['price']}")
            elif kind == 'proposal':
                lines.append(f"  - 제안: {item['action']}, 전략 문서: [[20_Strategies/{item['strategy_id']}]], 승인: 미확인")
                lines.append(f"  - 근거 노트: [[30_Decisions/{item['note_id']}]], 시세 기록: `{item['snapshot_id']}`")
        if not rows:
            lines.append('- 기록 없음. 실행 성공 또는 휴장으로 추정하지 않음.')
        return {'date': day, 'events': len(rows), 'markdown': '\n'.join(lines) + '\n'}
