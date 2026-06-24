#!/usr/bin/env bash
set +e
WS=/home/runner/workspace
echo "==LIA-DIAG== boot $(date -u +%H:%M:%S)"

# Resolve newest 64-bit libstdc++ (wheels + node 20 need a recent GLIBCXX).
LIBSTDCPP=""; BESTV=-1
for f in /nix/store/*gcc*-lib/lib/libstdc++.so.6; do
  [ -e "$f" ] || continue
  cls="$(od -An -t u1 -j 4 -N 1 "$f" 2>/dev/null | tr -d ' ')"; [ "$cls" = "2" ] || continue
  real="$(readlink -f "$f")"; v="${real##*.0.}"; case "$v" in ''|*[!0-9]*) v=0;; esac
  if [ "$v" -gt "$BESTV" ]; then BESTV="$v"; LIBSTDCPP="$(dirname "$f")"; fi
done
[ -n "$LIBSTDCPP" ] && export LD_LIBRARY_PATH="${LIBSTDCPP}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
echo "==LIA-DIAG== libstdcpp=$LIBSTDCPP v=$BESTV"

# Rebuild PYTHONPATH from pip .pth records (nix python has user-site disabled).
SPDIR="$WS/.pythonlibs/lib/python3.11/site-packages"
PYP="$SPDIR"
if [ -d "$SPDIR" ]; then
  for pth in "$SPDIR"/*.pth; do
    [ -e "$pth" ] || continue
    while IFS= read -r line; do case "$line" in /*) PYP="$PYP:$line";; esac; done < "$pth"
  done
fi
export PYTHONPATH="$PYP"
export PYTHONUSERBASE="$WS/.pythonlibs"
export PYTHONUNBUFFERED=1

# Resolve python3.11
PY_BIN=""
for c in "$(command -v python3.11 2>/dev/null)" /nix/store/*python3-3.11*/bin/python3.11; do
  [ -n "$c" ] && [ -x "$c" ] || continue
  if timeout 30 "$c" -c 'import pydantic_core,numpy,uvicorn,lia_config' >/dev/null 2>&1; then PY_BIN="$c"; break; fi
done

# Resolve node 20 (prefer PATH, then nix store; skip wrapper derivations).
NODE_BIN=""
N="$(command -v node 2>/dev/null)"; if [ -n "$N" ] && "$N" --version >/dev/null 2>&1; then NODE_BIN="$N"; fi
if [ -z "$NODE_BIN" ]; then
  for d in /nix/store/*nodejs-20*/bin; do
    case "$d" in *wrapped*) continue;; esac
    if [ -x "$d/node" ] && "$d/node" --version >/dev/null 2>&1; then NODE_BIN="$d/node"; break; fi
  done
fi

echo "==LIA-DIAG== py=$PY_BIN node=$NODE_BIN"
if [ -z "$PY_BIN" ] || [ -z "$NODE_BIN" ]; then
  echo "==LIA-FATAL== unresolved py=$PY_BIN node=$NODE_BIN libstdcpp=$LIBSTDCPP"; sleep 8; exit 1
fi

# Best-effort local redis (the app uses managed Redis via env; this is only a fallback).
RS="$(command -v redis-server 2>/dev/null)"
[ -z "$RS" ] && for d in /nix/store/*redis*/bin; do [ -x "$d/redis-server" ] && { RS="$d/redis-server"; break; }; done
[ -n "$RS" ] && "$RS" --daemonize yes --save '' --appendonly no >/dev/null 2>&1 || true

export PATH="$(dirname "$NODE_BIN"):$(dirname "$PY_BIN"):$PATH"

# Apply pending DB migrations before starting services.
echo "==LIA-DIAG== running alembic upgrade head"
( cd "$WS/lia-agent-system" && APP_ENV=production "$PY_BIN" -m alembic upgrade head 2>&1 ) || echo "==LIA-WARN== alembic upgrade failed (continuing)"

echo "==LIA-DIAG== starting backend(127.0.0.1:8001) + frontend(0.0.0.0:5000) + celery"

( cd "$WS/lia-agent-system" && APP_ENV=production "$PY_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --timeout-keep-alive 30 --no-access-log ) &
BACKEND_PID=$!

( cd "$WS/plataforma-lia" && HOSTNAME=0.0.0.0 PORT=5000 "$NODE_BIN" .next/standalone/server.js ) &
FRONTEND_PID=$!

( cd "$WS/lia-agent-system" && APP_ENV=production PYTHONUNBUFFERED=1 "$PY_BIN" -m celery -A app.core.celery_app worker --loglevel=warning --concurrency=2 -Q sourcing_high,evaluation_normal,vagas_normal,onboarding_low ) &
WORKER_PID=$!

# Beat roda em loop de auto-restart — crash do beat NAO derruba o deployment inteiro.
( while true; do
    ( cd "$WS/lia-agent-system" && APP_ENV=production PYTHONUNBUFFERED=1 "$PY_BIN" -m celery -A app.core.celery_app beat --loglevel=warning --schedule=/tmp/celerybeat-schedule )
    echo "==LIA-WARN== celery beat exited (code $?), restarting in 15s"
    sleep 15
  done ) &
BEAT_PID=$!

trap 'kill $BACKEND_PID $FRONTEND_PID $WORKER_PID $BEAT_PID 2>/dev/null || true' TERM INT EXIT

# Apenas os 3 processos críticos derrubam o deployment se saírem.
wait -n $BACKEND_PID $FRONTEND_PID $WORKER_PID
echo "==LIA-FATAL== a core process exited; restarting deployment"
kill $BACKEND_PID $FRONTEND_PID $WORKER_PID $BEAT_PID 2>/dev/null || true
exit 1
