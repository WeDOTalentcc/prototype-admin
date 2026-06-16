#!/bin/bash

# ============================================================================
# ⚠️  DEPRECADO - Use Rake Tasks ao invés deste script
# ============================================================================
# Este script foi deprecado em favor de Rake tasks (padrão Rails).
#
# Use ao invés:
#   make teams-reset
#   docker compose exec web bundle exec rails teams:reset_fast
#
# Para automação (cron), use:
#   docker compose exec -T web bundle exec rails teams:auto_reset
#
# Docs: TEAMS_DEV_SETUP.md
# ============================================================================

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 TEAMS SUBSCRIPTION RESET - Development Mode"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ! docker compose ps web | grep -q "Up"; then
  echo "❌ Container 'web' não está rodando"
  echo "   Execute: docker compose up -d"
  exit 1
fi

CURRENT_URL=$(grep "^APP_HOST=" .env 2>/dev/null | cut -d '=' -f2 | tr -d '"' || echo "NOT_SET")

echo "📍 Current APP_HOST (webhook URL):"
echo "   ${CURRENT_URL}/v1/webhooks/teams_chat"
echo ""

if [[ "$CURRENT_URL" == "NOT_SET" ]] || [[ "$CURRENT_URL" == "http://localhost:3000" ]]; then
  echo "⚠️  WARNING: APP_HOST parece ser localhost"
  echo "   Certifique-se que está usando ngrok ou túnel acessível externamente"
  echo ""
fi

echo "🔧 Executando reset rápido (sem deletar da Microsoft)..."
echo ""

docker compose exec -T web bundle exec rails teams:reset_fast

RESET_STATUS=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $RESET_STATUS -eq 0 ]; then
  echo "✅ Reset concluído com sucesso!"
  echo ""
  echo "📋 Próximos passos:"
  echo "   1. Envie uma mensagem para LIA no Teams"
  echo "   2. Verifique logs: docker logs -f ats_api"
  echo "   3. Se não funcionar, rode diagnóstico: make teams-diagnose"
else
  echo "❌ Reset falhou - veja erros acima"
  echo ""
  echo "🔍 Para mais detalhes:"
  echo "   make teams-diagnose    # Rodar diagnóstico completo"
  echo "   make teams-status      # Ver status das subscriptions"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
