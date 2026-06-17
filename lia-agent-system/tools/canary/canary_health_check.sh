#!/bin/bash
# Canary Health Check — Sprint III.E
#
# Lê métricas reais de OTLP/Sentry e compara contra MIGRATION_REGRESSION_BASELINE.md.
# Retorna exit code 0 se OK, 1 se rollback recomendado.
#
# Uso:
#   ./canary_health_check.sh [stage]
#   stages: 5pct | 25pct | 50pct | 100pct
#
# Exit codes:
#   0 = healthy, prosseguir para próximo estágio
#   1 = manual review needed (warning)
#   2 = AUTO-ROLLBACK recomendado (limites violados)
#
# Reference: docs/migrations/SPRINT_III_E_CANARY_PLAN.md

set -euo pipefail

STAGE="${1:-5pct}"

# ─────────────────────────────────────────────────────────────────────────────
# THRESHOLDS (de MIGRATION_REGRESSION_BASELINE.md Section 2)
# Conservative defaults — substituir por dados reais quando disponíveis.
# ─────────────────────────────────────────────────────────────────────────────

# Latência max absoluta (ms)
declare -A LATENCY_P95_MAX=(
    ["chat_rest"]=5000
    ["chat_ws"]=5000
    ["chat_sse"]=5000
    ["orchestrated_job_chat"]=6000
    ["orchestrated_talent_chat"]=6000
    ["orchestrated_jobs_mgmt"]=6000
    ["wizard_job_graph"]=8000
    ["legacy_orchestrator"]=6000
)

# Error rate max absoluto (%)
declare -A ERROR_RATE_MAX=(
    ["chat_rest"]=2.0
    ["chat_ws"]=2.0
    ["chat_sse"]=2.0
    ["orchestrated_job_chat"]=1.5
    ["orchestrated_talent_chat"]=1.5
    ["orchestrated_jobs_mgmt"]=1.5
    ["wizard_job_graph"]=3.0
)

# Janela de tempo (minutos) para média
WINDOW_MINUTES=10

echo "═══════════════════════════════════════════════════════════"
echo "CANARY HEALTH CHECK — Stage: $STAGE"
echo "Window: last $WINDOW_MINUTES minutes"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Fetch metrics
# ─────────────────────────────────────────────────────────────────────────────
# IMPLEMENTAÇÃO: substituir abaixo pelo provider real (Sentry, Datadog, etc.)
#
# Exemplo Sentry CLI:
#   sentry-cli query --window=10m --metric=p95_latency --filter='endpoint=...'
#
# Exemplo Datadog API:
#   curl -X GET "https://api.datadoghq.com/api/v1/query?query=avg:lia.latency.p95{...}" \
#     -H "DD-API-KEY: $DD_API_KEY"

fetch_p95_latency() {
    local endpoint="$1"
    # TODO: substituir por chamada real ao provider
    # Por enquanto, retorna placeholder — failsafe (high value para forçar attention)
    echo "9999"  # ← substituir
}

fetch_error_rate() {
    local endpoint="$1"
    # TODO: substituir por chamada real
    echo "10.0"  # ← substituir
}

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Verificar cada endpoint
# ─────────────────────────────────────────────────────────────────────────────

violations=0
warnings=0

for endpoint in "${!LATENCY_P95_MAX[@]}"; do
    p95=$(fetch_p95_latency "$endpoint")
    err=$(fetch_error_rate "$endpoint")

    p95_max=${LATENCY_P95_MAX[$endpoint]}
    err_max=${ERROR_RATE_MAX[$endpoint]:-2.0}

    status="✓"
    if (( $(echo "$p95 > $p95_max" | bc -l) )); then
        status="✗"
        ((violations++))
        echo "  ❌ $endpoint: p95=${p95}ms > max=${p95_max}ms (VIOLATION)"
    elif (( $(echo "$p95 > $p95_max * 0.9" | bc -l) )); then
        status="⚠"
        ((warnings++))
        echo "  ⚠️  $endpoint: p95=${p95}ms approaching max=${p95_max}ms"
    fi

    if (( $(echo "$err > $err_max" | bc -l) )); then
        status="✗"
        ((violations++))
        echo "  ❌ $endpoint: error_rate=${err}% > max=${err_max}% (VIOLATION)"
    fi

    if [ "$status" = "✓" ]; then
        echo "  ✓ $endpoint: p95=${p95}ms, error=${err}% (OK)"
    fi
done

echo ""
echo "─────────────────────────────────────────────────────────"
echo "Resultado: $violations violations, $warnings warnings"

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Decisão
# ─────────────────────────────────────────────────────────────────────────────

if (( violations > 0 )); then
    echo "🔴 AUTO-ROLLBACK RECOMENDADO"
    echo ""
    echo "Próxima ação: ./canary_rollback.sh"
    echo ""
    exit 2
fi

if (( warnings > 0 )); then
    echo "🟡 MANUAL REVIEW (warnings detectadas)"
    echo ""
    echo "Sugestão: aguardar 1h, rodar de novo. Se persistir, rollback."
    echo ""
    exit 1
fi

echo "🟢 HEALTHY — prosseguir para próximo estágio"
echo ""
exit 0
