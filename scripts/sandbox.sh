#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/infra/sandbox/compose.yaml"
ENV_FILE="${ROOT_DIR}/infra/sandbox/.env"

die() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

need_command() {
    command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

default_wiki_path() {
    local windows_home
    local wsl_home

    if command -v powershell.exe >/dev/null 2>&1 && command -v wslpath >/dev/null 2>&1; then
        windows_home="$(powershell.exe -NoProfile -Command '[Environment]::GetFolderPath("UserProfile")' | tr -d '\r')"
        wsl_home="$(wslpath -u "${windows_home}")"
        printf '%s\n' "${wsl_home}/Documents/Obsidian/ossai_llmwiki/Projects/Hermes-Paper-Trading"
        return
    fi

    printf '%s\n' "${HOME}/Documents/Obsidian/ossai_llmwiki/Projects/Hermes-Paper-Trading"
}

bootstrap() {
    need_command openssl

    if [[ -f "${ENV_FILE}" ]]; then
        printf 'sandbox environment already exists: %s\n' "${ENV_FILE}"
        return
    fi

    local wiki_path
    local novnc_password
    local dashboard_password
    local dashboard_secret

    wiki_path="${LLM_WIKI_PATH:-$(default_wiki_path)}"
    novnc_password="$(openssl rand -hex 4)"
    dashboard_password="$(openssl rand -hex 16)"
    dashboard_secret="$(openssl rand -hex 32)"

    mkdir -p "${wiki_path}"
    umask 077
    {
        printf 'COMPOSE_PROJECT_NAME=tradingagent\n'
        printf 'HERMES_IMAGE_TAG=latest\n'
        printf 'LLM_WIKI_PATH=%s\n' "${wiki_path}"
        printf 'NOVNC_PASSWORD=%s\n' "${novnc_password}"
        printf 'HERMES_DASHBOARD_BASIC_AUTH_USERNAME=tradingagent\n'
        printf 'HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=%s\n' "${dashboard_password}"
        printf 'HERMES_DASHBOARD_BASIC_AUTH_SECRET=%s\n' "${dashboard_secret}"
        printf 'NOVNC_PORT=6080\n'
        printf 'HERMES_DASHBOARD_PORT=9119\n'
    } > "${ENV_FILE}"
    chmod 0600 "${ENV_FILE}"

    printf 'created private sandbox configuration: %s\n' "${ENV_FILE}"
    printf 'created/verified private knowledge folder: %s\n' "${wiki_path}"
    printf 'credentials were generated but were not printed\n'
}

compose() {
    [[ -f "${ENV_FILE}" ]] || die "run '$0 bootstrap' first"
    docker compose --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" "$@"
}

env_value() {
    local key="$1"
    sed -n "s/^${key}=//p" "${ENV_FILE}" | tail -n 1
}

validate() {
    need_command docker
    compose config --quiet

    local rendered
    rendered="$(compose config --format json | tr -d '[:space:]')"
    [[ "${rendered}" == *'"host_ip":"127.0.0.1"'* ]] \
        || die "compose validation failed: published ports must bind to 127.0.0.1"
    [[ "${rendered}" != *'"published":"5901"'* ]] \
        || die "compose validation failed: raw VNC port 5901 must not be published"
    [[ "${rendered}" != *'docker.sock'* ]] \
        || die "compose validation failed: Docker socket must not be mounted"

    printf 'compose and security contract validation passed\n'
}

status() {
    compose ps
    printf '\nHermes Dashboard status:\n'
    curl -fsS "http://127.0.0.1:$(env_value HERMES_DASHBOARD_PORT)/api/status" || true
    printf '\n\nnoVNC status:\n'
    curl -fsSI "http://127.0.0.1:$(env_value NOVNC_PORT)/vnc.html" | head -n 1 || true
}

usage() {
    cat <<EOF
Usage: $0 <command>

Commands:
  bootstrap   Generate ignored local credentials and the private wiki folder
  validate    Validate Compose and the local-only exposure contract
  build       Pull/build the Linux + Hermes + noVNC image
  up          Start Gateway, Cron, Dashboard, XFCE, and noVNC
  down        Stop and remove the sandbox container (preserves Hermes data)
  status      Show container and local HTTP status
  logs        Follow sandbox logs
  shell       Open a shell in the sandbox
  setup       Run the interactive Hermes setup wizard in the sandbox
  doctor      Run Hermes diagnostics
EOF
}

command_name="${1:-}"
case "${command_name}" in
    bootstrap)
        bootstrap
        ;;
    validate)
        bootstrap
        validate
        ;;
    build)
        bootstrap
        validate
        compose build --pull
        ;;
    up)
        bootstrap
        validate
        compose up -d
        ;;
    down)
        compose down
        ;;
    status)
        status
        ;;
    logs)
        compose logs --follow --tail=200
        ;;
    shell)
        compose exec --user hermes hermes-sandbox bash
        ;;
    setup)
        compose exec --user hermes hermes-sandbox hermes setup
        ;;
    doctor)
        compose exec --user hermes hermes-sandbox hermes doctor
        ;;
    *)
        usage
        [[ -n "${command_name}" ]] && exit 1
        ;;
esac
