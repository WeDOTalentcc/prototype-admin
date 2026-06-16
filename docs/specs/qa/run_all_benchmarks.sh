#!/bin/bash
# run_all_benchmarks.sh — Executa todos os benchmarks de uma vez
# Uso: BASE_URL=https://SUA-URL.repl.co LIA_TOKEN=seu_token bash run_all_benchmarks.sh

BASE_URL="${BASE_URL:-http://localhost:3000}"
TOKEN="${LIA_TOKEN:-}"
OUTPUT_DIR="./qa_results_$(date +%Y%m%d_%H%M%S)"

if [ -z "$TOKEN" ]; then
  echo "❌ Token não definido. Exporte: export LIA_TOKEN=seu_token"
  echo "   Para obter: abra o app no browser → F12 → Console → localStorage.getItem('access_token')"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
echo "📁 Resultados em: $OUTPUT_DIR"
echo "🌐 Base URL: $BASE_URL"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔷 [1/3] Benchmark de Chat / UI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 benchmark_prompts.py \
  --base-url "$BASE_URL" \
  --token "$TOKEN" \
  --output "$OUTPUT_DIR" \
  --verbose

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔷 [2/3] Benchmark de Agentes de Processo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 benchmark_agents.py \
  --base-url "$BASE_URL" \
  --token "$TOKEN" \
  --output "$OUTPUT_DIR" \
  --verbose

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔷 [3/3] Teste de Fairness (Regra dos 4/5)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 test_agent_fairness.py \
  --base-url "$BASE_URL" \
  --token "$TOKEN" \
  --output "$OUTPUT_DIR" \
  --verbose

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Concluído! Resultados em: $OUTPUT_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ls -lh "$OUTPUT_DIR"
