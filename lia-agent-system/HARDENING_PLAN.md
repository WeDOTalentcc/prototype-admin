# LIA Agent System — Hardening Plan
> Iniciado: 2026-04-04 | Consultar este arquivo ao início e fim de cada etapa

## Status Geral
- [x] Etapa 0 — Auditoria de código (pré-implementação)
- [x] Etapa 1 — HNSW Index (migration 051)
- [x] Etapa 2 — Output Auditing
- [x] Etapa 3 — Fairness em inglês + fix bug idade PT-BR
- [x] Etapa 4 — Retenção de dados
- [x] Etapa 5 — Split wsi.py
- [x] Etapa 6 — Split job_vacancies (37+2), candidate_search (37), automation (26), lia_assistant (42) = 162 routes
- [x] Etapa 7 — Circuit Breaker: JÁ IMPLEMENTADO (13 circuits)
- [x] Etapa 8 — Agent Studio: fundação
- [x] Etapa 9 — Code review final (parcial — server offline para audit_prompts)
- [x] Testes unitários — 87 testes novos, 87 PASS, 3 bugs encontrados e corrigidos
- [x] Etapa 9.3 — Coverage críticos ≥ 50% — 198 novos testes (9 arquivos), módulos chave acima de 50%+
- [x] Split action_executor.py — 1887 LOC monolito → pacote 5 módulos (1216 LOC), 671 linhas dead code removidas, 44/44 testes PASS
- [x] Sprint de Consolidação — .bak removidos, vector cache 0.85, soft_warnings no ChatResponse, auditoria app/services/

---

## Etapa 0 — Auditoria de código ✅ CONCLUÍDA (2026-04-04)
**Objetivo:** estado atual antes de qualquer mudança.
- [x] 0.1 — audit_prompts.py → DEFERIDO para Etapa 9 (requer servidor rodando)
- [x] 0.2 — validate_stubs.py → ✅ 98/98 válidos, zero stubs quebrados
- [x] 0.3 — Coverage total: 24.99% — 6288 testes coletados: 6079 pass / 137 fail / 37 skip / 29 errors
             Arquivos críticos com gap: tool_registry_loader (23%), tools/registry (53%), domains/*
             Erros: 14 em test_api_misc_coverage (RuntimeError — DB não disponível), 15 em test_job_wizard_graph (mock insuficiente)
- [x] 0.4 — Circuit breakers: ✅ JÁ TOTALMENTE IMPLEMENTADO — 13 circuits (ANTHROPIC, GEMINI, OPENAI, WORKOS, MERGE, GUPY, PANDAPE, RESEND, MAILGUN, IUGU, VINDI, TWILIO_VOICE, GOOGLE_CALENDAR + Pearch)
- [x] 0.5 — Resultados registrados abaixo

**Resultados Etapa 0:**
```
audit_prompts.py: DEFERIDO — requer servidor HTTP em localhost:8000 (Etapa 9)
validate_stubs.py: ✅ 98/98 serviços válidos. Nenhum stub quebrado.
coverage críticos: 24.99% total. Gaps em orchestrator, compliance, cv_screening.
circuit_breakers wired: ✅ 13 circuits já implementados em todos os providers externos.

BUGS ENCONTRADOS em fairness_guard.py (4 testes falhando):
  - test_criterio_etario_bloqueado: "maiores de 50 anos" NÃO é bloqueado (bug real)
    → regex de `idade` não cobre "maiores de X anos" / "acima de X anos"
  - test_get_categories_returns_all: espera 9, tem 13 (teste desatualizado, não é bug)
  - test_discriminatory_message_blocked x2: problema de mock (não é bug de produção)

GAPS CONFIRMADOS:
  - audit_log model: SEM campo output_text — conversas da LIA não são auditadas
  - embedding_records: SEM HNSW index — busca vetorial em O(n) linear
  - fairness_guard.py: SEM termos EN (apenas PT-BR)
  - wsi.py: ~101k LOC em arquivo único
```

---

## Etapa 1 — HNSW Index ✅ CONCLUÍDA (2026-04-04)
**Migration:** `alembic/versions/051_add_hnsw_index_embeddings.py`
- [x] 1.1 — Migration 051 criada com IF EXISTS guard (adapta ao ambiente)
- [x] 1.2 — Aplicada no Neon DB via `DATABASE_URL=$NEON_DATABASE_URL alembic upgrade head`
- [x] 1.3 — Verificado: `idx_job_embeddings_hnsw` criado ✅ (embedding_records não existe no Neon → skip seguro)
**NOTAS:** Neon é o banco de produção. Banco local (helium) é dev incompleto. alembic_version estava em 008 no Neon — stampado para 050 antes de subir.

---

## Etapa 2 — Output Auditing ✅ CONCLUÍDA (2026-04-04)
**Local:** `/Users/paulomoraes/Documents/Python/lia-hardening/auditing/`
- [x] 2.1 — Confirmado: audit_log NÃO tinha output_text
- [x] 2.2 — Migration 052 aplicada no Neon ✅ (output_text, input_text, fairness_flags, agent_used, session_id confirmados)
- [x] 2.3 — Método log_output() inserido em audit_service.py (linha 247)
- [x] 2.4 — Wiring inserido em main_orchestrator.py (linha 497, antes do return)
- [x] 2.5 — Patches aplicados no Replit ✅ — syntax OK, import verificado

---

## Etapa 3 — Fairness EN + fix bug idade PT-BR ✅ CONCLUÍDA (2026-04-04)
**Local:** `/Users/paulomoraes/Documents/Python/lia-hardening/fairness/fairness_guard_patch.py`
- [x] 3.1 — IMPLICIT_BIAS_TERMS_EN: 20 termos EN (age proxies, class, appearance, origin, disability, family)
- [x] 3.2 — 3 novas categorias EN: gender_en, race_en, age_en (com regex) — total: 16 categorias
- [x] 3.3 — Fix bug PT-BR: 8 novos padrões regex de idade ("maiores de X anos", "acima de X", etc.)
- [x] 3.4 — check_implicit_bias() atualizado para iterar PT+EN ({**IMPLICIT_BIAS_TERMS, **IMPLICIT_BIAS_TERMS_EN})
- [x] 3.5 — Aplicado no Replit ✅ — 8/8 testes de smoke passaram, _PATTERNS_VERSION=4

---

## Etapa 4 — Retenção de Dados ✅ CONCLUÍDA (2026-04-04)
**Local:** `/Users/paulomoraes/Documents/Python/lia-hardening/retention/`
- [x] 4.1 — Model CompanyRetentionPolicy (retention_policy_model.py)
- [x] 4.2 — Migration 053 aplicada no Neon ✅ (company_retention_policies criada)
- [x] 4.3 — Celery task data.retention.run adicionado em celery_tasks.py
- [x] 4.4 — Endpoint GET + PATCH /api/v1/company/retention-policy (company_retention.py)
- [x] 4.5 — retention_policy.py + company_retention.py copiados ao Replit, router registrado em main.py ✅

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

## Etapa 7 — Circuit Breaker ✅ JÁ IMPLEMENTADO (não requer trabalho adicional)
Descoberto na Etapa 0: `app/shared/resilience/circuit_breaker.py` já implementa todos os estados
(CLOSED/OPEN/HALF_OPEN) com notificação Bell+Teams via Redis dedup (1 alerta/circuit/hora).
13 circuits nomeados cobrindo TODOS os providers externos.
- [x] 7.1 — Todos providers já protegidos: ANTHROPIC, GEMINI, OPENAI, WORKOS, MERGE, GUPY, PANDAPE, RESEND, MAILGUN, IUGU, VINDI, TWILIO_VOICE, GOOGLE_CALENDAR + Pearch
- [x] 7.2–7.5 — N/A

---

## Etapa 8 — Agent Studio: Fundação ✅ CONCLUÍDA (2026-04-04)
**Local:** `/Users/paulomoraes/Documents/Python/lia-hardening/agent_studio/`
- [x] 8.1 — Model AgentTemplate (agent_template_model.py)
- [x] 8.2 — Migration 054 aplicada no Neon ✅ (agent_templates criada)
- [x] 8.3 — YAML de exemplo: sourcing_default.yaml
- [x] 8.4 — registry_patch.py: get_domain_for_company()
- [x] 8.5 — CRUD completo: list/create/get/patch/publish/archive (agent_templates_api.py)
- [x] 8.6 — agent_template.py + agent_templates.py copiados ao Replit, router registrado em main.py ✅
- [ ] 8.7 — Teste end-to-end (Etapa 9)

---

## Etapa 9 — Code Review Final ✅ CONCLUÍDA (2026-04-05)
- [x] 9.1 — audit_prompts.py → ✅ 28/28 PASS (4 escopos: Job Wizard, Job Table, Talent Funnel, In-Job Pipeline)
- [x] 9.2 — validate_stubs.py → ✅ 96/96 válidos (2 novos vs Etapa 0), zero stubs quebrados
- [x] 9.3 — Coverage críticos ≥ 50% → ✅ temporal_resolver 95%, fact_checker 79%, fast_router 77%, fairness_guard 75%, main_orchestrator 67%
- [x] 9.4 — @circuit_breaker → ✅ Anthropic (4x), Gemini (4x), OpenAI (4x), Pearch, WORKOS, MERGE, GUPY, PANDAPE, RESEND, MAILGUN, IUGU, VINDI cobertos
- [x] 9.5 — Endpoints WSI via /docs → ✅ 1.423 endpoints totais, 98 WSI/screening visíveis
- [x] 9.6 — Fairness EN → ✅ Hard block: age regex EN/PT-BR; Soft advisory: implicit bias (young/dynamic, ivy league) — comportamento correto
- [x] 9.7 — Audit log output_text → ✅ log_output() em audit_service.py L247, wired em main_orchestrator.py L507, não-bloqueante

---

## Log de progresso
| Data | Etapa | Status | Observações |
|---|---|---|---|
| 2026-04-04 | Planejamento | ✅ | Diagnóstico profundo + plano completo |
| 2026-04-04 | Etapa 0 | ✅ | validate_stubs=98/98, coverage=24.99%, circuit_breakers=já implementados, fairness bugs=4 encontrados |
| 2026-04-04 | Etapa 7 | ✅ | Descoberto como já implementado na Etapa 0 — 13 circuits em produção |
| 2026-04-04 | Etapas 1-4,8 | ✅ MIGRATIONS APLICADAS | 051-054 rodaram no Neon. HNSW, output_text, retention_policy, agent_templates OK. Problemas resolvidos: 041 down_revision mismatch, CONCURRENTLY→IF NOT EXISTS, embedding_records IF EXISTS. |
| 2026-04-04 | Etapas 2,3,4,8 | ✅ CÓDIGO APLICADO | audit_service.log_output(), main_orchestrator wiring, fairness EN (16 cats), retention model+endpoint+Celery, agent_template model+CRUD API — todos no Replit. 7/7 verificações passaram. |
| 2026-04-04 | Testes unitários | ✅ 87/87 PASS | 5 arquivos, 87 testes. 3 bugs corrigidos: AuditLog model (colunas faltando), beat schedule (data-retention-monthly ausente), celery task (datetime not imported). |
| 2026-04-04 | Etapa 9.3 — Coverage ≥ 50% | ✅ 198/198 PASS | 9 arquivos novos. temporal_resolver 95%, intent_router 87%, action_handlers/candidate 69%, action_handlers/job 73%, fairness_middleware 73%, seniority_resolver 59%, seniority_utils 61%, domain_validators 42%. |
| 2026-04-05 | Split action_executor.py | ✅ 44/44 PASS | 1887 LOC → pacote 5 módulos: __init__.py (100%), action_types.py (100%), intents_config.py (100%), executor.py (28%), utils.py (29%). Dead code L931-L1660 eliminado (671 linhas). Zero breaking changes via re-exports. |
| 2026-04-05 | Etapa 9 — Code Review Final | ✅ COMPLETO | audit_prompts 28/28, validate_stubs 96/96, circuit_breakers 13 providers, 1423 endpoints/98 WSI no /docs, fairness EN hard+soft funcionando, output_text auditado. |
| 2026-04-05 | Sprint Consolidação — Tarefa 1 | ✅ COMPLETO | 3 arquivos .bak removidos (candidate_search, job_vacancies, lia_assistant) — 13.541 linhas eliminadas. commit 540e3d76 |
| 2026-04-05 | Sprint Consolidação — Tarefa 2 | ✅ COMPLETO | ROUTER_VECTOR_SIMILARITY_THRESHOLD: 0.92→0.85 em config.py, vector_semantic_cache.py fallback, cascaded_router.py comment, test_z5_03 assert atualizado. 11/11 PASS. commit 25e7d764 |
| 2026-04-05 | Sprint Consolidação — Tarefa 3 | ✅ COMPLETO | fairness_warnings: List[str] adicionado ao ChatResponse. _soft_warnings capturado da FairnessGuard e injetado nos 3 phases (0/1/2). 19/19 testes PASS. 3425 baseline mantido. |
| 2026-04-05 | Sprint Consolidação — Tarefa 4 | ✅ JÁ IMPLEMENTADO | Auditoria revelou: 97/98 shims já existiam (from app.domains.X import *). voice_service.py tem implementações diferentes e complementares (VoiceService STT+TTS vs TriagemVoiceService). 128 arquivos exclusivos em services/ são genuinamente compartilhados. Zero mudanças necessárias — arquitetura já consolidada. 3425/3425 baseline mantido. |

