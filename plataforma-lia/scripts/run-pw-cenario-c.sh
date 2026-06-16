#!/usr/bin/env bash
# Task #1079 — wrapper para Cenário C (HITL correção).
exec "$(dirname "$0")/run-pw-cenario.sh" \
  "pw-cenario-C" \
  "${PW_SPEC:-e2e/tests/wizard/08-hitl-correcao.spec.ts}" \
  "${PW_PROJECT:-desktop-chrome}"
