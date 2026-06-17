#!/usr/bin/env bash
# Task #1079 — wrapper para Cenário B (vaga executiva).
exec "$(dirname "$0")/run-pw-cenario.sh" \
  "pw-cenario-B" \
  "${PW_SPEC:-e2e/tests/wizard/03-vaga-executiva.spec.ts}" \
  "${PW_PROJECT:-desktop-chrome}"
