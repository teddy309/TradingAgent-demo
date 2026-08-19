# Public sharing guide

## Recommended structure

Share the engineering process through four complementary records:

1. **README** — current purpose, architecture, and entry points.
2. **ADR** — why an important technical or security decision was made.
3. **Runbook/setup guide** — repeatable commands and verification steps.
4. **Progress log** — a dated, sanitized record of what changed and what remains.

GitHub Issues should track planned work and defects. Pull requests should connect the implementation, ADR/runbook update, and verification evidence.

## Safe to publish

- Dockerfiles, Compose configuration, schemas, interfaces, and tests
- Synthetic market data and synthetic orders
- API endpoint names and limits already present in official public documentation
- Generic risk-control architecture
- Sanitized screenshots without credentials, account details, positions, or P&L
- Performance and reliability measurements of the software itself
- Lessons about reproducibility, observability, testing, and failure handling

## Keep private

- Account number, HTS ID, customer ID, personal name, email, or phone number
- App Key, App Secret, access/refresh token, OAuth state, passwords, or signing secrets
- Actual holdings, orders, fills, balances, P&L, tax data, or timestamps that identify activity
- Exact private investment rules, thresholds, target universe, prompts, and post-trade analysis
- Obsidian notes, Hermes memory/session data, and raw model transcripts
- Screenshots that reveal any of the above

## Progress log template

```markdown
# YYYY-MM-DD — Short milestone

## Objective

What engineering capability was being added?

## Changes

- Public, implementation-level changes only.

## Verification

- Commands run and pass/fail outcomes.
- Synthetic or redacted evidence only.

## Limitations

- Known technical limitations without private trading details.

## Next step

- The next public engineering milestone.
```

## Strategy separation

Keep the private strategy in the mounted Obsidian folder. The public repository may define a strategy interface and use a synthetic example such as `SyntheticStrategyV1`, but must not include real parameters or the private decision prompt.

## Before every push

```bash
./scripts/validate-public-repo.sh
git status --short
git diff --cached
```

Review every new image and binary attachment separately. Git ignore rules do not protect content pasted into Markdown, issue descriptions, PR comments, CI logs, or screenshots.
