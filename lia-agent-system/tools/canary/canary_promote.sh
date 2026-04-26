#!/bin/bash
# Canary Promote — Sprint III.E
#
# Avança canary para próximo estágio: 5pct → 25pct → 50pct → 100pct.
# Roda health_check ANTES de promover. Se health falhar, aborta.
#
# Uso:
#   ./canary_promote.sh [next_stage]
#   stages: 25pct | 50pct | 100pct
#
# Reference: docs/migrations/SPRINT_III_E_CANARY_PLAN.md

set -euo pipefail

NEXT_STAGE="${1:-}"

if [ -z "$NEXT_STAGE" ]; then
    echo "Uso: ./canary_promote.sh [25pct|50pct|100pct]"
    exit 1
fi

echo "═══════════════════════════════════════════════════════════"
echo "CANARY PROMOTE → $NEXT_STAGE"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Step 1: Health check do estágio atual
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Step 1: Health check pré-promotion..."
if ! "$SCRIPT_DIR/canary_health_check.sh"; then
    echo ""
    echo "🔴 Health check falhou — promotion ABORTADA"
    echo "Resolva issues e tente novamente."
    exit 1
fi

echo ""
echo "✓ Health check OK"
echo ""

# Step 2: Definir percentual
case "$NEXT_STAGE" in
    "25pct") PCT=25 ;;
    "50pct") PCT=50 ;;
    "100pct") PCT=100 ;;
    *) echo "Stage inválido: $NEXT_STAGE"; exit 1 ;;
esac

# Step 3: Confirmar
echo "Step 2: Promover para $PCT% do tráfego"
echo ""
echo "MANUAL: Abra Replit IDE → Secrets tab"
echo ""
echo "Para ativar PlanService em $PCT% das requests:"
echo "  Use feature flag service (LaunchDarkly, Unleash) com gradual rollout"
echo "  OU restart percentage de pods com flag ON:"
echo ""
echo "  Pseudo-config Replit deployments:"
echo "    instance_count=10"
echo "    instances_with_v2: $((PCT / 10))"
echo ""
read -p "Confirma promotion para $PCT%? [y/N] " confirm
if [ "$confirm" != "y" ]; then
    echo "Cancelado."
    exit 1
fi

# Step 4: Audit log
PROMOTE_LOG="/tmp/canary_promote_$(date +%Y%m%d_%H%M%S).log"
{
    echo "Canary Promote Event"
    echo "Date: $(date -u)"
    echo "From stage: previous"
    echo "To stage: $NEXT_STAGE ($PCT%)"
    echo "Operator: ${USER:-unknown}"
} > "$PROMOTE_LOG"

echo ""
echo "✓ Promotion to $NEXT_STAGE initiated"
echo "Audit log: $PROMOTE_LOG"
echo ""
echo "Aguardar 24h em $PCT% antes do próximo promote."
echo "Health check deve rodar a cada 1h durante esse período."
exit 0
