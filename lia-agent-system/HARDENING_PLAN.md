# LIA Agent System — Hardening Plan
> Iniciado: 2026-04-04 | Consultar este arquivo ao início e fim de cada etapa

## Status Geral
- [ ] Etapa 0 — Auditoria de código (pré-implementação)
- [ ] Etapa 1 — HNSW Index (migration 051)
- [ ] Etapa 2 — Output Auditing
- [ ] Etapa 3 — Fairness em inglês
- [ ] Etapa 4 — Retenção de dados
- [ ] Etapa 5 — Split wsi.py
- [ ] Etapa 6 — Split job_vacancies, candidate_search, automation, lia_assistant
- [ ] Etapa 7 — Circuit Breaker: verificar e conectar
- [ ] Etapa 8 — Agent Studio: fundação
- [ ] Etapa 9 — Code review final

---

## Etapa 0 — Auditoria de código ⬜
**Objetivo:** estado atual antes de qualquer mudança.
- [ ] 0.1 — Rodar `python scripts/audit_prompts.py` → anotar resultados PASS/FAIL
- [ ] 0.2 — Rodar `python scripts/validate_stubs.py` → anotar stubs sem implementação
- [ ] 0.3 — Coverage: `pytest --cov=app/domains/cv_screening --cov=app/orchestrator --cov=app/shared/compliance --cov-report=term-missing -q`
- [ ] 0.4 — Verificar circuit breakers wired: `grep -rn "@circuit_breaker\|CircuitBreaker(" app/ --include="*.py" | grep -v test`
- [ ] 0.5 — Registrar achados no campo "Resultados" abaixo

**Resultados Etapa 0:**
```
audit_prompts.py: [PREENCHER]
validate_stubs.py: [PREENCHER]
coverage críticos: [PREENCHER]
circuit_breakers wired: [PREENCHER]
```

---

## Etapa 1 — HNSW Index ⬜
**Migration:** `alembic/versions/051_add_hnsw_index_embeddings.py`
- [ ] 1.1 — Criar migration 051
- [ ] 1.2 — Rodar: `alembic upgrade head`
- [ ] 1.3 — Verificar com EXPLAIN ANALYZE

---

## Etapa 2 — Output Auditing ⬜
**Arquivos:** `app/orchestrator/main_orchestrator.py`, `app/shared/compliance/audit_service.py`
- [ ] 2.1 — Verificar se `output_text` existe em audit_logs
- [ ] 2.2 — Criar migration 052 se necessário
- [ ] 2.3 — Adicionar `log_output()` em audit_service.py
- [ ] 2.4 — Wiring em main_orchestrator.py
- [ ] 2.5 — Teste: ação no chat → checar audit_logs

---

## Etapa 3 — Fairness em inglês ⬜
**Arquivo:** `app/shared/compliance/fairness_guard.py`
- [ ] 3.1 — Adicionar IMPLICIT_BIAS_TERMS_EN (12+ termos)
- [ ] 3.2 — Adicionar DISCRIMINATORY_CATEGORIES EN (gender_en, race_en, age_en)
- [ ] 3.3 — Atualizar loop principal PT + EN
- [ ] 3.4 — Teste: FairnessGuard().check("only young candidates ivy league") → is_blocked=True

---

## Etapa 4 — Retenção de Dados ⬜
- [ ] 4.1 — Criar model CompanyRetentionPolicy
- [ ] 4.2 — Criar migration 053
- [ ] 4.3 — Criar Celery task data.retention.run (auto_anonymize=False por default)
- [ ] 4.4 — Criar endpoint PATCH /api/v1/company/retention-policy
- [ ] 4.5 — Teste: ativar → rodar task → verificar anonimização

---

## Etapa 5 — Split wsi.py ⬜
**De:** app/api/v1/wsi.py (101k LOC) → **Para:** app/api/v1/wsi/ (6 módulos)
- [ ] 5.1 — Criar diretório app/api/v1/wsi/
- [ ] 5.2 — questions.py (L246–L967)
- [ ] 5.3 — evaluation.py (L484–L1383)
- [ ] 5.4 — sessions.py (L1383–L1959)
- [ ] 5.5 — reports.py (L1959–L2398)
- [ ] 5.6 — voice.py (endpoints Twilio WSI)
- [ ] 5.7 — admin.py (config, reset)
- [ ] 5.8 — __init__.py agregador
- [ ] 5.9 — Atualizar main.py
- [ ] 5.10 — py_compile sem erros
- [ ] 5.11 — GET /docs mostra todos os endpoints

---

## Etapa 6 — Split outros arquivos grandes ⬜

### 6a — job_vacancies.py → app/api/v1/job_vacancies/
- [ ] crud.py | lifecycle.py | analytics.py | export.py | public.py | screening.py | __init__.py

### 6b — candidate_search.py → app/api/v1/candidate_search/
- [ ] core_search.py | contact.py | jd_search.py | archetypes.py | calibration.py | __init__.py

### 6c — automation.py → app/api/v1/automation/
- [ ] triggers.py | suggestions.py | event_handlers.py | __init__.py

### 6d — lia_assistant.py → app/api/v1/lia_assistant/
- [ ] suggestions.py | wizard.py | insights.py | conversational.py | __init__.py

---

## Etapa 7 — Circuit Breaker ⬜
- [ ] 7.1 — Mapear providers já protegidos
- [ ] 7.2 — Conectar llm_cascade.py (Anthropic, Gemini)
- [ ] 7.3 — Conectar pearch_service.py
- [ ] 7.4 — Conectar Merge.dev
- [ ] 7.5 — Teste: simular falha → resposta degradada

---

## Etapa 8 — Agent Studio: Fundação ⬜
- [ ] 8.1 — Model AgentTemplate
- [ ] 8.2 — Migration 054
- [ ] 8.3 — System prompts Python → YAML (paralelo)
- [ ] 8.4 — registry.py: suporte a tenant-scoped templates
- [ ] 8.5 — CRUD /api/v1/agent-templates
- [ ] 8.6 — Registrar em main.py
- [ ] 8.7 — Teste end-to-end

---

## Etapa 9 — Code Review Final ⬜
- [ ] 9.1 — audit_prompts.py → todos PASS
- [ ] 9.2 — validate_stubs.py → zero stubs críticos
- [ ] 9.3 — Coverage críticos ≥ 50%
- [ ] 9.4 — @circuit_breaker: Anthropic, Gemini, Pearch cobertos
- [ ] 9.5 — Todos endpoints WSI acessíveis via /docs
- [ ] 9.6 — Fairness EN confirmado
- [ ] 9.7 — Audit log output_text preenchido

---

## Log de progresso
| Data | Etapa | Status | Observações |
|---|---|---|---|
| 2026-04-04 | Planejamento | ✅ | Diagnóstico profundo + plano completo |

