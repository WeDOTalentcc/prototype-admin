# Production Readiness — Gaps e Plano de Ação
**Versão:** 1.0 | **Data:** 2026-04-04 | **Task:** #126
**Referência:** PRODUCTION_READINESS_REPORT.md

---

## Gaps Identificados — Ordenados por Severidade

### G-01 — Health Check incompleto (sem Redis, LLM providers, Celery, circuit breakers)
**Critério:** #10 — Health check endpoint
**Severidade:** ALTO
**Status:** ✅ Resolvido neste sprint

**Descrição:**
O endpoint `/health` original cobria apenas DB, rate_limiter, task_manager e multi_channel.
Serviços críticos como Redis, circuit breakers, Celery e LLM providers não eram verificados.

**Resolução:**
- `app/api/v1/system_health.py` atualizado com:
  - Redis: verificação de conectividade com timeout de 1s
  - Circuit breakers: status de todos os 14 circuits (open/closed/half_open)
  - Celery workers: fila lengths via Redis broker
  - LLM providers: verificação de configuração (keys presentes)
  - DLQ: disponibilidade do serviço
  - Novos endpoints: `/health/ready` (readiness probe) e `/health/live` (liveness probe)

**Impacto:** Kubernetes probes agora funcionam corretamente para readiness/liveness.

---

### G-02 — Sem penetration test ou SAST scan documentado
**Critério:** #18 — Segurança e Autenticação
**Severidade:** ALTO
**Status:** ABERTO — Tarefa separada necessária

**Descrição:**
- Sem evidência de SAST (Static Application Security Testing) executado
- Sem penetration test documentado
- Sem SCA (Software Composition Analysis) para dependências vulneráveis
- Refresh token rotation não verificado

**Recomendações:**
1. Integrar Bandit (Python) ao CI/CD para SAST automático
2. Integrar Safety ou pip-audit para SCA de dependências
3. Executar OWASP ZAP scan contra ambiente de staging
4. Documentar procedimento de refresh token rotation
5. Auditar headers de segurança (HSTS, CSP, X-Frame-Options)

**Estimativa:** 2-3 dias de trabalho + configuração CI

---

### G-03 — Bias audit baseline sem agendamento periódico
**Critério:** #9 — Bias Audit Baseline
**Severidade:** MÉDIO
**Status:** ABERTO — Tarefa separada necessária

**Descrição:**
- Endpoint de bias audit baseline disponível (`POST /api/v1/bias-audit/job/{job_id}/run-baseline`)
- Golden dataset sintético implementado
- **Gap:** Execução apenas sob demanda — sem schedule automático
- **Gap:** Sem alerta quando AIR (Adverse Impact Ratio) cai abaixo de 0.80 (Four-Fifths Rule)
- **Gap:** Sem relatório mensal de fairness enviado para compliance team

**Recomendações:**
1. Criar task Celery `bias_audit.run_periodic_baseline` (weekly/monthly)
2. Adicionar alerta Bell + Teams quando AIR < 0.80 em qualquer dimensão
3. Gerar relatório PDF mensal de bias audit para compliance
4. Integrar ao `ComplianceHealthCheckItem` com status automático

**Estimativa:** 1-2 dias de trabalho

---

### G-04 — LLM fallback chain sem teste e2e em CI
**Critério:** #2 — LLM Fallback Chain testada e2e
**Severidade:** MÉDIO
**Status:** ✅ Parcialmente resolvido neste sprint

**Descrição:**
A implementação de fallback chain é sólida (`LLMProviderFactory.generate_with_fallback`),
mas não havia testes e2e automatizados.

**Resolução:**
- `tests/e2e/test_llm_fallback_chain_e2e.py` criado com 18 cenários de teste cobrindo:
  - Fallback primário → gemini
  - Fallback claude + gemini → openai
  - Todos falham → Exception clara
  - CircuitBreakerError bypasses
  - Ordem de fallback verificada
  - System prompt handling

**Gap restante:** Testes usam mocks — sem teste de integração real contra APIs externas.
Recomendação: criar smoke test semanal contra APIs reais em ambiente staging.

**Estimativa:** 0.5 dia para smoke test em staging

---

### G-05 — Circuit breaker cascata sem teste e2e
**Critério:** #12 — Governança IA (Dim 12)
**Severidade:** MÉDIO
**Status:** ✅ Resolvido neste sprint

**Descrição:**
CircuitBreaker implementado com estados corretos, mas sem testes e2e de cascata.

**Resolução:**
- `tests/e2e/test_circuit_breaker_cascade_e2e.py` criado com 35 cenários cobrindo:
  - Transição CLOSED → OPEN (com threshold de falhas)
  - Transição OPEN → HALF_OPEN (após recovery_timeout)
  - Transição HALF_OPEN → CLOSED (após success_threshold)
  - HALF_OPEN → OPEN (se falhar durante probe)
  - Reset manual
  - Cascata: service A falha → service B também abre
  - Stats completas (total_calls, failed, rejected, state_changes)
  - Timeout como falha

---

### G-06 — Load test não integrado ao CI/CD
**Critério:** #14 — Load Test
**Severidade:** MÉDIO
**Status:** ABERTO — Tarefa separada necessária

**Descrição:**
- `tests/load/locustfile.py` bem configurado com 6 cenários
- SLAs definidos (P95 < 5s para chat/screening, P95 < 2s para candidate_search)
- **Gap:** Sem integração ao pipeline CI/CD
- **Gap:** Sem resultado baseline documentado
- **Gap:** Sem alertas para regressão de performance

**Resolução parcial neste sprint:**
- Adicionado cenário `chat_screening` para triagem via LLM (novo)
- Adicionado cenário `sourcing_search` (novo)
- SLAs atualizados para cobrir novos endpoints

**Recomendações:**
1. Integrar locust ao GitHub Actions com perfil `smoke` (5 users, 60s) em cada PR
2. Executar perfil `load` semanalmente em staging
3. Armazenar histórico de P95 em banco de dados para tracking de regressão
4. Alertar no Slack/Teams se P95 regredir > 20% em relação à última semana

**Estimativa:** 1 dia para configuração CI

---

### G-07 — Golden datasets para LLM quality evaluation
**Critério:** Dim 10 — Qualidade LLM
**Severidade:** ALTO
**Status:** ABERTO — Coberto pela migração LangGraph (tarefa separada)

**Descrição:**
- Sem golden datasets para avaliação automática da qualidade LLM
- Sem LLM-as-judge implementado para ragas/deepeval
- Sem rastreamento de regressão de qualidade entre versões de modelo

**Recomendações:**
1. Criar `tests/ragas/golden_dataset_screening.py` com casos de triagem representativos
2. Implementar LLM-as-judge com critérios de scoring (acurácia, fairness, relevância)
3. Executar ragas eval em cada mudança de modelo ou prompt
4. Threshold mínimo: faithfulness > 0.85, answer_relevancy > 0.80

**Estimativa:** 3-5 dias de trabalho (coberto pela migração LangGraph)

---

### G-08 — Rollback de deploy sem procedimento interno
**Critério:** #13 — Rollback procedure
**Severidade:** BAIXO
**Status:** PARCIALMENTE documentado

**Descrição:**
- Rollback de dados (Neon PITR) está bem documentado em `RUNBOOK_BACKUP_RECOVERY.md`
- Rollback de schema (Alembic downgrade) está disponível
- **Gap:** Rollback de código (deploy) depende da plataforma CI/CD externa
- Sem procedimento documentado para "deploy anterior" em emergência

**Recomendações:**
1. Documentar procedimento de rollback de imagem Docker/container
2. Garantir que toda release tenha tag semântica para rollback fácil
3. Adicionar checklist de rollback ao `RUNBOOK_INCIDENT_PLAYBOOKS.md`

**Estimativa:** 0.5 dia para documentação

---

## Sumário de Ações por Prioridade

### Ações imediatas (este sprint — CONCLUÍDAS)
| Ação | Arquivo | Status |
|------|---------|--------|
| Health check consolidado | `app/api/v1/system_health.py` | ✅ |
| Testes e2e LLM fallback | `tests/e2e/test_llm_fallback_chain_e2e.py` | ✅ |
| Testes e2e circuit breaker cascata | `tests/e2e/test_circuit_breaker_cascade_e2e.py` | ✅ |
| Load test com screening | `tests/load/locustfile.py` | ✅ |
| Relatório de Production Readiness | `docs/PRODUCTION_READINESS_REPORT.md` | ✅ |

### Próximas sprints (tarefas separadas)
| Gap | Severidade | Esforço Estimado |
|-----|-----------|-----------------|
| SAST scan + pen test (G-02) | ALTO | 2-3 dias |
| Golden datasets LLM (G-07) | ALTO | 3-5 dias |
| Bias audit periódico (G-03) | MÉDIO | 1-2 dias |
| Load test no CI/CD (G-06) | MÉDIO | 1 dia |
| Smoke test LLM real (G-04 restante) | BAIXO | 0.5 dia |
| Rollback de deploy documentado (G-08) | BAIXO | 0.5 dia |
