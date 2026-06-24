#!/bin/bash
# SENSOR: detecta proxies com REGRA 6 anti-pattern (X-Company-ID header manual)
# Tipo: Computacional (grep determinístico)
# Baseado em CLAUDE.md REGRA 6

set -e
PROXY_DIR="${1:-src/app/api/backend-proxy}"
VIOLATIONS=()

# Detecta: 'X-Company-ID' header construído manualmente em route.ts files
while IFS= read -r line; do
    file=$(echo "$line" | cut -d: -f1)
    lineno=$(echo "$line" | cut -d: -f2)
    # Exclude canonical files (proxy-handler.ts and auth-headers.ts are allowed)
    if [[ "$file" != *"proxy-handler"* && "$file" != *"auth-headers"* && "$file" != *"tenant_guard"* ]]; then
        VIOLATIONS+=("$file:$lineno")
    fi
done < <(grep -rn "X-Company-ID.*||" "$PROXY_DIR" 2>/dev/null | grep -v "node_modules" | grep -v ".next" || true)

# Also detect local getAuthHeaders redefining X-Company-ID with fallback
while IFS= read -r line; do
    file=$(echo "$line" | cut -d: -f1)
    lineno=$(echo "$line" | cut -d: -f2)
    if [[ "$file" != *"proxy-handler"* && "$file" != *"auth-headers"* ]]; then
        VIOLATIONS+=("$file:$lineno")
    fi
done < <(grep -rn "admin_company\|admin_user" "$PROXY_DIR" 2>/dev/null | grep -v "node_modules" | grep -v ".next" || true)

if [ ${#VIOLATIONS[@]} -gt 0 ]; then
    echo "❌ REGRA 6 VIOLATION — Proxy com X-Company-ID ou fallback admin_company detectado:"
    echo ""
    for v in "${VIOLATIONS[@]}"; do
        echo "  $v"
    done
    echo ""
    echo "→ Fix: substituir por createProxyHandlers de @/lib/api/proxy-handler"
    echo "  export const { dynamic, POST } = createProxyHandlers({ backendPath: '/api/v1/...' })"
    echo "  Ver CLAUDE.md REGRA 6 para detalhes."
    exit 1
else
    echo "✅ REGRA 6: nenhum proxy com anti-pattern X-Company-ID fallback encontrado"
    exit 0
fi
