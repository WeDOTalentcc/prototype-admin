#!/bin/bash
set -e

echo "=== Post-merge setup ==="

if [ -f "plataforma-lia/package.json" ]; then
  echo "[1/2] Installing frontend dependencies..."
  cd plataforma-lia && npm install --legacy-peer-deps < /dev/null && cd ..
fi

# NOTE on interpreter choice: this script intentionally uses bare `pip` and
# bare `python -m alembic` rather than `python3 -m pip`. On Replit/Nix, `pip`
# is a wrapper that installs into the writable per-Repl env, while
# `python3 -m pip` resolves to the immutable Nix store and is blocked by
# PEP 668. Both `pip` and `python` resolve to the same env here in practice,
# so Alembic finds every package `pip` just installed.

if [ -f "lia-agent-system/requirements.txt" ]; then
  echo "[2/3] Installing backend dependencies..."
  ( cd lia-agent-system && pip install -q -r requirements.txt < /dev/null )
fi

# Apply Alembic migrations so newly merged model changes don't leave the
# running DB in an "ORM expects column X but it doesn't exist" state.
# (Triggered the 2026-04-17 outage where Task #346 added candidates.company_id
#  in code+migration 082, but the migration was never applied → all candidate
#  list/search endpoints returned 500 with UndefinedColumnError.)
if [ -f "lia-agent-system/alembic.ini" ]; then
  echo "[3/4] Applying database migrations (alembic upgrade head)..."
  ( cd lia-agent-system && python -m alembic upgrade head < /dev/null )
fi

if [ -f "lia-agent-system/scripts/seed_first_party_agents.py" ]; then
  echo "[4/4] Seeding first-party WeDo agents (idempotent upsert)..."
  ( cd lia-agent-system && python scripts/seed_first_party_agents.py < /dev/null )
fi

echo "=== Post-merge setup complete ==="
