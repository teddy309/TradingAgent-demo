# TradingAgent Agent Rules

## Scope

- Work only on the `develop` branch unless the user explicitly requests another branch.
- Never merge or push directly to `main`.
- The public repository documents infrastructure, interfaces, tests, and sanitized operational processes.
- Private investment knowledge belongs in the mounted Obsidian folder at `/knowledge/trading`, not in this repository.

## Financial safety

- Paper trading only. Production brokerage endpoints and real-money order paths are forbidden.
- Fail closed when the runtime environment is not explicitly marked as virtual trading.
- An LLM may propose a decision but may not bypass deterministic risk checks.
- Do not invent market data, fills, balances, order states, or performance.

## Secrets and personal data

- Never read, print, log, commit, or summarize brokerage secrets, account identifiers, dashboard passwords, VNC passwords, tokens, or personal information.
- Never write secrets into Markdown, source files, fixtures, screenshots, chat output, Git history, or the Obsidian Vault.
- Local secrets belong only in ignored runtime secret stores such as `infra/sandbox/.env` or the Hermes data volume.
- Use synthetic identifiers and synthetic market/trade data in examples and tests.

## Change records

- Record architectural choices in `docs/adr/`.
- Record reusable operating procedures in `docs/runbooks/` or `docs/setup/`.
- Record sanitized milestones in `docs/progress/`.
- Each progress entry should state: objective, changes, verification, limitations, and next step.

## Verification

- Validate Docker Compose before starting the sandbox.
- Keep noVNC and Hermes Dashboard bound to host loopback only.
- Do not expose raw VNC port 5901 or the Hermes API port to the LAN or public internet.
- Never mount the Docker socket, the Windows home directory, or the full Obsidian Vault.
