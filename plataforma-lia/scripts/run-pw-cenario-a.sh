#!/usr/bin/env bash
# Task #1053 — wrapper canônico para a sentinela e2e do wizard.
#
# Uso:
#   ./plataforma-lia/scripts/run-pw-cenario-a.sh
#
# Pré-requisitos:
#   - lia-agent-system rodando em $LIA_BACKEND_URL (default 127.0.0.1:8001)
#     com o demo user seedado (demo@wedotalent.com / demo123).
#   - Frontend Next.js rodando em $PLAYWRIGHT_BASE_URL (default :5000).
#
# Por que existe um wrapper:
#   O workflow Replit `pw-cenario-A` roda esse comando inline. Centralizar
#   no script evita que ajustes de env (BACKEND_URL, base URL, project)
#   precisem editar `.replit` (que é gerenciado pela plataforma e não pode
#   ser modificado direto pelo agente). Também garante que CI/cron jobs
#   futuros (ver follow-up #1054) e devs locais executem a mesma matriz
#   de envs do harness.
#
# O fixture (e2e/fixtures/auth.fixture.ts, post Task #1053) já não depende
# de LIA_DEV_AUTO_LOGIN no FE — ele chama o backend direto. As envs abaixo
# são exportadas como rede de segurança para qualquer outra ferramenta de
# auth/bootstrap que ainda consuma a flag.
set -euo pipefail

cd "$(dirname "$0")/.."

export APP_ENV="${APP_ENV:-development}"
export NODE_ENV="${NODE_ENV:-development}"
export LIA_DEV_AUTO_LOGIN="${LIA_DEV_AUTO_LOGIN:-true}"
export PLAYWRIGHT_BASE_URL="${PLAYWRIGHT_BASE_URL:-http://localhost:5000}"
export LIA_BACKEND_URL="${LIA_BACKEND_URL:-${BACKEND_URL:-http://127.0.0.1:8001}}"

PROJECT="${PW_PROJECT:-desktop-chrome}"
SPEC="${PW_SPEC:-e2e/tests/wizard/02-vaga-tecnica.spec.ts}"

echo "[pw-cenario-A] APP_ENV=$APP_ENV"
echo "[pw-cenario-A] PLAYWRIGHT_BASE_URL=$PLAYWRIGHT_BASE_URL"
echo "[pw-cenario-A] LIA_BACKEND_URL=$LIA_BACKEND_URL"
echo "[pw-cenario-A] project=$PROJECT spec=$SPEC"

# Task #1054 — warmup do Next/Turbopack.
# Cold-compile de /pt no Replit leva 40-70s na primeira request, e o
# `page.goto('/pt')` do helper estourava 30s antes do fix. Pré-aquecemos
# /pt e /pt/chat com curl (timeouts generosos: connect 10s + max 120s)
# para que o teste já encontre a rota compilada. Se o frontend não estiver
# de pé, o curl falha silencioso (|| true) — o test próprio reportará
# baseURL inacessível com erro mais claro.
echo "[pw-cenario-A] warming up Next.js routes..."
for path in "/pt" "/pt/chat"; do
  echo "[pw-cenario-A]   GET $PLAYWRIGHT_BASE_URL$path"
  curl -fsS --connect-timeout 10 --max-time 120 \
    -o /dev/null -w "    -> HTTP %{http_code} in %{time_total}s\n" \
    "$PLAYWRIGHT_BASE_URL$path" || \
    echo "    -> warmup falhou (frontend pode estar offline; teste vai falhar com mensagem clara)"
done

exec pnpm playwright test "$SPEC" --project="$PROJECT" --reporter=list
