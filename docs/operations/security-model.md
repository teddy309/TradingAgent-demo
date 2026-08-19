# Sandbox security model

## Protected assets

- Brokerage and model-provider credentials
- Hermes sessions, memory, skills, Cron definitions, and configuration
- Private investment strategy and review notes
- Host files outside the project and dedicated knowledge folder

## Trust boundaries

### Windows host

Stores the Git working tree and Obsidian Vault. Hermes Desktop is a remote client and does not execute agent tools locally when connected to the sandbox Dashboard.

### WSL2 and Docker engine

Provide the Linux container boundary. Docker Desktop is trusted infrastructure and must remain patched.

### Hermes sandbox container

Runs Hermes, Gateway, Cron, XFCE, TigerVNC, and noVNC. It has outbound network access for model and future brokerage API calls, but receives only three writable mounts.

## Controls

- Host-loopback-only publication for ports 6080 and 9119
- Password-gated Hermes Dashboard
- Password-gated VNC with raw port 5901 unexposed
- Read-only container root filesystem
- Ephemeral, size-limited `/run`, `/tmp`, and `/var/tmp`; `noexec` remains on
  `/tmp` and `/var/tmp`, while `/run` permits execution required by s6-overlay
- CPU, memory, PID, and shared-memory limits
- No Docker socket mount
- No new privileges and reduced Linux capabilities
- Multiple Hermes safe-write roots limited to state, project, and private trading notes
- Git ignore rules, PR privacy checklist, and a repository privacy scan
- Secret redaction enabled in Hermes

## Residual risks

- Any process with access to a read/write bind mount can change files in that mount.
- An agent terminal can do more than Hermes file-tool guards allow; the Docker boundary is the primary control.
- The Hermes state volume contains sensitive model configuration and must not be exported publicly.
- Password authentication is appropriate only because ports are host-loopback-only. Public exposure requires OAuth/OIDC and TLS.
- Future brokerage keys should ideally be held by a narrow broker-proxy service rather than exposed to a general agent terminal.

## Future hardening before brokerage credentials

1. Add a KIS proxy service exposing only allowlisted market-data and virtual-order operations.
2. Store KIS secrets only in the proxy, not in the Hermes container.
3. Enforce a virtual-trading-only environment flag and reject production hosts.
4. Add request quotas, order idempotency, audit logs, and a kill switch.
5. Add outbound-domain controls for the KIS proxy.
