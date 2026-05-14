#!/usr/bin/env bash
# Task #1079 — thin wrapper sobre run-pw-cenario.sh (mantido para
# compatibilidade com workflows que invocam este nome diretamente).
exec "$(dirname "$0")/run-pw-cenario.sh" \
  "pw-cenario-A" \
  "${PW_SPEC:-e2e/tests/wizard/02-vaga-tecnica.spec.ts}" \
  "${PW_PROJECT:-desktop-chrome}"
