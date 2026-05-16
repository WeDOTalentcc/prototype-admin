# Runbook — Wizard de Criação de Vaga (supervisor + LLM gates)

**Última atualização:** 2026-05-16 (Task #1131 / T4.2)
**Dashboard:** `ops/grafana/lia-wizard-dashboard.json` (UID `lia-wizard-observability`)
**Domínio backend:** `lia-agent-system/app/domains/job_creation/`
**On-call:** PD service `lia-recruiter-agent`

---

## 1. Visão geral

O wizard de criação de vaga tem 2 camadas de LLM observáveis:

1. **Supervisor pre-graph** (`WizardSupervisorClassifier`, Task #1127) — classifica cada turno em 6 intents (`create_new | resume_draft | edit_published | meta_question | exit_wizard | continue_current`) ANTES de invocar o `JobCreationGraph`.
2. **Gate classifier** (`WizardGateClassifier`, Tasks #1085/#1086/#1087/#1088, GA #1130) — classifica a resposta do recrutador nos 4 HITL gates do graph (jd_enrichment, competency, wsi_questions, review).

Ambos rodam Claude Haiku (`CANONICAL_HAIKU_MODEL`) com Pydantic schema + allowlist enforced + fallback determinístico. Falhas são fail-OPEN no supervisor (cai em `continue_current`) e fail-loud no gate (mensagem de re-pergunta + audit row).

## 2. Métricas Prometheus (4)

| Métrica | Tipo | Labels | Fonte |
|---|---|---|---|
| `lia_wizard_supervisor_intent_total` | Counter | `intent`, `stage` | `wizard_session_service.py:728-745` |
| `lia_wizard_gate_classifier_total` | Counter | `stage`, `intent` | `wizard_gate_classifier.py:570` |
| `lia_wizard_gate_classifier_latency_ms` | Histogram | `stage` | `wizard_gate_classifier.py:550` |
| `lia_wizard_silent_fallback_total` | Counter | — | `wizard_session_service.py:50-56` |

Todas são best-effort (`try/except` swallow) — failures de Prometheus NUNCA bloqueiam o classifier.

## 3. Painéis do dashboard

| # | Painel | Métrica | SLO |
|---|---|---|---|
| 1 | Supervisor — intent distribution | `rate(lia_wizard_supervisor_intent_total[5m])` by intent | — |
| 2 | Supervisor — fallback rate | `continue_current` / total | < 2% (yellow > 2%, red > 5%) |
| 3 | Silent fallback (session_service) | `increase(lia_wizard_silent_fallback_total[5m])` | < 5/5min (yellow > 5, red > 20) |
| 4 | Gate latency p50/p95/p99 | `histogram_quantile(0.95, ...)` by stage | p95 < 700ms (yellow > 700ms, red > 2000ms) |
| 5 | Gate intent distribution | `rate(lia_wizard_gate_classifier_total[5m])` by (stage, intent) | — |
| 6 | Gate error rate | erro buckets (timeout/error/invalid_shape/off_allowlist/schema_invalid) | < 1% (yellow > 1%, red > 5%) |
| 7 | Review — publish_now rate | `increase(...{stage="review",intent="publish_now"}[5m])` | trend |
| 8 | Review — ask_clarification rate | `increase(...{stage="review",intent="ask_clarification"}[5m])` | < 15% de publish_now (yellow > 5, red > 20) |

## 4. Alertas recomendados (Prometheus AlertManager)

Copy/paste para `ops/prometheus/alerts/lia-wizard.yaml` quando o dashboard for promovido. **Ainda não wireado** — esta seção é a especificação para o próximo ciclo.

```yaml
groups:
  - name: lia-wizard
    rules:
      - alert: LiaWizardGateLatencyHigh
        expr: |
          histogram_quantile(0.95,
            sum by (stage, le) (rate(lia_wizard_gate_classifier_latency_ms_bucket[5m]))
          ) > 2000
        for: 5m
        labels: { severity: warning, team: lia-recruiter }
        annotations:
          summary: "Gate classifier p95 > 2s no stage {{ $labels.stage }}"
          runbook: "docs/runbooks/wizard-observability.md#5-troubleshooting"

      - alert: LiaWizardGateErrorRateHigh
        expr: |
          100 * sum(rate(lia_wizard_gate_classifier_total{intent=~"timeout|error|invalid_shape|off_allowlist|schema_invalid"}[5m]))
            / clamp_min(sum(rate(lia_wizard_gate_classifier_total[5m])), 0.0001) > 5
        for: 5m
        labels: { severity: critical, team: lia-recruiter }
        annotations:
          summary: "Gate classifier error rate > 5% (5m)"
          runbook: "docs/runbooks/wizard-observability.md#5-troubleshooting"

      - alert: LiaWizardSilentFallbackSpike
        expr: increase(lia_wizard_silent_fallback_total[5m]) > 20
        for: 5m
        labels: { severity: critical, team: lia-recruiter }
        annotations:
          summary: "Wizard session_service caindo em fallback determinístico > 20x em 5min"
          runbook: "docs/runbooks/wizard-observability.md#5-troubleshooting"

      - alert: LiaWizardSupervisorFallbackHigh
        expr: |
          100 * sum(rate(lia_wizard_supervisor_intent_total{intent="continue_current"}[5m]))
            / clamp_min(sum(rate(lia_wizard_supervisor_intent_total[5m])), 0.0001) > 5
        for: 10m
        labels: { severity: warning, team: lia-recruiter }
        annotations:
          summary: "Supervisor fallback rate > 5% (10m) — Haiku pode estar down/lento"
          runbook: "docs/runbooks/wizard-observability.md#5-troubleshooting"
```

## 5. Troubleshooting

### 5.1 Gate classifier p95 > 2s

**Sintomas:** painel #4 vermelho; recrutadores reportam wizard "travado" por vários segundos antes da próxima pergunta.

**Causas mais prováveis (em ordem de frequência):**
1. **Anthropic API lenta** — Haiku está com latência elevada em algumas regiões. Verificar status em https://status.anthropic.com e `lia-backend` logs por `[WizardGateClassifier] tokens in=… elapsed=…ms`.
2. **`AI_INTEGRATIONS_ANTHROPIC_BASE_URL` apontando para proxy lento** — em dev, o `modelfarm` pode adicionar overhead. Não usar em prod.
3. **Network egress congestionado** — checar `replit.com/status` e métricas de network do container.

**Ações:**
1. Subir o timeout temporariamente: `LIA_WIZARD_GATE_CLASSIFIER_TIMEOUT_S=10` (default 5s).
2. Se persistir > 1h, considerar rollback emergencial: `LIA_WIZARD_LLM_GATES=0` (volta ao keyword-based pré-#1085). **Ciente:** quebra os fixes de "manda bala / tá liberado" — comunicar ao time de produto.

### 5.2 Gate classifier error rate > 5%

**Sintomas:** painel #6 vermelho. Erros típicos: `timeout`, `error`, `invalid_shape`, `off_allowlist`, `schema_invalid`.

**Investigação:**
1. `lia-backend` logs: `rg "WizardGateClassifier.*fallback" /tmp/lia-backend-stdout.log | tail -50` — identifica o motivo dominante.
2. Se `off_allowlist` predominar: LLM está emitindo intent fora da allowlist do stage. Pode ser drift do prompt YAML — diffar `app/prompts/job_creation/gate_*.yaml` contra o último deploy estável.
3. Se `timeout` predominar: ver §5.1.
4. Se `schema_invalid` predominar: bug em `GateClassifierOutput` (Pydantic) — escalar pra eng.

**Mitigação imediata:** o fallback é determinístico (`ask_question` + reply pedindo re-clarificação). UX degrada mas **não corrompe state** — o wizard nunca avança em fallback.

### 5.3 Silent fallback spike (session_service)

**Sintomas:** painel #3 vermelho. Counter `lia_wizard_silent_fallback_total` subindo.

**Significado:** o `WizardSessionService` está caindo no fallback Haiku do `_generate_fallback_reply` — graph está retornando state inconsistente ou stage não reconhecido. **Mais grave que erro de classifier** porque indica que o graph propriamente dito tem bug.

**Ações:**
1. Verificar audit log: `decision_type=wizard_fallback_invoked` no `audit_logs` por tenant — qual stage e qual mensagem disparou.
2. Sentinela offline: `tests/integration/agents/test_wizard_no_canned_fallback_t3.py` — rodar para garantir que nenhum literal canned foi reintroduzido.
3. Se reproduzir em dev: rodar `pytest tests/integration/agents/test_wizard_session_continuity_t1080.py` + `test_intake_node_schema_contract.py`.
4. Emergency kill: `LIA_WIZARD_FALLBACK_LLM_DISABLED=1` faz o fallback voltar para o prefixo hard `[ATENÇÃO: estado inconsistente]` ao invés de chamar Haiku — útil quando o próprio Haiku está down.

### 5.4 Supervisor fallback alto (>5%)

**Sintomas:** painel #2 vermelho. `intent=continue_current` representa > 5% do total.

**Significado:** o supervisor está fail-OPEN (caindo em `continue_current` que é o intent de "passa pro graph") — provavelmente exceção ou timeout no Haiku. NÃO é bug de classification — é falta de classification.

**Investigação:**
1. `rg "WizardSupervisorClassifier.*fail" /tmp/lia-backend-stdout.log | tail -20`.
2. Se for timeout: subir `LIA_WIZARD_SUPERVISOR_TIMEOUT_S=8` (default 5s).
3. Se for exceção do SDK Anthropic: ver §5.1.

**Rollback:** `LIA_WIZARD_SUPERVISOR_CLASSIFIER=0` desliga o supervisor pre-graph. **Ciente:** quebra os intents `meta_question` / `exit_wizard` (caem no graph que não trata). Comunicar ao time.

## 6. Sentinelas offline (CI gates)

Antes de deployar mudanças no wizard, garanta que estes testes passam:

```bash
cd lia-agent-system
pytest tests/integration/agents/test_wizard_supervisor_t1127.py            # supervisor allowlist
pytest tests/integration/agents/test_wizard_gate_engine_t2.py              # jd_enrichment
pytest tests/integration/agents/test_wizard_gate_competency_t4.py          # competency
pytest tests/integration/agents/test_wizard_gate_wsi_questions_t5.py       # wsi_questions
pytest tests/integration/agents/test_wizard_gate_review_t6.py              # review + SOX dual-confirm
pytest tests/integration/agents/test_wizard_no_canned_fallback_t3.py       # fail-loud fallback
pytest tests/integration/agents/test_wizard_hitl_unified_contract.py       # contract sentinelas S1-S20
```

Eval gates online (rodam contra LLM live, threshold 0.85):

```bash
python -m eval.eval_runner --gate eval/golden/wizard_supervisor_routing.jsonl
python -m eval.eval_runner --gate eval/golden/wizard_conversational_hitl.jsonl
python -m eval.eval_runner --gate eval/golden/wizard_gate_competency.jsonl
python -m eval.eval_runner --gate eval/golden/wizard_gate_wsi_questions.jsonl
python -m eval.eval_runner --gate eval/golden/wizard_gate_review.jsonl
```

E2E Playwright (wave 16-20 — Task #1131):

```bash
bash plataforma-lia/scripts/run-pw-cenario.sh pw-cenario-1131-16 e2e/tests/wizard/16-vaga-nova-do-zero.spec.ts
bash plataforma-lia/scripts/run-pw-cenario.sh pw-cenario-1131-17 e2e/tests/wizard/17-retomada-draft.spec.ts
bash plataforma-lia/scripts/run-pw-cenario.sh pw-cenario-1131-18 e2e/tests/wizard/18-edicao-publicada.spec.ts
bash plataforma-lia/scripts/run-pw-cenario.sh pw-cenario-1131-19 e2e/tests/wizard/19-meta-question-global.spec.ts
bash plataforma-lia/scripts/run-pw-cenario.sh pw-cenario-1131-20 e2e/tests/wizard/20-exit-wizard-clean.spec.ts
```

## 7. Import do dashboard no Grafana

1. Grafana UI → Dashboards → New → Import.
2. Cole o conteúdo de `ops/grafana/lia-wizard-dashboard.json`.
3. Selecione o datasource Prometheus desejado (variable `DS_PROMETHEUS`).
4. Save → confirmar UID `lia-wizard-observability` para que os links do runbook funcionem.

Provisioning automatizado (recomendado): copiar o JSON para o diretório de dashboards do Grafana (`/etc/grafana/provisioning/dashboards/` por convenção) — datasource fica resolvido via `${DS_PROMETHEUS}` template variable.

## 8. Compliance e auditoria

Cada classification do gate gera 1 audit row (`agent_name=wizard_<stage>_classifier`, `decision_type=wizard_step_completed`, retenção SOX 7 anos). O **review gate publish_now** é dual: gera 2 audit rows correlatas via `trace_id` (`confirmation_method=chat` + `confirmation_method=dual`). Os painéis #7 e #8 medem a porta de saída do wizard — divergência > 10% entre `publish_now` registrado aqui e `audit_logs` no banco indica perda de auditoria (escalar imediatamente, viola Inegociável #6 do WeDO Talent Guide).

## 9. Histórico

- **2026-05-16 (Task #1131 / T4.2)** — runbook criado, dashboard JSON inicial (8 painéis). Alertas especificados mas ainda não wireados no AlertManager.
- (próximo) — wirar alertas, adicionar painel de "intents per recruiter" para detectar abuso, alinhar com painel de billing (`external_api_consumption`).
