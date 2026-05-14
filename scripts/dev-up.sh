#!/usr/bin/env bash
# Task #1079 — bootstrap único para o ambiente de dev local.
#
# Sobe redis + lia-backend + dev-server (frontend) em ordem com healthcheck
# entre cada etapa. Idempotente: se um serviço já está saudável, não relança.
#
# Uso:
#   ./scripts/dev-up.sh           # sobe tudo
#   ./scripts/dev-up.sh --no-fe   # apenas redis + backend (útil quando o
#                                 # workflow `dev-server` já gerencia o FE)
#
# Nota: este script é projetado para uso interativo no shell. Para os
# workflows do Replit (lia-backend, dev-server) os comandos canônicos
# continuam embutidos no workflow — este script existe para devs locais
# e para a suíte E2E poder bootstrappar tudo numa única invocação.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WITH_FE=1
for arg in "$@"; do
  case "$arg" in
    --no-fe) WITH_FE=0 ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0
      ;;
  esac
done

log() { echo "[dev-up] $*"; }
fail() { echo "[dev-up] ERRO: $*" >&2; exit 1; }

wait_http() {
  local url="$1" max="${2:-60}" i
  for i in $(seq 1 "$max"); do
    if curl -fsS --connect-timeout 2 --max-time 5 -o /dev/null "$url" 2>/dev/null; then
      log "   $url OK em ${i}s"
      return 0
    fi
    sleep 1
  done
  return 1
}

wait_port_free() {
  local port="$1" max="${2:-15}" i
  for i in $(seq 1 "$max"); do
    if ! fuser "${port}/tcp" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

# --- 1. Redis ---------------------------------------------------------------
log "1/3 — Redis"
if redis-cli ping 2>/dev/null | grep -q PONG; then
  log "   redis já está respondendo"
else
  redis-server --daemonize yes >/dev/null 2>&1 || fail "falha ao subir redis-server"
  for i in 1 2 3 4 5; do
    if redis-cli ping 2>/dev/null | grep -q PONG; then
      log "   redis OK"
      break
    fi
    sleep 1
  done
fi

# --- 2. LIA backend (FastAPI) ----------------------------------------------
log "2/3 — lia-backend (port 8001)"
if curl -fsS --max-time 3 -o /dev/null "http://127.0.0.1:8001/api/v1/health" 2>/dev/null; then
  log "   backend já saudável — skip restart"
else
  log "   matando processo antigo na 8001 (se houver)..."
  fuser -k -KILL 8001/tcp >/dev/null 2>&1 || true
  wait_port_free 8001 15 || fail "porta 8001 não liberou em 15s"
  log "   subindo uvicorn em background..."
  (
    cd "$ROOT/lia-agent-system"
    PYTHONUNBUFFERED=1 nohup python3 -m uvicorn app.main:app \
      --host 0.0.0.0 --port 8001 \
      > /tmp/lia-backend-stdout.log 2>&1 &
    disown
  )
  if wait_http "http://127.0.0.1:8001/api/v1/health" 60; then
    log "   backend OK"
  else
    fail "backend não ficou saudável em 60s — ver /tmp/lia-backend-stdout.log"
  fi
fi

# --- 3. Frontend (dev-server) ----------------------------------------------
if [ "$WITH_FE" = "1" ]; then
  log "3/3 — dev-server (port 5000)"
  if curl -fsS --max-time 3 -o /dev/null "http://127.0.0.1:5000/" 2>/dev/null; then
    log "   frontend já saudável — skip"
  else
    log "   matando processo antigo na 5000 (se houver)..."
    fuser -k -KILL 5000/tcp >/dev/null 2>&1 || true
    wait_port_free 5000 15 || fail "porta 5000 não liberou em 15s"
    log "   subindo `npm run dev` em background..."
    (
      cd "$ROOT/plataforma-lia"
      nohup npm run dev > /tmp/dev-server-stdout.log 2>&1 &
      disown
    )
    if wait_http "http://127.0.0.1:5000/" 90; then
      log "   frontend OK"
    else
      fail "frontend não ficou saudável em 90s — ver /tmp/dev-server-stdout.log"
    fi
  fi
else
  log "3/3 — frontend skipado (--no-fe)"
fi

log "✅ ambiente pronto"
