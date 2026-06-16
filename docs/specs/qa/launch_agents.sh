#!/bin/bash
set -e

cd /home/runner/workspace/docs/specs/qa

# Get fresh token
TOKEN=$(curl -sL -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@wedotalent.com","password":"demo123"}' | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d['access_token'])")

if [ -z "$TOKEN" ]; then
  echo "ERRO: Token vazio"
  exit 1
fi

echo "Token OK: ${TOKEN:0:20}..."
echo "Iniciando benchmark_agents..."

python3 benchmark_agents.py \
  --base-url http://localhost:5000 \
  --token "$TOKEN" \
  --timeout 120 \
  2>&1

echo "CONCLUIDO"
