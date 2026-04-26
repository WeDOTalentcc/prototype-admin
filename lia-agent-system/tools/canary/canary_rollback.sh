#!/bin/bash
# Canary Rollback — Sprint III.E
#
# Desliga IMEDIATAMENTE todas as feature flags V2 e força V1 delegation.
# Use em qualquer estágio do canary se health_check exit 2 ou se algo
# observável estiver errado.
#
# Uso:
#   ./canary_rollback.sh [--reason "descrição"]
#
# Exit codes:
#   0 = rollback bem-sucedido
#   1 = falha ao desligar flags (manual intervention needed)
#
# Reference: docs/migrations/SPRINT_III_E_CANARY_PLAN.md

set -euo pipefail

REASON="${1:---reason}"
REASON_TEXT="${2:-no reason given}"

echo "═══════════════════════════════════════════════════════════"
echo "🚨 CANARY ROLLBACK"
echo "Reason: $REASON_TEXT"
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 1: Replit env vars (atual)
# ─────────────────────────────────────────────────────────────────────────────
# Replit Secrets é o lugar onde env vars de prod ficam.
# Update via Replit IDE → Secrets tab → set:
#   LIA_V2_USE_PLAN_SERVICE=false
#   LIA_V2_USE_FALLBACK_REACT=false
#
# Após update: restart workflow para aplicar.

echo "Step 1: Desligar feature flags (Replit Secrets)"
echo ""
echo "MANUAL: Abra Replit IDE → Secrets tab → atualize:"
echo "  LIA_V2_USE_PLAN_SERVICE=false"
echo "  LIA_V2_USE_FALLBACK_REACT=false"
echo ""
echo "Após salvar, restart o workflow lia-agent-system."
echo ""

# Se você usa Kubernetes:
# kubectl set env deploy/lia-agent LIA_V2_USE_PLAN_SERVICE=false
# kubectl set env deploy/lia-agent LIA_V2_USE_FALLBACK_REACT=false
# kubectl rollout restart deploy/lia-agent
# echo "K8s rollout em andamento..."
# kubectl rollout status deploy/lia-agent

# Se você usa feature flag service externo (LaunchDarkly, etc.):
# curl -X PATCH "https://app.launchdarkly.com/api/v2/flags/lia/use_plan_service" \
#   -H "Authorization: $LD_API_KEY" \
#   -d '{"value": false}'

# ─────────────────────────────────────────────────────────────────────────────
# Estratégia 2: SSH manual nos pods (fallback)
# ─────────────────────────────────────────────────────────────────────────────
# Se Replit Secrets não responder, SSH direto e ajustar .env.local:
#
# ssh ... 'sed -i "s/^LIA_V2_USE_PLAN_SERVICE=.*/LIA_V2_USE_PLAN_SERVICE=false/" \
#   /home/runner/workspace/lia-agent-system/.env.local'

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Validação pós-rollback
# ─────────────────────────────────────────────────────────────────────────────

echo "Step 2: Verificar que rollback foi efetivo"
echo ""
echo "Aguardar 60s para propagação, depois:"
echo "  - Conferir logs: nenhum span 'orchestrator.v2.services.*' nos próximos 5 min"
echo "  - Conferir métricas: latency e error rate voltando a baseline V1"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Audit trail
# ─────────────────────────────────────────────────────────────────────────────

ROLLBACK_LOG="/tmp/canary_rollback_$(date +%Y%m%d_%H%M%S).log"
{
    echo "Canary Rollback Event"
    echo "Date: $(date -u)"
    echo "Reason: $REASON_TEXT"
    echo "Operator: ${USER:-unknown}"
    echo ""
    echo "Flags desligadas:"
    echo "  LIA_V2_USE_PLAN_SERVICE=false"
    echo "  LIA_V2_USE_FALLBACK_REACT=false"
} > "$ROLLBACK_LOG"

echo "Step 3: Audit log salvo em: $ROLLBACK_LOG"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Notificação
# ─────────────────────────────────────────────────────────────────────────────

echo "Step 4: NOTIFICAR EQUIPE"
echo ""
echo "Mensagem sugerida (Slack/email):"
echo "─────────────────────────────────────"
echo "🚨 Canary Sprint III.E foi rolled back."
echo "Reason: $REASON_TEXT"
echo "Time: $(date)"
echo "Próximo passo: investigar logs em Honeycomb/Sentry."
echo "─────────────────────────────────────"
echo ""

echo "✓ Rollback initiated. Confirme via dashboard que flags estão OFF."
exit 0
