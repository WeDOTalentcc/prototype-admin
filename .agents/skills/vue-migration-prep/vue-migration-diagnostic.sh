#!/bin/bash
# Vue Migration Diagnostic — Calcula % portabilidade por arquivo e total
# Uso: bash .agents/skills/vue-migration-prep/vue-migration-diagnostic.sh [diretório]

DIR="${1:-plataforma-lia/src}"
REPORT_FILE="/tmp/vue-migration-report-$(date +%Y%m%d-%H%M%S).md"

count_grep() {
  local result
  result=$(grep -rn "$1" "$DIR" ${2:+--include="$2"} ${3:+--include="$3"} 2>/dev/null | grep -v "node_modules\|\.d\.ts\|design-tokens\|\.test\.\|\.spec\.\|\.stories\.\|components/ui/" | wc -l)
  echo "${result// /}"
}

count_grep_pipe() {
  local result
  result=$(grep -rn "$1" "$DIR" ${3:+--include="$3"} 2>/dev/null | grep -v "node_modules\|\.d\.ts\|components/ui/" | grep -i "$2" | wc -l)
  echo "${result// /}"
}

count_find() {
  local result
  result=$(eval "find \"$DIR\" $1 2>/dev/null | wc -l")
  echo "${result// /}"
}

{
echo "# Vue Migration Diagnostic Report"
echo ""
echo "**Gerado em:** $(date '+%Y-%m-%d %H:%M:%S')"
echo "**Diretório:** $DIR"
echo ""

echo "## 1. Anti-Patterns React-Only"
echo ""

AP_COUNT=$(count_grep "cloneElement\|Children\.map\|useImperativeHandle\|dangerouslySetInnerHTML" "*.tsx" "*.ts")
FORWARD_REF=$(count_grep "forwardRef" "*.tsx" "*.ts")
if [ "$AP_COUNT" -gt 0 ] 2>/dev/null; then
  echo "**$AP_COUNT anti-patterns criticos + $FORWARD_REF forwardRef (shadcn/ui, menor prioridade):**"
  grep -rn "cloneElement\|Children\.map\|useImperativeHandle\|dangerouslySetInnerHTML" "$DIR" --include="*.tsx" --include="*.ts" 2>/dev/null | grep -v "node_modules\|\.d\.ts" | head -20 || true
else
  AP_COUNT=0
  echo "Nenhum anti-pattern React-only encontrado."
fi
echo ""

echo "## 2. Context Usage"
echo ""
CTX_COUNT=$(count_grep "useContext\|createContext" "*.tsx" "*.ts")
: "${CTX_COUNT:=0}"
echo "**$CTX_COUNT usos de Context** (cada um precisa virar Pinia store)"
if [ "$CTX_COUNT" -gt 0 ] 2>/dev/null; then
  grep -rn "useContext\|createContext" "$DIR" --include="*.tsx" --include="*.ts" 2>/dev/null | head -15 || true
fi
echo ""

echo "## 3. Componentes Grandes (>150 linhas)"
echo ""
LARGE_COUNT=0
while IFS= read -r line; do
  LINES=$(echo "$line" | awk '{print $1}')
  FILE=$(echo "$line" | awk '{print $2}')
  if [ -n "$LINES" ] && [ "$LINES" -gt 150 ] 2>/dev/null; then
    echo "- **$FILE** ($LINES linhas) — precisa extrair hook"
    LARGE_COUNT=$((LARGE_COUNT + 1))
  fi
done < <(find "$DIR" -name "*.tsx" -exec wc -l {} \; 2>/dev/null | sort -rn | head -30)
if [ "$LARGE_COUNT" -eq 0 ]; then
  echo "Nenhum componente > 150 linhas."
fi
echo ""

echo "## 4. Props Tipadas"
echo ""
PROPS_COUNT=$(count_grep "interface.*Props" "*.tsx")
: "${PROPS_COUNT:=0}"
echo "**$PROPS_COUNT componentes com Props tipadas (interface)**"
echo ""

echo "## 5. Callbacks on*"
echo ""
ON_COUNT=$(count_grep "on[A-Z][a-zA-Z]*[?:]\s*(" "*.tsx")
: "${ON_COUNT:=0}"
echo "**$ON_COUNT callbacks on* encontrados**"
echo ""

echo "## 6. Hooks Separados"
echo ""
HOOK_COUNT=$(count_find "-name 'use-*.ts' -not -name '*.tsx'")
: "${HOOK_COUNT:=0}"
echo "**$HOOK_COUNT hooks separados** (composables em Vue)"
echo ""

echo "## 7. Design System Conformidade (via Figma)"
echo ""
CYAN_BUTTONS=$(count_grep_pipe "bg-cyan\|bg-\[#60BED1\]" "button\|btn" "*.tsx")
: "${CYAN_BUTTONS:=0}"
ROUNDED_VIOLATIONS=$(count_grep "rounded-xl\|rounded-2xl\|rounded-3xl" "*.tsx")
: "${ROUNDED_VIOLATIONS:=0}"
SHADOW_EXCESS=$(count_grep "shadow-2xl" "*.tsx")
: "${SHADOW_EXCESS:=0}"
DEPRECATED_COLORS=$(count_grep "#FAFAFA\|#E8E8E8\|#666666\|#999999\|#2D2D2D\|#E4EBEF" "*.tsx")
: "${DEPRECATED_COLORS:=0}"
DS_VIOLATIONS=$((CYAN_BUTTONS + ROUNDED_VIOLATIONS + SHADOW_EXCESS + DEPRECATED_COLORS))

echo "| Check | Count | Status |"
echo "|-------|-------|--------|"
echo "| Cyan em botoes | $CYAN_BUTTONS | $([ "$CYAN_BUTTONS" -eq 0 ] && echo 'OK' || echo 'FAIL') |"
echo "| Rounded violations | $ROUNDED_VIOLATIONS | $([ "$ROUNDED_VIOLATIONS" -eq 0 ] && echo 'OK' || echo 'WARN') |"
echo "| Shadow excess | $SHADOW_EXCESS | $([ "$SHADOW_EXCESS" -eq 0 ] && echo 'OK' || echo 'WARN') |"
echo "| Deprecated colors | $DEPRECATED_COLORS | $([ "$DEPRECATED_COLORS" -eq 0 ] && echo 'OK' || echo 'WARN') |"
echo ""

HELPER_COUNT=$(count_grep "getButtonClasses\|getCardClasses\|getInputClasses\|getBadgeClasses" "*.tsx" "*.ts")
: "${HELPER_COUNT:=0}"
echo "**Design token helpers usados:** $HELPER_COUNT"
echo ""

echo "## 8. Resumo por Tipo de Arquivo"
echo ""
TYPES_TS=$(count_find "-name 'types.ts' -o -name '*.types.ts' -o -name 'constants.ts'")
: "${TYPES_TS:=0}"
UTILS_TS=$(find "$DIR" -path "*/utils/*.ts" -o -path "*/lib/*.ts" 2>/dev/null | grep -v ".tsx" | wc -l)
UTILS_TS="${UTILS_TS// /}"
: "${UTILS_TS:=0}"
HOOKS_TS=$HOOK_COUNT
COMPONENTS_TSX=$(count_find "-name '*.tsx'")
: "${COMPONENTS_TSX:=0}"

echo "| Tipo | Qtd | Portabilidade | Caminho |"
echo "|------|-----|---------------|---------|"
echo "| types/constants | $TYPES_TS | 100% Direto | Codigo |"
echo "| utils/lib | $UTILS_TS | 95% Direto | Codigo |"
echo "| hooks (use-*) | $HOOKS_TS | 90% Adaptacao | Codigo |"
echo "| components (.tsx) | $COMPONENTS_TSX | 50-70% | Ambos |"
echo ""

TOTAL_FILES=$((TYPES_TS + UTILS_TS + HOOKS_TS + COMPONENTS_TSX))
DIRECT_READY=$((TYPES_TS + UTILS_TS))
ADAPT_NEEDED=$HOOKS_TS
REBUILD_NEEDED=$LARGE_COUNT

if [ "$TOTAL_FILES" -gt 0 ]; then
  CODE_DIRECT=$((TYPES_TS * 100 + UTILS_TS * 95 + HOOKS_TS * 90))
  CODE_COMPONENT=$((COMPONENTS_TSX * 60))
  CODE_TOTAL=$((CODE_DIRECT + CODE_COMPONENT))
  CODE_SCORE=$((CODE_TOTAL / TOTAL_FILES))

  PENALTY=0
  if [ "$AP_COUNT" -gt 0 ]; then
    P=$AP_COUNT; [ "$P" -gt 20 ] && P=20; PENALTY=$((PENALTY + P))
  fi
  if [ "$CTX_COUNT" -gt 5 ]; then
    P=$((CTX_COUNT - 5)); [ "$P" -gt 10 ] && P=10; PENALTY=$((PENALTY + P))
  fi
  if [ "$LARGE_COUNT" -gt 3 ]; then
    P=$((LARGE_COUNT - 3)); [ "$P" -gt 10 ] && P=10; PENALTY=$((PENALTY + P))
  fi
  CODE_SCORE=$((CODE_SCORE - PENALTY))
  [ "$CODE_SCORE" -lt 0 ] && CODE_SCORE=0
  [ "$CODE_SCORE" -gt 100 ] && CODE_SCORE=100

  if [ "$DS_VIOLATIONS" -gt 100 ]; then DS_PENALTY=30; else DS_PENALTY=$((DS_VIOLATIONS * 30 / 100)); fi
  FIGMA_BASE=85
  [ "$HELPER_COUNT" -gt 10 ] && FIGMA_BASE=$((FIGMA_BASE + 5))
  [ "$PROPS_COUNT" -gt "$((COMPONENTS_TSX / 2))" ] && FIGMA_BASE=$((FIGMA_BASE + 5))
  FIGMA_SCORE=$((FIGMA_BASE - DS_PENALTY))
  [ "$FIGMA_SCORE" -lt 0 ] && FIGMA_SCORE=0
  [ "$FIGMA_SCORE" -gt 100 ] && FIGMA_SCORE=100

  TOTAL_SCORE=$(( (CODE_SCORE + FIGMA_SCORE) / 2 ))
else
  CODE_SCORE=0
  FIGMA_SCORE=0
  TOTAL_SCORE=0
fi

echo "---"
echo ""
echo "## SCORE FINAL"
echo ""
echo "| Metrica | Valor |"
echo "|---------|-------|"
echo "| **Score Geral** | **${TOTAL_SCORE}%** |"
echo "| Via Codigo (direto) | ${CODE_SCORE}% |"
echo "| Via Figma (visual) | ${FIGMA_SCORE}% |"
echo "| Total de Arquivos | $TOTAL_FILES |"
echo "| Migration-Ready (copiar) | $DIRECT_READY |"
echo "| Adaptacao Necessaria | $ADAPT_NEEDED |"
echo "| Reconstruir | $REBUILD_NEEDED |"
echo "| Anti-patterns | $AP_COUNT |"
echo "| Context usages | $CTX_COUNT |"
echo "| Componentes >150 linhas | $LARGE_COUNT |"
echo "| DS violations | $DS_VIOLATIONS |"
echo ""

echo "## Acoes Recomendadas"
echo ""
[ "$AP_COUNT" -gt 0 ] && echo "- [ ] Eliminar $AP_COUNT anti-patterns React-only"
[ "$CTX_COUNT" -gt 5 ] && echo "- [ ] Reduzir $CTX_COUNT contextos para hooks isolados"
[ "$LARGE_COUNT" -gt 0 ] && echo "- [ ] Extrair hooks de $LARGE_COUNT componentes grandes"
[ "$DS_VIOLATIONS" -gt 0 ] && echo "- [ ] Corrigir $DS_VIOLATIONS violacoes DS v4.2.1"
[ "$PROPS_COUNT" -lt "$((COMPONENTS_TSX / 2))" ] 2>/dev/null && echo "- [ ] Tipar props em componentes restantes"
[ "$HELPER_COUNT" -lt 5 ] && echo "- [ ] Usar helpers de design tokens"
echo ""
echo "---"
echo "*Relatorio gerado por vue-migration-diagnostic.sh*"

} > "$REPORT_FILE"

echo ""
echo "=========================================="
echo "  VUE MIGRATION DIAGNOSTIC COMPLETE"
echo "=========================================="
echo ""
echo "  Score Geral: ${TOTAL_SCORE}%"
echo "  Via Codigo:  ${CODE_SCORE}%"
echo "  Via Figma:   ${FIGMA_SCORE}%"
echo ""
echo "  Arquivos:    $TOTAL_FILES"
echo "  Ready:       $DIRECT_READY"
echo "  Adaptar:     $ADAPT_NEEDED"
echo "  Reconstruir: $REBUILD_NEEDED"
echo ""
echo "  Anti-patterns: $AP_COUNT"
echo "  DS violations: $DS_VIOLATIONS"
echo ""
echo "  Relatorio: $REPORT_FILE"
echo "=========================================="
