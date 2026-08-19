# ADR 0001: WSL2-hosted Docker sandbox with noVNC

- Status: Accepted
- Date: 2026-08-19

## Context

Hermes should be operated from Windows Hermes Desktop while all agent execution, Gateway, Cron, state, and future brokerage integration remain inside a Linux isolation boundary. The environment also needs a visual inspection surface.

## Decision

Run a custom image derived from the official Hermes Agent image under Docker Desktop's WSL2 Linux engine. Add XFCE, TigerVNC, and noVNC to the same container. Connect Windows Hermes Desktop to the authenticated Hermes Dashboard on host loopback.

The project repository, a dedicated Obsidian subfolder, and a private Hermes state volume are the only writable mounts.

## Consequences

### Positive

- Agent tools execute on the remote container, not the Windows Desktop host.
- Gateway, Cron, terminal, and visual desktop share one observable Linux environment.
- noVNC and Dashboard are reachable locally without publishing raw VNC or API ports.
- The environment is reproducible from the public repository.

### Negative

- The image is larger because it contains a desktop stack.
- The container requires outbound network access.
- A compromise can modify the project and dedicated knowledge folder because both are intentionally writable.
- Updating Hermes requires rebuilding the image rather than using `hermes update` in place.

## Rejected alternatives

- Native Windows Hermes backend: does not provide the requested Linux isolation.
- WSL process without Docker: weaker per-project isolation and cleanup.
- Separate noVNC companion with Docker socket access: would expose excessive control over the host Docker engine.
- Publicly exposed Dashboard/noVNC: unnecessary and unsafe for a local project.
