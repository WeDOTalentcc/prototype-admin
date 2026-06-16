#!/usr/bin/env bash
# pre-commit-hook.sh — sensores de qualidade WeDOTalent (GAP-00-008)
#
# ARQUITETURA:
#   Rápidos (sempre rodam, bloqueadores < 5s):
#     check_migration_merge_safety.py  — detecta alembic heads conflitantes
#   Lentos (warn-only por default, 20-50s cada):
#     check_pydantic_conventions.py    — R1/R2/R3/R6 multi-tenancy
#     check_capability_catalog_sync.py — ghosts em tool_permissions.yaml
#     check_tool_registry_sync.py      — ghosts em tool_registry_metadata.yaml
#
# SKIP:
#   SKIP_SLOW_SENSORS=1 git commit ...  — pula os lentos (mantém rápidos)
#   SKIP_ALL_SENSORS=1  git commit ...  — pula tudo (emergência)
#
# Sensor output é otimizado pra LLM (instruções de fix em PT-BR inline).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIA_DIR="$(git rev-parse --show-toplevel)/lia-agent-system"
PYTHON="${PYTHON:-python3}"

# ── Bail-outs ─────────────────────────────────────────────────────────────────
if [[ "${SKIP_ALL_SENSORS:-0}" == "1" ]]; then
    echo "[pre-commit] SKIP_ALL_SENSORS=1 — sensores desabilitados." >&2
    exit 0
fi

if [[ ! -d "$LIA_DIR" ]]; then
    echo "[pre-commit] lia-agent-system não encontrado em $LIA_DIR — skip." >&2
    exit 0
fi

cd "$LIA_DIR"

FAILED=0
SLOW_SKIPPED=0

# ── Helper ────────────────────────────────────────────────────────────────────
run_sensor() {
    local name="$1"
    shift
    echo "[pre-commit] ▶ $name"
    if "$PYTHON" "$@"; then
        echo "[pre-commit] ✓ $name"
    else
        echo "[pre-commit] ✗ $name FALHOU" >&2
        FAILED=1
    fi
}

run_sensor_warn() {
    local name="$1"
    shift
    echo "[pre-commit] ▶ $name (warn-only)"
    if ! "$PYTHON" "$@" 2>&1; then
        echo "[pre-commit] ⚠  $name reportou violações (warn-only, commit continua)" >&2
    fi
}

# ── RÁPIDOS — sempre rodam, bloqueadores ──────────────────────────────────────
run_sensor "migration-merge-safety" \
    scripts/check_migration_merge_safety.py

# ── LENTOS — warn-only, puláveis via SKIP_SLOW_SENSORS=1 ─────────────────────
if [[ "${SKIP_SLOW_SENSORS:-0}" == "1" ]]; then
    echo "[pre-commit] SKIP_SLOW_SENSORS=1 — sensores lentos pulados."
    SLOW_SKIPPED=1
else
    run_sensor_warn "pydantic-conventions" \
        scripts/check_pydantic_conventions.py app/

    run_sensor_warn "capability-catalog-sync" \
        scripts/check_capability_catalog_sync.py

    run_sensor_warn "tool-registry-sync" \
        scripts/check_tool_registry_sync.py
fi

# ── Resultado ─────────────────────────────────────────────────────────────────
if [[ "$FAILED" -ne 0 ]]; then
    echo ""
    echo "[pre-commit] ❌ Commit bloqueado por sensor(es) acima." >&2
    echo "[pre-commit] Fix as violações ou use: SKIP_ALL_SENSORS=1 git commit (emergência)" >&2
    exit 1
fi

if [[ "$SLOW_SKIPPED" -eq 1 ]]; then
    echo "[pre-commit] ✅ OK (sensores lentos pulados — rode 'make ci' para suite completa)"
else
    echo "[pre-commit] ✅ OK"
fi

exit 0
