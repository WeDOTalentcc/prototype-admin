#!/bin/bash
set -e

echo "=== Post-merge setup ==="

if [ -f "plataforma-lia/package.json" ]; then
  echo "[1/2] Installing frontend dependencies..."
  cd plataforma-lia && npm install --legacy-peer-deps < /dev/null && cd ..
fi

if [ -f "lia-agent-system/requirements.txt" ]; then
  echo "[2/2] Installing backend dependencies..."
  cd lia-agent-system && pip install -q -r requirements.txt < /dev/null && cd ..
fi

echo "=== Post-merge setup complete ==="
