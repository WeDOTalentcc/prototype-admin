#!/usr/bin/env bash
# Task #1134 — wrapper para o spec sentinela da Task #1128
# (nova-conversa-reset-canonical).
#
# Invocação canônica:
#   bash plataforma-lia/scripts/run-pw-cenario-reset.sh
#
# Por que existe (replit.md §"Ambiente E2E"):
#   O bug do contador de workflow-limit (mockup-sandbox managed-by-artifact
#   contando dobrado, counter 11/10) impede `configureWorkflow` de criar
#   um workflow `pw-cenario-reset` nativo. Enquanto a plataforma não
#   destrava o counter, este wrapper é a forma operacional de rodar o
#   sentinela canônico do reset de wizard — segue o mesmo contrato dos
#   demais (run-pw-cenario-{a,b,c}.sh): delega ao canônico
#   run-pw-cenario.sh com label + spec + project.
exec "$(dirname "$0")/run-pw-cenario.sh" \
  "pw-cenario-reset" \
  "${PW_SPEC:-e2e/tests/wizard/15-nova-conversa-reset.spec.ts}" \
  "${PW_PROJECT:-desktop-chrome}"
