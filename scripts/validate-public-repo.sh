#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

fail=0

private_paths="$(
    git ls-files \
        | grep -E '(^|/)\.env($|\.)|account|credential|llm-wiki|vault' \
        | grep -Ev '(^|/)\.env\.example$' \
        || true
)"

if [[ -n "${private_paths}" ]]; then
    printf 'error: a secret/private path appears to be tracked by Git\n' >&2
    printf '%s\n' "${private_paths}" >&2
    fail=1
fi

if git grep -nEI \
    '(app[_ -]?secret|access[_ -]?token|account[_ -]?(no|number)|cano)[[:space:]]*[:=][[:space:]]*[^<${][^ ]+' \
    -- ':!scripts/validate-public-repo.sh' ':!*.example' >/tmp/tradingagent-secret-scan.txt; then
    printf 'error: possible secret or account identifier found in tracked content\n' >&2
    cat /tmp/tradingagent-secret-scan.txt >&2
    fail=1
fi

rm -f /tmp/tradingagent-secret-scan.txt

if [[ "${fail}" -ne 0 ]]; then
    exit 1
fi

printf 'public repository privacy checks passed\n'
