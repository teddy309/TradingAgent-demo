# 2026-09-09 — Private KIS query and Wiki foundation

## Objective

Prepare user-entered VTS secrets, SQLite source records and an Obsidian research workflow.

## Changes

- Added a separate immutable, non-root KIS service with no published host port.
- Moved KIS inputs outside the repository and Agent mounts; only the KIS service receives the file.
- Made the Agent code mount read-only and masked the existing sandbox secret file there.
- Added VTS allowlisted current-price, daily-candle and balance-connectivity operations.
- Added an append-only SQLite event ledger and idempotent unapproved proposal registration.
- Added replayable daily reports, Wiki seeds and an Agent operating guide.
- Added structural Compose validation. Python uses only the standard library; no third-party dependency lockfile is needed at this stage.

## Verification

Synthetic tests cover duplicate/conflicting requests, append-only records, missing snapshots,
blocked orders/redirects, authentication cooldown, token reuse, response filtering and report replay.
- Ten synthetic tests passed, including upstream timeout/429 and expired-token renewal.
- Live checks passed: Agent cannot access KIS secret, DB or Docker socket, has no KIS environment variables,
  has read-only source and a masked sandbox `.env`; proxy runs as UID 10001 with a read-only secret mount,
  no Vault/repository/socket and a valid SQLite database.
- Hermes can reach proxy; readiness is `configured=false`, `orders_enabled=false` before private input.
- A zero-event daily report was generated into the private Wiki and found on the Windows host.
- HTTP checks for 6080 and 9119 returned 200; proxy has no published ports.
- Windows ACL initially blocked Docker; host-owner permissions plus SYSTEM read access fixed the mount.
  Host-owner editing access was verified without reading file contents.
- Removed the setup tool account's separate folder grant after setup; runtime checks still passed.
- Final Hermes and proxy containers are healthy. KIS base image is pinned to the built Python digest.

## Limitations

No real credentials have been supplied or inspected. Live KIS authentication/API support remains unverified.
Balance returns connectivity and pagination status only; it is not a portfolio valuation feed.
No strategy is approved and no order routes exist. Trade/fill reconciliation, risk gates,
performance evaluation, automatic outbox delivery and scheduled execution remain later milestones.
The initial adapter supports Korean KRX stock queries only, without selecting the investment universe.

## Next step

User privately enters VTS inputs, restarts only the KIS service, selects a test symbol and runs
`kis-readonly-smoke`. Record sanitized API support/limits before choosing investment policy.
