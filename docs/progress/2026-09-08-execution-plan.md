# 2026-09-08 — Execution plan revision

## Objective

Turn the initial roadmap into ordered implementation tasks with commands, acceptance criteria, and failure handling.

## Changes

- Added an execution plan covering WSL/Docker recovery, GUI browser integration, Hermes authentication, and Desktop verification.
- Separated brokerage read-only checks, user-selected experiment parameters, Shadow execution, and virtual orders.
- Moved order deduplication, reconciliation, proxy isolation, and the stop control before order activation.
- Distinguished existing commands from CLI contracts that require implementation.

## Verification

- Cross-checked the plan against existing Docker, bootstrap, and setup files.
- Reviewed WSL/Docker recovery commands and Hermes/KIS integration guidance against official documentation.
- This is a documentation change; runtime recovery, browser installation, and brokerage integration have not been executed.

## Limitations

The earlier environment inspection found a WSL VM creation failure. Its exact missing-file cause remains unconfirmed. No current container/browser verification is claimed.

## Next step

Execute E0/E1, preserving existing Ubuntu and Hermes state before recovery work.
