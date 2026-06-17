#!/bin/bash
cd /home/runner/workspace/docs/specs/qa

# Get fresh token
TOKEN=$(curl -sL -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@wedotalent.com","password":"demo123"}' | \
  python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

echo "Token: ${TOKEN:0:30}..."
echo "Starting fairness test with 120s timeout per candidate..."

python3 test_agent_fairness.py \
  --base-url http://localhost:5000 \
  --token "$TOKEN" \
  --timeout 120 \
  --verbose 2>&1
