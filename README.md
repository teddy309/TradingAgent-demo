# TradingAgent Demo

증권거래 전략 수립, 모의투자, 결과 리포트 작성을 자동화하는 Hermes Agent 실험 프로젝트입니다.

현재 단계의 목표는 실제 투자 전략이나 수익률 공개가 아니라 다음 실행 기반을 재현 가능하게 만드는 것입니다.

- WSL2에서 실행되는 격리형 Linux/Hermes 환경
- 로컬 전용 noVNC 화면
- Windows Hermes Desktop에서 연결하는 원격 Hermes Dashboard
- 컨테이너 내부 Gateway와 Cron
- 프로젝트 저장소와 전용 Obsidian 하위 폴더만 허용하는 파일 경계
- 개인정보·계좌정보·전략을 제외한 공개 개발 기록

## Architecture

```text
Windows
├─ Hermes Desktop ─────────────── http://127.0.0.1:9119
├─ Browser ────────────────────── http://127.0.0.1:6080/vnc.html
└─ WSL2 / Docker Desktop
   └─ tradingagent-hermes-sandbox
      ├─ Hermes Dashboard / Gateway / Cron
      ├─ XFCE + TigerVNC + noVNC
      ├─ /workspace/trading-agent  → this repository
      ├─ /knowledge/trading        → dedicated private Obsidian folder
      └─ /opt/data                 → private Hermes state volume
```

Only ports 9119 and 6080 are published, and both are bound to Windows loopback.
The raw VNC port, Docker socket, and Hermes API port are not exposed.

## Quick start

기존 환경 복구 또는 다음 개발 작업을 시작할 때는 [실행계획](docs/setup/execution-plan.md)의 E0부터 따른다. 아래 명령만으로 GUI 브라우저 추가와 전체 모의투자 시스템 구현이 완료되지는 않는다.

Run from Ubuntu in WSL2:

```bash
./scripts/sandbox.sh bootstrap
./scripts/sandbox.sh validate
./scripts/sandbox.sh build
./scripts/sandbox.sh up
./scripts/sandbox.sh status
```

Then open:

- noVNC: http://127.0.0.1:6080/vnc.html?autoconnect=1&resize=scale
- Hermes Dashboard: http://127.0.0.1:9119

Passwords are generated locally in the ignored file `infra/sandbox/.env`.
Do not copy that file into issues, commits, screenshots, or chat.

Full instructions: [Linux sandbox setup](docs/setup/linux-sandbox.md)

## Public documentation policy

This repository may contain architecture, schemas, synthetic examples, tests, runbooks, ADRs, and sanitized progress notes. It must not contain brokerage keys, account details, raw transactions, portfolio values, private strategy rules, or Obsidian content.

See [Public sharing guide](docs/operations/public-sharing.md) and [Security policy](SECURITY.md).
# KIS / SQLite / Wiki quick entry

The read-only research foundation is available. Start with [the private setup runbook](docs/runbooks/kis-wiki.md)
and [the Hermes workflow](docs/agent/trading-wiki.md). KIS keys go outside this checkout, never in its sandbox `.env`.
Live KIS verification requires user-entered VTS inputs. Orders and performance evaluation are not enabled.
