#!/usr/bin/env bash
# Run all 5 harness sensors (R-006, R-007, R-008 + 2 runtime probes).
#
# Modes:
#   --block       — exit 1 if any sensor reports violations (CI mode)
#   --warn-only   — log violations but exit 0 (default, dev mode)
#   --json        — emit machine-readable summary at end
#
# Usage:
#   scripts/run_all_sensors.sh
#   scripts/run_all_sensors.sh --block          # for CI
#   scripts/run_all_sensors.sh --skip runtime   # only static sensors (CI without app)
#
# Exit codes:
#   0 — all sensors GREEN (or --warn-only)
#   1 — at least one violation in --block mode
#   2 — usage error

set -uo pipefail

MODE="warn-only"
SKIP_RUNTIME=0
EMIT_JSON=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --block) MODE="block" ; shift ;;
    --warn-only) MODE="warn-only" ; shift ;;
    --skip)
      case "$2" in
        runtime) SKIP_RUNTIME=1 ;;
        *) echo "❌ unknown --skip target: $2" ; exit 2 ;;
      esac
      shift 2 ;;
    --json) EMIT_JSON=1 ; shift ;;
    *) echo "❌ unknown arg: $1" ; exit 2 ;;
  esac
done

cd "$REPO_ROOT"

declare -a SENSOR_NAMES
declare -a SENSOR_EXITS
declare -a SENSOR_TIMES

run_sensor() {
  local name="$1"
  local cmd="$2"
  local start=$(date +%s)
  echo ""
  echo "═══════════════════════════════════════════════"
  echo " ▶ $name"
  echo "═══════════════════════════════════════════════"
  eval "$cmd"
  local rc=$?
  local elapsed=$(( $(date +%s) - start ))
  SENSOR_NAMES+=("$name")
  SENSOR_EXITS+=("$rc")
  SENSOR_TIMES+=("$elapsed")
  if [[ $rc -ne 0 ]]; then
    echo ""
    echo " [exit $rc, ${elapsed}s]"
  else
    echo " [GREEN, ${elapsed}s]"
  fi
}

# ── Static sensors (no app/DB dependency) ────────────────────────────────
run_sensor "R-006 / check_required_env" \
  "python3 scripts/check_required_env.py --strict --dotenv .env"

run_sensor "R-008 / check_duplicate_pydantic_schemas" \
  "python3 scripts/check_duplicate_pydantic_schemas.py"

# ── DB-dependent sensors ─────────────────────────────────────────────────
run_sensor "R-007 / check_schema_drift" \
  "python3 scripts/check_schema_drift.py"

# ── Runtime probes (require uvicorn on localhost:8001) ───────────────────
if [[ $SKIP_RUNTIME -eq 0 ]]; then
  run_sensor "R-WIZARD / check_endpoint_smoke" \
    "python3 scripts/check_endpoint_smoke.py"
  run_sensor "R-AGENTS / check_domain_registry_health" \
    "python3 scripts/check_domain_registry_health.py --timeout 20"
else
  echo ""
  echo " (skipping runtime probes — --skip runtime)"
fi

# ── Summary ──────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════"
echo " SUMMARY"
echo "═══════════════════════════════════════════════"
fail_count=0
for i in "${!SENSOR_NAMES[@]}"; do
  rc=${SENSOR_EXITS[$i]}
  name=${SENSOR_NAMES[$i]}
  elapsed=${SENSOR_TIMES[$i]}
  if [[ $rc -eq 0 ]]; then
    echo " ✅ $name (${elapsed}s)"
  else
    echo " ❌ $name → exit $rc (${elapsed}s)"
    fail_count=$((fail_count + 1))
  fi
done

echo ""
if [[ $fail_count -eq 0 ]]; then
  echo " 🎯 All sensors GREEN."
  exit 0
fi

if [[ "$MODE" == "block" ]]; then
  echo " ❌ $fail_count sensor(s) failed — BLOCKING."
  exit 1
else
  echo " ⚠️  $fail_count sensor(s) reported violations (warn-only)."
  echo " Promote to --block mode after follow-up tasks #25 (192 schemas), #27 (196 drifts) are addressed."
  exit 0
fi
