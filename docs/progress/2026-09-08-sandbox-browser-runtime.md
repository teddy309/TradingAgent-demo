# 2026-09-08 — Sandbox and browser runtime

## Objective

Execute the environment portion of the paper-trading plan and verify that the Linux GUI, Hermes services, and local access paths are usable.

## Changes

- Added Chromium, `xdg-utils`, C.UTF-8 locale settings, Noto CJK and emoji fonts to the sandbox image.
- Added a Sandbox Browser desktop shortcut and explicit HTTP/HTTPS Chromium associations.
- Made sandbox shell, setup, and diagnostics commands run as the `hermes` user.
- Rebuilt and recreated the container while preserving the named Hermes data volume for this Docker context.

## Verification

- Ubuntu WSL and the Docker Desktop Linux engine are running.
- Container health is `healthy`; only loopback ports 6080 and 9119 are published.
- Chromium is installed, the X display is reachable, and `xdg-settings` reports `chromium.desktop`.
- noVNC returns HTTP 200 and its WebSocket reaches TigerVNC with the RFB 3.8 handshake.
- Hermes Dashboard returns HTTP 200 with overall status `ok`, Gateway `running`, and Basic Auth enabled.

## Limitations

- Hermes model-provider authentication is not configured yet; provider warnings at startup are expected.
- KIS credentials, read-only API checks, investment parameters, and trading code are not configured.
- Visual inspection through the Windows browser automation helper could not complete because the helper stopped when it could not determine the current browser URL. HTTP, WebSocket, X display, and Chromium process checks passed.

## Next step

From the noVNC Sandbox Terminal shell, run `hermes model`, complete the provider login, and verify a short test response before implementing the KIS read-only proxy.
