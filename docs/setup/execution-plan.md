# 모의투자 Agent 실행계획

작성일: 2026-09-08. 이 문서가 초기 로드맵보다 우선한다. 현재는 계획이며 각 체크박스는 검증 후에만 완료 처리한다.

## 실행 원칙과 현재 상태

- 코드 작업은 `develop`에서 수행한다. `main` 병합은 사용자가 한다.
- 작업자는 각 단계의 구현과 검증을 수행하고, 사용자는 계정 로그인·비밀값 입력·투자 조건 선택을 담당한다.
- 이전 단계의 완료 기준을 통과한 뒤 다음 단계로 진행한다. 실패하면 해당 단계의 대응 절차를 수행한다.
- 8월 19일 컨테이너 정상 실행 이력은 있지만, 9월 8일 점검에서는 Ubuntu 시작 시 `CreateVm/HCS/ERROR_FILE_NOT_FOUND`, Docker 엔진 연결 실패를 확인했다. Ubuntu VHD는 존재한다. 누락 파일은 아직 특정하지 못했다.
- 기존 이미지 정의에는 GUI 브라우저 설치가 없다. 실행 중인 이미지의 실제 설치 상태는 WSL 복구 후 확인한다.
- 기존 `scripts/sandbox.sh`는 존재한다. 아래에서 **구현 대상**으로 표시한 파일·명령은 아직 없으며 먼저 구현해야 한다.
- 시장·종목·원금·판단주기·전략 수치·실제 모의 주문 허용량은 API 확인 후 정한다. 미설정 상태에서는 주문을 거부한다.

## 경로와 실행 위치

| 위치 | 용도 |
|---|---|
| Windows의 기존 `TradingAgent-demo` 체크아웃 | 공개 코드·문서 |
| WSL에서 같은 체크아웃으로 이동한 Bash | Docker 빌드·운영 |
| noVNC의 Sandbox Terminal | 컨테이너 안의 Linux 셸·Hermes 설정 |
| Hermes Desktop의 Remote gateway | 컨테이너의 Agent에 작업 지시 |
| `/workspace/trading-agent` | 컨테이너에 마운트된 코드 |
| `/knowledge/trading` | Vault의 `Projects/Hermes-Paper-Trading` 전용 하위 폴더 |
| `/opt/data` | Hermes 설정·인증·세션용 비공개 named volume |

PowerShell 명령을 Hermes 대화창에 입력하지 않는다. `hermes model`은 Linux 셸 명령이며 대화 입력이 아니다.

## E0. 사전 확인과 보존

작업자, Windows PowerShell에서 기존 체크아웃으로 이동한다.

```powershell
git status --short --branch
git branch --show-current
wsl --version
wsl --status
wsl --list --verbose
docker version
```

1. 브랜치가 `develop`인지 확인한다. 변경 파일이 있으면 소유자와 범위를 확인하고 보존한다.
2. Ubuntu와 Docker Desktop의 데이터 위치·크기를 확인한다. 시스템 복구가 필요하면 Ubuntu VHD와 Docker 데이터 디스크의 오프라인 백업을 먼저 준비한다. 백업 위치는 공개 저장소와 Vault 밖의 비공개 로컬 폴더로 정하고 필요한 여유 공간을 확인한다.
3. 오프라인 복사는 Docker 종료 및 모든 WSL 작업 저장 후 수행한다. Ubuntu 디스크만 보관하면 Hermes named volume까지 백업되는 것은 아니다.
4. 비밀 파일을 출력하는 `docker inspect` 전체 덤프, 렌더링된 Compose 전체 출력, `.env` 출력은 수집하지 않는다.

완료: [ ] 기존 코드·비밀값·Ubuntu·Docker 데이터의 보존 대상과 복구 방법이 확인됨.

## E1. WSL과 Docker 복구

### E1-A. WSL

Windows PowerShell:

```powershell
wsl -d Ubuntu -- /bin/true
```

성공하면 E1-B로 간다. 현재와 같이 실패하면 다음 순서로 진행한다.

1. WSL 작업을 저장하고 Docker Desktop을 종료한다. `wsl --shutdown`은 모든 WSL 배포판을 중지하므로 이 시점에만 실행한다.
2. 관리자 PowerShell에서 아래 명령을 실행한다.

```powershell
wsl --shutdown
wsl --update
```

3. Store 다운로드 실패일 때만 `wsl --update --web-download`로 재시도한다. 재부팅이 요구되면 사용자가 Windows를 재부팅한 뒤 같은 단계에서 재개한다.
4. `wsl -d Ubuntu -- /bin/true`와 `wsl -d Ubuntu -- uname -r`로 재검증한다.
5. 동일 오류가 남으면 WSL 버전, 커스텀 커널 경로 유무, 등록된 VHD 경로 존재 여부, WSL/HCS 이벤트를 조사한다. 오류 코드만으로 VHD 손상이나 특정 파일 누락을 단정하지 않는다.
6. 런타임 복구 설치가 필요하면 E0의 백업 검증 후 해당 버전에 맞는 Microsoft 공식 복구 절차를 확정한다. 이 분기는 원인 확인 전 일괄 자동화하지 않는다.

`wsl --unregister`, 배포판 초기화, Docker factory reset, VHD 삭제는 이 계획의 복구 방법에 포함하지 않는다.

완료: [ ] Ubuntu 명령 실행 성공. 실패 시 여기서 중단하며 브라우저 빌드로 넘어가지 않는다.

### E1-B. Docker

Windows PowerShell:

```powershell
Start-Process -FilePath 'C:\Program Files\Docker\Docker\Docker Desktop.exe' -WindowStyle Hidden
```

Docker Desktop에서 WSL2 engine과 Ubuntu WSL Integration을 활성화한다. 기존 데이터·컨테이너가 보이지 않으면 새 볼륨을 만들기 전에 Docker context와 디스크 설정부터 확인한다.

WSL Ubuntu Bash:

```bash
docker version
docker compose version
docker context show
docker ps -a --filter name=tradingagent-hermes-sandbox
docker volume inspect tradingagent-hermes-data --format '{{.Name}}'
```

완료: [ ] Client와 Server 응답, Compose 사용 가능, 기존 Hermes 볼륨 확인. Docker 소켓 권한 오류를 `chmod 666`으로 우회하지 않는다.

근거: [Microsoft WSL 명령](https://learn.microsoft.com/en-us/windows/wsl/basic-commands), [Docker WSL Integration](https://docs.docker.com/desktop/features/wsl/).

## E2. 브라우저를 포함한 재현 가능한 이미지

이 단계는 **구현 작업**이다. 실행 중인 read-only 컨테이너에 임시 설치하지 않고 아래 파일을 수정한다.

| 파일 | 구현할 변경 |
|---|---|
| `infra/sandbox/Dockerfile` | Debian Chromium, `xdg-utils`, `fonts-dejavu-core`, `fonts-noto-cjk`, `fonts-noto-color-emoji`, UTF-8 지원을 이미지에 포함 |
| `infra/sandbox/docker/cont-init.d/10-novnc-setup` | Sandbox Browser 바로가기 생성, HOME 아래 기본 http/https 브라우저 등록, writable 프로필 폴더 권한 설정 |
| `infra/sandbox/compose.yaml` | UTF-8 locale 명시, 기존 loopback 포트·read-only root·권한 제한 유지 |
| `scripts/sandbox.sh` | `shell`, `setup`, `doctor`를 `hermes` 사용자로 실행하고 필요한 HOME/HERMES_HOME/PATH를 보장 |
| 빌드 설정 | Hermes base image를 검증된 digest로 고정하고 버전 기록. `latest`에 따른 의도치 않은 Hermes 업그레이드 방지 |

Chromium은 `hermes` 사용자, `DISPLAY=:1`, 영구 프로필 `/opt/data/.config/chromium`으로 실행한다. 기본 브라우저 지정도 같은 사용자의 설정으로 적용한다. 사용자 namespace와 Chromium sandbox가 현재 컨테이너 제약에서 작동하는지 먼저 확인한다. 실행 실패 시 `--no-sandbox`를 기본값으로 추가하지 말고 원인을 조사하며, 해결 전에는 Windows 브라우저의 기기 코드 인증으로 다음 인증 작업을 수행할 수 있다.

WSL Bash, 저장소 루트에서 변경 후 실행:

```bash
bash -n scripts/sandbox.sh scripts/validate-public-repo.sh
./scripts/sandbox.sh bootstrap
./scripts/sandbox.sh validate
./scripts/sandbox.sh build
./scripts/sandbox.sh up
docker ps --filter name=tradingagent-hermes-sandbox
```

기존 `.env`가 있으면 bootstrap이 재생성하지 않는다. 이미지 digest 적용 방식에 맞게 build argument와 예제 설정도 함께 변경한다. 빌드 실패 시 기존 볼륨은 유지하고 마지막 검증 이미지로 재기동한다.

브라우저 수동 검증은 noVNC의 Sandbox Terminal에서 수행한다.

```bash
id -un
locale
command -v chromium
xdg-settings get default-web-browser
xdg-open https://example.com
```

완료 기준:

- [ ] `hermes` 사용자이며 HTTPS 페이지가 noVNC 화면에 표시됨.
- [ ] 터미널 링크 클릭으로 동일 브라우저가 열림. 한글·상자 문자가 읽힘.
- [ ] 컨테이너 healthy, 6080/9119만 호스트 loopback에 노출됨. 5901과 브라우저 디버깅 포트는 공개하지 않음.
- [ ] 재시작 후 브라우저 설정과 Hermes 기존 데이터가 유지됨.
- [ ] 브라우저 화면 검증과 서비스 health 검증 결과를 따로 기록함.

GUI 브라우저 설치만으로 Hermes 브라우저 자동화 도구가 연결되는 것은 아니다. 해당 도구는 필요 시 별도 구성·검증한다. REST 기반 첫 MVP의 필수 요소는 아니다. [Hermes Browser 문서](https://hermes-agent.nousresearch.com/docs/user-guide/features/browser)

## E3. Hermes 인증과 Desktop 연결

사용자, noVNC Sandbox Terminal의 Linux 셸에서:

```bash
/opt/hermes/.venv/bin/hermes --version
/opt/hermes/.venv/bin/hermes model
```

1. 사용할 공급자를 선택한다. 이전에 시도했던 Codex를 계속 쓰면 OpenAI Codex/ChatGPT Subscription 항목을 선택한다. 이름은 설치 버전에 따라 다를 수 있다.
2. 안내된 기기 코드 URL을 Linux 또는 Windows 브라우저에서 열고 사용자가 직접 승인한다. 대기 중인 터미널은 종료하지 않는다.
3. 모델 선택까지 완료한 뒤 `hermes`를 실행하여 짧은 응답을 확인한다. 인증 성공만으로 추론 성공을 판정하지 않는다.
4. Hermes Desktop Remote gateway에 `http://127.0.0.1:9119`를 등록한다. 로그인 값은 사용자가 로컬 시크릿 파일에서 직접 사용한다.
5. Desktop에서 `pwd`, `id -un` 실행과 `/knowledge/trading`의 비공개 테스트 노트 작성을 지시한다. Windows에서 해당 노트가 나타나는지 확인한다. 공개 로그에는 내용 대신 성공 여부만 남긴다.
6. 재시작 전 대화를 저장하고, 컨테이너 재시작 후 Desktop 재접속과 짧은 응답을 다시 확인한다.

실패 분기: 기기 코드 만료/취소 → 셸에서 `hermes model` 재실행. `command not found` → 위 절대 경로 사용 후 PATH 수정. 인증됐지만 추론 실패 → 공급자·모델 사용 권한·응답 오류 확인. 같은 인증을 무한 반복하지 않는다.

완료: [ ] CLI 추론, Desktop 추론, 컨테이너 도구 실행, Vault 쓰기, 재시작 후 인증 유지 모두 통과.

[Hermes 공급자 설정](https://hermes-agent.nousresearch.com/docs/integrations/providers/)은 셸의 `hermes model`과 대화 중 `/model`의 역할을 구분한다.

## E4. KIS 조회 전용 연결

사용자 준비: KIS 모의투자 이용 신청, 모의투자용 App Key/Secret과 모의계좌 준비. 값은 채팅·Markdown·Vault에 입력하지 않는다.

**구현 대상:** `src/trading_agent/broker_proxy/`, `schemas/`, `tests/`, `pyproject.toml`과 lockfile.

1. 별도 `kis-proxy` 서비스에만 KIS 비밀값을 주입한다. 시크릿 원본은 Agent에 마운트된 저장소 밖에 두고 proxy에만 읽기 전용으로 마운트한다. proxy에는 Vault·Hermes 상태·Docker 소켓을 마운트하지 않는다.
2. Hermes의 tool/skill이 proxy의 허용된 조회 인터페이스만 사용하도록 연결한다. 초기에는 proxy에 주문 route 자체를 만들지 않는다.
3. 모의 환경을 명시하지 않으면 시작 실패. VTS host와 API/TR allowlist를 검증하고 실전 주소로 자동 전환하지 않는다. 이 제어는 일반 Agent가 수정 가능한 파일만으로 강제한다고 주장하지 않는다.
4. 토큰 만료 캐시, 동시 발급 잠금, 요청 큐·제한, 타임아웃, 제한된 재시도를 구현한다. 조회 재시도와 향후 주문 재시도를 분리한다.
5. 토큰 발급 → 사용자 선택 테스트 종목 현재가 → 봉 데이터 → 모의 잔고 순서로 조회한다. 여기서 선택한 종목은 전략 대상 확정이 아니다.
6. API별 환경 지원·TR ID·호출 한도·조회 가능 기간·휴장 응답을 공식 문서와 소량 조회로 확인한다. 토큰을 매 요청마다 재발급하지 않는다.

**구현할 검증 명령 계약:** 다음 명령이 작동하도록 CLI를 만들고 테스트한다. 현재 실행 가능한 명령으로 취급하지 않는다.

```bash
uv run pytest tests/unit tests/contracts
uv run python -m trading_agent.cli kis-readonly-smoke
```

smoke는 별도 비공개 설정에서 테스트 종목을 읽고, 인증·현재가·봉·모의 잔고의 성공 여부/지연/정규화 오류만 출력한다. 주문·계좌값·잔고 원문은 출력하지 않는다. 실데이터는 비공개 데이터 볼륨에 저장한다.

완료: [ ] 조회 4종 통과, 비밀값 로그 없음, 만료·429/제한 오류·타임아웃 테스트 통과, 공식 지원 표 작성. 모의환경에서 필요한 API가 미지원이면 그 기능을 제외하고 사용자에게 제약을 제시한다.

근거: [KIS 공식 샘플](https://github.com/koreainvestment/open-trading-api). 샘플의 실전 기본값을 그대로 실행하지 않는다. API 호출량 제한과 주문 건수 정책을 따로 기록한다.

## E5. 투자 조건과 비공개 지식 구조 확정

작업자는 E4 결과로 후보별 필요한 호출 수·예상 지연·모의환경 제약을 계산하고, 사용자가 시장·대상·원금·판단주기·주문 상한·비용 가정을 선택한다. 선택 전에는 임의 기본값을 활성화하지 않는다.

호출 예산 = 종목 수 × 종목당 조회 수 × 판단 횟수 + 계좌/체결 대조 + 토큰/재시도 여유. LLM 호출 수와 비용도 별도 계산한다.

전용 `/knowledge/trading` 아래 `00_Home`, `10_Strategies`, `20_Decisions`, `30_Trades`, `40_Reviews`, `90_Templates`를 만든다. 계좌 식별자 대신 내부 별칭을 쓴다.

승인 전략에는 ID·버전·승인 상태·적용일을 둔다. 실행마다 전략 내용 hash, 시세 snapshot ID, 지표 버전, 모델/프롬프트 버전을 결정에 연결한다. LLM 응답의 완전한 재현성을 보장하지 않고, 결정론적 계산 재현성과 LLM 결정 일치율을 구분한다.

완료: [ ] 사용자 선택이 비공개 설정에 저장됨, 누락 설정 시 주문 불가, 노트 간 ID 연결과 템플릿 검증 통과.

## E6. 주문 전 개발과 Shadow 검증

**구현 대상:** `market_data`, `strategy`, `risk`, `journal`, `evaluation`, `orchestration` 모듈 및 단위/통합 테스트.

1. 공개 스키마: candle, signal, decision, order_intent, order, fill, position. 금액은 Decimal, 시각은 timezone 포함, 모든 객체에 내부 ID를 둔다.
2. 승인 전략을 결정론적 코드로 계산하고 Hermes는 JSON Schema에 맞춘 판단 제안만 한다. 잘못된 JSON, 오래된 시세, 승인되지 않은 전략, 누락 값이면 주문 불가.
3. Risk Gate와 주문 중지 기능을 proxy 실행 경계에 둔다. Agent가 proxy 운영 코드·시크릿·정책을 바꿀 수 없도록 배포와 권한을 분리한다.
4. 판단 주기별 실행 ID·잠금·만료를 두고 재시작 시 실행 중 상태를 복구한다. 시장 캘린더, 장 시간, 지연 시세를 검증한다.
5. 이벤트 DB를 기록의 원본으로 두고 Obsidian은 재생성 가능한 문서로 만든다. DB commit과 outbox로 노트 작성 실패를 재시도한다.
6. 순차 데이터 백테스트, 미래 정보 참조 방지, 비용·슬리피지, 벤치마크 계산을 검증한다. 회고가 승인 전략을 자동 변경하지 않게 한다.
7. Hermes Cron을 수동 테스트한 동일 진입점에 연결한다. cron과 별도 scheduler가 같은 일을 중복 실행하지 않게 한다. Windows 절전/재부팅 중 실행을 보장하지 않으며 깨어난 뒤 과거 주문을 몰아서 내지 않는다.

구현할 명령 계약: `uv run pytest`, `uv run python -m trading_agent.cli run-once --mode shadow`. shadow는 합성 입력 테스트와 실제 조회 테스트를 구분하여 기록하고 주문 호출이 0인지 검증한다.

완료: [ ] 최소 5거래일 Shadow 기록, 중복 실행·시세 누락·잘못된 JSON·Vault 쓰기 실패·프로세스 재시작 시험 통과. 기간은 전략 성과 증명의 의미가 아니다.

## E7. 모의 주문 활성화와 운영

E6 통과 후 사용자가 확정한 모의 주문 정책으로만 활성화한다.

1. proxy에 VTS 주문·취소·조회 allowlist를 추가한다. 도메인과 TR ID 불일치를 거부한다.
2. 내부 결정 ID에 unique constraint와 주문 상태 머신을 둔다. 내부 ID를 KIS가 멱등 키로 처리한다고 가정하지 않는다.
3. 전송 직후 타임아웃이면 `UNKNOWN` 상태로 저장하고 주문/체결 조회로 대조한다. 확인 전 재전송을 금지한다. 미해결이면 신규 주문을 중지한다.
4. 사용자 정책 내 최소 단위 모의 주문 1건으로 접수 → 조회 → 체결 또는 취소를 확인한다. 시장 종료면 다음 유효 세션까지 대기하며 체결을 만들어내지 않는다.
5. 부분 체결·거부·취소 경합·재시작 후 대조를 테스트한다. 중지 기능은 신규 주문을 막고 기존 주문 조회·취소는 유지한다.
6. 운영 평가 목표는 최소 20거래일로 두고 매일 결정/주문/체결/DB/Vault 일치 여부를 확인한다. 주간 성과와 오류를 분리해서 검토한다.

완료: [ ] 중복 주문 0, 원인 없는 상태 불일치 0, 모든 거래의 전략/시세/판단 추적 가능, 중지 기능 검증. 실패하면 주문 비활성화 후 조회·대조만 유지한다.

## E8. 공개 기록과 인수인계

각 단계마다 `docs/progress/`에 목표·변경·검증·한계·다음 작업을 적는다. 실제 전략, 계좌, 인증 URL의 코드, 원시 거래/P&L, Vault 내용을 포함하지 않는다.

```bash
./scripts/validate-public-repo.sh
git diff --check
git diff --cached --check
git diff --cached
```

기존 검사 스크립트는 보조 검사이며 모든 비밀값 유출을 탐지하지 않는다. 스테이징된 변경과 이미지·첨부는 별도 검토한다. 검증한 변경만 `develop`에 커밋·푸시하고 `main`은 사용자가 확인 후 병합한다.

첫 실행 작업은 E0/E1이다. 첫 환경 마일스톤은 E3 완료이며, 첫 투자 시스템 마일스톤은 E6의 조회 → 판단 → 비공개 기록이다.
