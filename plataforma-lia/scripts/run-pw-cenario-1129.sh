#!/usr/bin/env bash
# Task #1149 (T-1129 sealing) — wrapper canônico para o spec
# `e2e/tests/multi-tenant/15-multi-tenant-ownership.spec.ts`.
#
# Espelha o padrão dos demais `run-pw-cenario-*.sh` (thin wrapper que
# delega ao `run-pw-cenario.sh` parametrizado de Task #1079).
#
# Credenciais multi-tenant precisam estar no ambiente (não podem usar
# `LIA_DEV_AUTO_LOGIN` porque o cenário alterna login A→B):
#   E2E_TENANT_A_EMAIL / E2E_TENANT_A_PASSWORD / E2E_TENANT_A_COMPANY_ID
#   E2E_TENANT_B_EMAIL / E2E_TENANT_B_PASSWORD / E2E_TENANT_B_COMPANY_ID
#
# Uso:
#   ./scripts/run-pw-cenario-1129.sh
#
set -euo pipefail

export LIA_DEV_AUTO_LOGIN="${LIA_DEV_AUTO_LOGIN:-false}"

exec "$(dirname "$0")/run-pw-cenario.sh" \
  "pw-cenario-1129" \
  "${PW_SPEC:-e2e/tests/multi-tenant/15-multi-tenant-ownership.spec.ts}" \
  "${PW_PROJECT:-desktop-chrome}"
