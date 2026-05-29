#!/usr/bin/env bash
# Task #1079 — wrapper canônico parametrizado para cenários E2E do wizard.
#
# Substitui run-pw-cenario-{a,b,c}.sh duplicados. Esses agora são thin
# wrappers que chamam este script com label + spec.
#
# Uso:
#   ./run-pw-cenario.sh <label> <spec-relativo> [project]
#
# Pré-requisitos:
#   - dev-server rodando em $PLAYWRIGHT_BASE_URL (default :5000)
#   - lia-backend rodando em $LIA_BACKEND_URL (default 127.0.0.1:8001)
#
# Dois mecanismos defensivos contra os bugs de infra que motivaram #1079:
#   1. PW_REUSE_SERVER=1 (default) — playwright.config.ts agora trata
#      reuseExistingServer como opt-out explícito; nenhum cenário tenta
#      spawnar um webServer novo na 5000 e colidir com o dev-server.
#   2. Wait loop HTTP — antes de invocar `pnpm playwright test`, espera
#      o frontend responder em /api/health (ou /). Se não subir em 120s,
#      falha rápido com mensagem clara — não atribui o timeout do teste
#      a um bug de aplicação.
set -euo pipefail

cd "$(dirname "$0")/.."

LABEL="${1:?label required (ex: pw-cenario-A)}"
SPEC="${2:?spec path required (ex: e2e/tests/wizard/02-vaga-tecnica.spec.ts)}"
PROJECT="${3:-${PW_PROJECT:-desktop-chrome}}"

export APP_ENV="${APP_ENV:-development}"
export NODE_ENV="${NODE_ENV:-development}"
export LIA_DEV_AUTO_LOGIN="${LIA_DEV_AUTO_LOGIN:-true}"
export PLAYWRIGHT_BASE_URL="${PLAYWRIGHT_BASE_URL:-http://localhost:5000}"
export LIA_BACKEND_URL="${LIA_BACKEND_URL:-${BACKEND_URL:-http://127.0.0.1:8001}}"
export PW_REUSE_SERVER="${PW_REUSE_SERVER:-1}"

echo "[$LABEL] APP_ENV=$APP_ENV PW_REUSE_SERVER=$PW_REUSE_SERVER"
echo "[$LABEL] PLAYWRIGHT_BASE_URL=$PLAYWRIGHT_BASE_URL"
echo "[$LABEL] LIA_BACKEND_URL=$LIA_BACKEND_URL"
echo "[$LABEL] project=$PROJECT spec=$SPEC"

# --- wait loop: frontend healthcheck ---------------------------------------
# Polla a baseURL até 120s. Cobre o caso "dev-server ainda subindo quando
# o workflow de cenário arranca" — comum quando ambos restartam juntos.
echo "[$LABEL] aguardando frontend ficar saudável em $PLAYWRIGHT_BASE_URL ..."
FE_OK=0
for i in $(seq 1 60); do
  if curl -fsS --connect-timeout 2 --max-time 5 -o /dev/null "$PLAYWRIGHT_BASE_URL/" 2>/dev/null; then
    echo "[$LABEL]   frontend respondeu após ${i} tentativa(s) (~$((i*2))s)"
    FE_OK=1
    break
  fi
  sleep 2
done
if [ "$FE_OK" != "1" ]; then
  echo "[$LABEL] ERRO: frontend não ficou saudável em 120s — abortando antes do teste"
  exit 1
fi

# --- warmup do Next/Turbopack (Task #1054, #1173) --------------------------
# Cold-compile de /pt no Replit pode levar 30-70s na primeira request.
#
# Etapa 1 (curl): compila a ROTA do servidor. Rápido, mas NÃO compila os
# chunks JS client-side que o Chromium headless pede em seguida.
echo "[$LABEL] warming up rotas Next.js (curl) ..."
for path in "/pt" "/pt/chat"; do
  curl -fsS --connect-timeout 10 --max-time 120 \
    -o /dev/null -w "[$LABEL]   GET $path -> HTTP %{http_code} em %{time_total}s\n" \
    "$PLAYWRIGHT_BASE_URL$path" \
    || echo "[$LABEL]   warmup $path falhou (continuando — teste reportará)"
done

# Etapa 2 (browser): Task #1173 — dirige um Chromium headless real pelas
# rotas-alvo para forçar a compilação dos chunks lazy (dynamic imports do
# chat, locale routing). Sem isto, a PRIMEIRA navegação do teste pega o
# `next dev --turbopack` ainda compilando esses chunks → 502 / "Failed to
# fetch" → goto estoura 90s mesmo com o curl tendo passado em <1s. Best-effort.
echo "[$LABEL] warming up bundles via headless Chromium (Task #1173) ..."
PLAYWRIGHT_BASE_URL="$PLAYWRIGHT_BASE_URL" node scripts/pw-warmup.mjs "$PLAYWRIGHT_BASE_URL" \
  || echo "[$LABEL]   warmup browser falhou (continuando — teste tem retry próprio)"

exec pnpm playwright test "$SPEC" --project="$PROJECT" --reporter=list
