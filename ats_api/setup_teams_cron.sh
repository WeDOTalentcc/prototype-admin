#!/bin/bash

# ============================================================================
# ⚠️  DEPRECADO - Adicione diretamente ao crontab
# ============================================================================
# Este script foi deprecado. Adicione manualmente ao crontab:
#
#   crontab -e
#
# Cole esta linha (ajuste o caminho):
#   */30 8-18 * * 1-5 cd /SEU/PROJETO && \
#     docker compose exec -T web bundle exec rails teams:auto_reset >> log/teams_cron.log 2>&1
#
# Ver exemplos completos:
#   make teams-show-cron
#
# Docs: TEAMS_DEV_SETUP.md
# ============================================================================

set -e

PROJECT_DIR="/home/victhor/ats_mercado/ats_api"
CRON_COMMAND="*/30 8-18 * * 1-5 cd $PROJECT_DIR && ./teams_reset_dev.sh >> /tmp/teams_reset.log 2>&1"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Setup Automático - Teams Reset Crontab"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar se já existe no crontab
if crontab -l 2>/dev/null | grep -q "teams_reset_dev.sh"; then
  echo "⚠️  Job já existe no crontab!"
  echo ""
  echo "Configuração atual:"
  crontab -l | grep "teams_reset_dev.sh"
  echo ""
  echo "Para remover, execute: crontab -e e delete a linha"
  exit 0
fi

echo "📍 Projeto detectado em: $PROJECT_DIR"
echo "⏰ Frequência: A cada 30 minutos (Seg-Sex, 8h-18h)"
echo "📝 Logs em: /tmp/teams_reset.log"
echo ""

read -p "Continuar e adicionar ao crontab? (s/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[SsSyY]$ ]]; then
  echo "❌ Cancelado"
  exit 1
fi

# Adicionar ao crontab
(crontab -l 2>/dev/null; echo ""; echo "# Microsoft Teams Auto Reset (Development)"; echo "$CRON_COMMAND") | crontab -

echo ""
echo "✅ Crontab configurado com sucesso!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Comandos Úteis:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Ver configuração atual:"
echo "  crontab -l"
echo ""
echo "Ver logs em tempo real:"
echo "  tail -f /tmp/teams_reset.log"
echo ""
echo "Testar manualmente:"
echo "  cd $PROJECT_DIR && ./teams_reset_dev.sh"
echo ""
echo "Remover do crontab:"
echo "  crontab -e  # Delete a linha do teams_reset_dev.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Setup completo! O reset rodará automaticamente."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
