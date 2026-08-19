# Linux sandbox setup

## Purpose

This setup runs Hermes Agent, its Gateway, Cron scheduler, dashboard, terminal, and a visual Linux desktop inside one Docker container backed by WSL2. Windows Hermes Desktop acts as a remote client. noVNC is an operational inspection surface, not the agent transport.

## Prerequisites

- Windows 10/11 with WSL2
- Ubuntu WSL distribution
- Docker Desktop using the WSL2 engine
- Docker Desktop integration enabled for the Ubuntu distribution
- Git and OpenSSL inside Ubuntu

Verify from Ubuntu:

```bash
docker version
docker compose version
openssl version
```

## Start

```bash
git clone --branch develop https://github.com/teddy309/TradingAgent-demo.git
cd TradingAgent-demo

./scripts/sandbox.sh bootstrap
./scripts/sandbox.sh validate
./scripts/sandbox.sh build
./scripts/sandbox.sh up
./scripts/sandbox.sh status
```

The bootstrap step:

- creates `infra/sandbox/.env` with random local passwords;
- sets its permission to mode 0600;
- creates a dedicated `Projects/Hermes-Paper-Trading` folder under the Windows Obsidian Vault;
- does not print passwords.

## Open the visual desktop

Open:

```text
http://127.0.0.1:6080/vnc.html?autoconnect=1&resize=scale
```

Use `NOVNC_PASSWORD` from the ignored `infra/sandbox/.env` file.
The raw VNC port is internal to the container and is not published.

## Configure Hermes

Run the setup wizard:

```bash
./scripts/sandbox.sh setup
```

Alternatively, open **Sandbox Terminal** on the noVNC desktop and run:

```bash
hermes setup
```

The setup writes provider credentials and Hermes configuration to the private Docker volume `tradingagent-hermes-data`.

## Connect Windows Hermes Desktop

1. Open **Settings → Gateways → Remote gateway**.
2. Set Remote URL to `http://127.0.0.1:9119`.
3. Sign in with:
   - username from `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`;
   - password from `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`.
4. Save and reconnect.

The container dashboard binds to `0.0.0.0` internally so its authentication gate is enabled, while Docker publishes it only to Windows loopback.

## File boundaries

| Container path | Host source | Access |
|---|---|---|
| `/workspace/trading-agent` | This repository | Read/write |
| `/knowledge/trading` | Dedicated private Obsidian subfolder | Read/write |
| `/opt/data` | Private Docker named volume | Read/write |
| Other host paths | Not mounted | No access |

The Docker socket, Windows home, full Obsidian Vault, raw VNC port, and Hermes API port are not exposed.

## Operations

```bash
./scripts/sandbox.sh status
./scripts/sandbox.sh logs
./scripts/sandbox.sh shell
./scripts/sandbox.sh doctor
./scripts/sandbox.sh down
```

`down` preserves the Hermes data volume. Do not use `docker compose down -v` unless permanent deletion of Hermes configuration, sessions, skills, memory, and Cron state is intended.

## Updating

Review upstream Hermes release notes, then:

```bash
git switch develop
git pull --ff-only
./scripts/sandbox.sh build
./scripts/sandbox.sh up
```

The custom image inherits from the official Hermes Docker image. Updating recreates the image while the named state volume remains.

## Troubleshooting

### Docker client works but the server is unavailable

Start Docker Desktop and wait for the Linux engine to report ready:

```bash
docker version
```

Both Client and Server sections must be present.

### noVNC opens but shows no desktop

```bash
./scripts/sandbox.sh logs
docker top tradingagent-hermes-sandbox -eo pid,comm,args
```

Confirm that `Xtigervnc`, `xfce4-session`, and `websockify` are present.

### Hermes Desktop reports that the gateway is incomplete

Verify:

```bash
curl -s http://127.0.0.1:9119/api/status
```

The response must advertise `auth_required: true` and include the `basic` provider.
