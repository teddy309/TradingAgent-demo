# KIS 조회와 Wiki 운영

## 최초 준비 (호스트에서만)

저장소의 부모 폴더에 `.private/kis.env`를 생성하고 `infra/kis/.env.example`의 빈 항목을 직접 채운다.
이 파일은 저장소, Vault, Hermes 마운트 밖에 있어야 한다. 기존 파일은 덮어쓰지 않는다.
현재 로컬 설치에서는 빈 파일을 준비해 두었다. `.env` 파일은 암호화 저장소가 아니므로
호스트 사용자와 관리자에게는 접근 가능하다. 폴더 ACL은 호스트 소유자의 전체 권한과
Docker 실행에 필요한 SYSTEM 읽기 권한으로 제한한다. 초기 파일 생성에 사용한
작업 도구 계정의 별도 접근 권한은 제거했다. 호스트 사용자 권한으로 실행되는 도구와 관리자는 여전히 신뢰 대상이다.
Docker 시작 실패 시 비밀값을 출력하지 말고 파일 접근 권한과 마운트만 확인한다.

필수 입력: 모의용 `KIS_APP_KEY`, `KIS_APP_SECRET`, 모의계좌 앞 8자리 `KIS_CANO`,
뒤 2자리 `KIS_PRODUCT_CODE`. `KIS_ENV=vts`는 유지한다.
`KIS_TEST_SYMBOL`에는 조회를 시험할 국내주식 6자리 코드를 직접 선택한다.
고객명, 이메일, HTS ID, 계좌 비밀번호는 이 REST 조회 구현에 입력하지 않는다.
원시 값은 따옴표 없이 `=` 오른쪽에 붙여 넣고 저장한다. 채팅으로 전달하지 않는다.

WSL Bash에서 저장소 루트로 이동한 뒤:

```bash
docker compose --env-file infra/sandbox/.env -f infra/sandbox/compose.yaml up -d --build kis-proxy
# 이미 실행 중인 서비스에 입력값 변경을 적용할 때:
docker compose --env-file infra/sandbox/.env -f infra/sandbox/compose.yaml restart kis-proxy
```

키 파일을 수정한 뒤 새 inode로 저장하는 편집기를 썼다면 `up -d --force-recreate kis-proxy`로
다시 마운트한다. Hermes/Obsidian 화면에 키 파일을 열지 않는다. 이미지 재빌드나 Docker 제어는
호스트에서만 수행한다. Agent는 실행 중인 proxy 코드나 DB 파일에 직접 접근할 수 없다.

권장 적용 명령 (저장 후 WSL에서):

```bash
docker compose --env-file infra/sandbox/.env -f infra/sandbox/compose.yaml up -d --no-build --force-recreate kis-proxy
bash scripts/verify-runtime.sh
```

검증 스크립트는 키 내용을 읽지 않고 격리와 상태만 출력한다. 실연결 검증은 다음 smoke로 별도 실행한다.

## Hermes에서 사용

새 대화에서 `/workspace/trading-agent/docs/agent/trading-wiki.md`와
`/knowledge/trading/AGENTS.md`를 먼저 읽도록 지시한다. 문서 배치는 도구 설치와 다르며,
기존 대화가 새 지침을 자동 로드했다고 가정하지 않는다.

터미널 도구로 실행할 명령:

```bash
python -m trading_agent.cli status
python -m trading_agent.cli kis-readonly-smoke
python -m trading_agent.cli quote --symbol <사용자가_선택한_6자리_코드>
python -m trading_agent.cli candles --symbol <같은_코드>
python -m trading_agent.cli balance-check
python -m trading_agent.cli report
```

smoke는 인증·현재가·일봉·잔고 응답의 성공 여부만 출력하며 실패 시 종료 코드 1이다.
빈 키에서는 `configured=false`가 정상이다. health 성공은 KIS 연결 성공이 아니다.
조회 대상 어댑터는 국내 KRX부터 구현했으며 최종 투자 시장 확정이 아니다.
해외 종목, ETN 특수코드, 실시간 시세, 과거 대량 다운로드는 미지원이다.
잔고는 연결 검증만 반환한다. 페이지가 남으면 complete=false이며, 보유 내역이나 성과를
완전히 조회했다고 주장하지 않는다. 실제 API 지원은 키 입력 후 검증해야 한다.

## 원장과 문서

SQLite는 `tradingagent-ledger` named volume의 `/state/ledger.sqlite3`에 있다.
현재 원장은 조회 snapshot과 LLM의 미승인 판단 제안을 append-only로 기록한다.
금액은 정밀도 손실을 피하기 위해 십진 문자열, 시간은 KST offset 포함이다.
주문/체결/포지션 원장은 VTS 주문 단계에서 스키마와 대조 로직을 추가해야 한다.
DB는 암호화되지 않으며 Docker 관리자 접근과 디스크 분실에 대한 보호는 호스트에 의존한다.

`40_Daily/Generated/YYYY-MM-DD.md`는 DB에서 재생성한다. 같은 날짜를 재실행하면
생성 보고서만 교체하며, 수동 회고는 다른 파일에 둔다. Wiki 쓰기가 실패해도 원장은 남는다.
`report --date YYYY-MM-DD`로 복구한다. 자동 outbox worker와 예약 실행은 아직 연결하지 않았다.
백업은 실행 중인 sqlite 파일을 단순 복사하지 말고 호스트에서 SQLite backup API로 수행한다.
볼륨 삭제 명령은 사용하지 않는다.

## 경계와 미완료 사항

- VTS host와 세 API/TR만 고정한다. 주문 route, 임의 URL 전달, 실전 fallback 없음.
- 비밀값은 환경변수가 아닌 파일로 proxy에만 마운트하며 토큰은 proxy 메모리에만 저장한다.
- 오류는 고정 코드만 반환한다. upstream 본문, 헤더, 계좌식별자는 응답·원장·로그에 저장하지 않는다.
- proxy는 호스트 포트 공개 없이 동일 Docker 네트워크의 Hermes에서만 사용한다.
  그 네트워크에 붙일 수 있는 Docker 관리자는 신뢰 대상이다. HTTP 인증을 별도로 제공하지 않는다.
- 요청은 직렬화하고 최소 1.1초 간격, 15초 upstream timeout, 인증 재시도 최소 65초를 둔다.
  이는 자체 보수적 설정이며 공식 사용량 보장이 아니다. 자동 재시도는 없고 사용자가 오류 확인 후 재실행한다.
- 키가 LLM 컨텍스트로 전달되는 정상 경로를 제거했지만, 호스트/컨테이너 취약점까지 포함한
  절대적 유출 방지를 보장하지 않는다. Wiki의 리서치·전략은 Hermes 사용 시 선택한 LLM에 전달될 수 있다.
- 거래 전략 승인·위험 검사·성과 계산·중복 주문 방지·자동 Cron은 후속 단계다.

API 근거: [KIS 공식 조회 샘플](https://github.com/koreainvestment/open-trading-api/tree/main/examples_llm/domestic_stock),
[공식 인증 구현](https://github.com/koreainvestment/open-trading-api/blob/main/examples_llm/kis_auth.py).
