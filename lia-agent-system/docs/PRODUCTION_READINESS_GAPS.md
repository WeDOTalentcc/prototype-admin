# Production Readiness — Gaps e Plano de Ação
**Versão:** 2.0 | **Data:** 2026-04-11 | **Task:** #164 (V2) | **Anterior:** #126 (V1, 2026-04-04)
**Referência:** PRODUCTION_READINESS_REPORT.md

---

## Status dos Gaps V1 → V2

| Gap V1 | Status V1 | Status V2 | Ação V2 |
|--------|-----------|-----------|---------|
| G-01 — Health check incompleto | ✅ Resolvido (sprint V1) | ✅ Mantido | — |
| G-02 — Sem pen test / SAST | ABERTO | Parcialmente coberto | 11 testes de prompt injection adicionados |
| G-03 — Bias audit sem schedule | ABERTO | ABERTO | Prioridade para próximo sprint |
| G-04 — LLM fallback sem smoke real | Parcial | Parcial | Sem mudança |
| G-05 — Circuit breaker cascata | ✅ Resolvido (sprint V1) | ✅ Mantido | — |
| G-06 — Load test não em CI/CD | ABERTO | ABERTO | Sem mudança |
| G-07 — Golden datasets LLM | ABERTO | ABERTO | Prioridade alta |
| G-08 — Rollback de deploy | Parcial | Parcial | Sem mudança |

---

## Gaps Ativos — Ordenados por Severidade

### G-02 — Sem penetration test ou SAST scan documentado
**Critério:** #18 — Segurança e Autenticação
**Severidade:** ALTO
**Status:** Parcialmente coberto (V2)

**Progresso V2:**
- 11 cenários de prompt injection security adicionados cobrindo:
  - Jailbreak (ignore instructions, DAN, role reversal)
  - SQL injection via prompt
  - Encoded injection (Base64)
  - System prompt extraction
  - Data exfiltration
  - Privilege escalation
  - Multi-language injection
  - Indirect injection (via candidate name)
  - Context window stuffing

**Gap restante:**
- Sem SAST (Bandit) integrado ao CI/CD
- Sem pen test externo profissional
- Sem SCA para dependências vulneráveis

**Recomendações:**
1. Integrar Bandit ao CI/CD para SAST automático
2. Integrar pip-audit para SCA de dependências
3. Executar OWASP ZAP scan contra staging
4. Documentar refresh token rotation

**Estimativa:** 2-3 dias

---

### G-07 — Golden datasets para LLM quality evaluation
**Critério:** Dim 10 — Qualidade LLM
**Severidade:** ALTO
**Status:** ABERTO

**Descrição:**
- Sem golden datasets para avaliação automática da qualidade LLM
- Sem LLM-as-judge implementado
- Sem rastreamento de regressão entre versões de modelo

**Progresso V2:**
- Classificação eval expandida com 3 novas categorias (CLARIFICAÇÃO ADEQUADA, RECUSA ÉTICA, AÇÃO PARCIAL)
- Detecção de alucinação reforçada (5 padrões vs 2 em V1)
- Métricas de latência por domínio adicionadas ao reporter
- Reporter V2 com comparativo automático V1 vs V2

**Recomendações:**
1. Criar `tests/ragas/golden_dataset_screening.py` com casos representativos
2. Implementar LLM-as-judge com scoring: acurácia, fairness, relevância
3. Threshold mínimo: faithfulness > 0.85, answer_relevancy > 0.80

**Estimativa:** 3-5 dias

---

### G-03 — Bias audit baseline sem agendamento periódico
**Critério:** #9 — Bias Audit Baseline
**Severidade:** MÉDIO
**Status:** ABERTO

**Descrição:**
- Endpoint disponível mas execução apenas sob demanda
- Sem schedule automático
- Sem alerta quando AIR < 0.80

**Progresso V2:**
- 14 cenários de governance-fairness.spec.ts testam as 13 categorias de discriminação via chat
- Cobertura complementar ao bias audit — valida que FairnessGuard bloqueia solicitações discriminatórias na camada de prompt

**Recomendações:**
1. Criar task Celery `bias_audit.run_periodic_baseline` (weekly)
2. Alerta Bell + Teams quando AIR < 0.80
3. Relatório mensal de bias audit para compliance

**Estimativa:** 1-2 dias

---

### G-04 — LLM fallback chain sem smoke test real
**Critério:** #2 — LLM Fallback Chain
**Severidade:** MÉDIO
**Status:** Parcialmente resolvido

**Gap:** Testes usam mocks. Sem smoke test semanal contra APIs reais em staging.

**Estimativa:** 0.5 dia

---

### G-06 — Load test não integrado ao CI/CD
**Critério:** #14 — Load Test
**Severidade:** MÉDIO
**Status:** ABERTO

**Gap:** Sem integração CI/CD, sem baseline documentado, sem alertas de regressão.

**Estimativa:** 1 dia

---

### G-08 — Rollback de deploy sem procedimento interno
**Critério:** #13 — Rollback procedure
**Severidade:** BAIXO
**Status:** Parcialmente documentado

**Gap:** Rollback de código depende da plataforma CI/CD externa.

**Estimativa:** 0.5 dia

---

## Novos Gaps Identificados em V2

### G-09 — Baseline de resultados V2 não registrado
**Critério:** Geral
**Severidade:** BAIXO
**Status:** Suíte pronta — aguarda execução contra ambiente staging/dev

**Descrição:**
162 cenários de capability eval criados com assertions rigorosas. Primeira execução gerará `eval-summary.json` com baseline V2 comparável ao V1 via reporter automático.

**Ação:** Executar via `npx playwright test --config=e2e/tests/lia-capability-eval/eval.config.ts` contra ambiente staging/dev. Registrar `eval-summary.json` como `eval-summary-v2-baseline.json`.

**Nota:** Execução requer aplicação rodando (frontend + backend + LLM providers). Não é possível executar em ambiente isolado de desenvolvimento sem o stack completo.

---

### G-10 — Validação de retenção de contexto multi-turn
**Critério:** Dim 9 — Arquitetura de Agentes
**Severidade:** MÉDIO
**Status:** 8 cenários criados com assertions de context retention

**Descrição:**
Multi-turn context retention é crítico para UX de recrutamento. 8 cenários cobrem:
- Conversas de 3-5 turnos com referência a contexto anterior
- Resolução de pronomes ("ela", "essa vaga", "dele")
- Correção mid-conversation
- Context switch entre domínios

Todos os cenários incluem `expect(result.contextRetained).toBe(true)` como assertion obrigatória.

**Ação:** Executar e analisar `eval_context_retained` annotations para baseline de retenção. Avaliar se threshold de keyword matching em `sendMultiTurnConversation` é suficiente ou precisa de ajuste fino.

---

## Sumário de Ações por Prioridade

### Concluídas neste sprint (V2)
| Ação | Arquivos | Status |
|------|----------|--------|
| Expandir 7 domínios de 5→10 cenários | 7 spec files atualizados | ✅ |
| Criar 6 novos domínios | hiring-policy, cv-screening-wsi, talent-pool, digital-twin, ats-integration, recruitment-campaign | ✅ |
| Criar 4 dimensões transversais | multi-turn-context, governance-fairness, prompt-injection-security, anti-sycophancy | ✅ |
| Expandir eval-helpers.ts | 3 novas classificações, multi-turn, latency metrics, assertors | ✅ |
| Atualizar eval-reporter.ts | V1 vs V2 comparativo, executive summary, domain latency | ✅ |
| Atualizar PRODUCTION_READINESS_REPORT.md | V2.0 com novos scores e comparativo | ✅ |
| Atualizar PRODUCTION_READINESS_GAPS.md | Status V1→V2, novos gaps G-09/G-10 | ✅ |

### Próximas sprints (tarefas separadas)
| Gap | Severidade | Esforço Estimado |
|-----|-----------|-----------------|
| SAST scan + pen test externo (G-02) | ALTO | 2-3 dias |
| Golden datasets LLM (G-07) | ALTO | 3-5 dias |
| Bias audit periódico (G-03) | MÉDIO | 1-2 dias |
| Multi-turn context baseline (G-10) | MÉDIO | 0.5 dia |
| Load test no CI/CD (G-06) | MÉDIO | 1 dia |
| Smoke test LLM real (G-04) | BAIXO | 0.5 dia |
| Rollback de deploy (G-08) | BAIXO | 0.5 dia |
