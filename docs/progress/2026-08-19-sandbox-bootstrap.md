# 2026-08-19 — Linux sandbox bootstrap

## Objective

Create a reproducible local Linux environment for Hermes Agent before configuring the brokerage API or selecting paper-trading defaults.

## Changes

- Added a Docker image derived from the official Hermes Agent image.
- Added XFCE, TigerVNC, and noVNC to the same isolated environment.
- Added host-loopback-only Dashboard and noVNC ports.
- Added a private Hermes state volume and narrowly scoped project/knowledge mounts.
- Added local secret generation, validation, lifecycle commands, and documentation.
- Added public-sharing and privacy rules that exclude account, strategy, and trading data.

## Verification

- Compose syntax and port/mount security contracts are validated by `scripts/sandbox.sh validate`.
- The custom Hermes/noVNC image builds successfully on Docker Desktop with the WSL2 engine.
- The container reports `healthy` with only `127.0.0.1:6080` and `127.0.0.1:9119` published.
- noVNC serves its web client successfully, its WebSocket reaches the VNC server (`RFB 003.008`), and TigerVNC, XFCE, and websockify are running inside the container.
- Hermes Dashboard reports overall status `ok`, Basic Auth enabled, and Gateway state `running`.

## Limitations

- No model provider is configured.
- No brokerage API credentials or endpoints are configured.
- No investment universe, capital, frequency, or private strategy is defined.

## Next step

Complete the interactive Hermes provider setup, connect Hermes Desktop in remote-gateway mode, and verify a non-brokerage test prompt before adding the Korea Investment API.
