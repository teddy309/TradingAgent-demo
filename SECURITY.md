# Security Policy

## Supported scope

This repository is for paper-trading research. It does not authorize or support production brokerage orders.

## Never commit

- Brokerage App Key, App Secret, access token, account number, HTS ID, or customer information
- Hermes provider credentials, OAuth state, dashboard login, or VNC password
- Actual holdings, order/fill history, P&L, tax data, or private investment strategy
- Obsidian Vault content or screenshots containing any of the above

## Local secret locations

- `infra/sandbox/.env` — generated local sandbox credentials; ignored by Git
- Docker named volume `hermes-data` — Hermes configuration, sessions, skills, memory, and cron state
- Future brokerage credentials — Hermes state or a dedicated broker proxy secret store; never a repository file

## Network exposure

- noVNC and Hermes Dashboard must remain bound to `127.0.0.1`.
- Raw VNC port 5901 and Hermes API port 8642 must not be published.
- Do not expose the password-based Dashboard directly to the internet.

## Incident response

If a secret is committed:

1. Revoke and rotate it immediately.
2. Remove it from the working tree and Git history.
3. Review CI logs, screenshots, issue attachments, and forks for copies.
4. Document only the sanitized cause and remediation.
