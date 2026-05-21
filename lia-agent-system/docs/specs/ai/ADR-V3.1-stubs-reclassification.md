# ADR-V3.1: 30 Repository Stubs Reclassification (T-12 correção)

**Status:** Aprovado 2026-05-20
**Decisor:** Paulo Moraes (PLANO_ACAO_REPLIT_V3 T-12 + V3.1 correção pós-audit)
**Substitui:** V3 D2 "deletar 10 stubs" (inviável — endpoints v1 ativos)
**Relaciona:** DOMAIN_CATALOG.md, ADR-019-v2

## Contexto

V3 plan D2 (Paulo aprovou em 2026-05-20):
- MANTÉM (~10): auth, chat, notifications, consent, data_subject, audit, observability, admin, approvals, health_check
- DELETA (~10): triagem, workforce, opinions, trust_center, saas_metrics, technical_tests, goals, bulk_actions, job_vacancies_analytics, agent_memory
- CASO A CASO (~5): admin_settings, clients, client_users, email_templates, company_culture
- PROMOÇÕES (5): backlog F4+ (U2 overruled)

Audit Sprint 3 SSH read-only revelou **TODOS os 10 DELETE candidates têm endpoints v1 ATIVOS** em `app/api/routes.py`:

- triagem: 12 rotas, 531 LOC
- workforce: 22 rotas, 1052 LOC
- opinions: 7 rotas, 371 LOC (cross-call communication)
- trust_center: 13 rotas
- saas_metrics: 12 rotas, 968 LOC
- technical_tests: 11 rotas
- goals: 12 rotas, 656 LOC
- bulk_actions: 8 rotas, 1043 LOC
- job_vacancies_analytics: 9 rotas, 1480 LOC
- agent_memory: 4 rotas

**Total: ~110 rotas produção + 7000+ LOC.** Deletar = quebrar features ativas em uso.

## Decisão V3.1

Reclassificar D2:

### 1. STUB pattern É canonical (não anti-pattern)
- 30 stubs = thin-CRUD repositories com dependency injection (`dependencies.py`)
- Pattern intencional, não código morto
- Cada um serve API v1 ativa

### 2. DELETE → "DESCONTINUE-FEATURE-FIRST"
Para deletar qualquer stub, primeiro o **feature de produto** deve ser descontinuado (decisão de produto, não técnica). Wave plan se houver decisão futura:

| Wave | Stubs | Pré-requisito | Risk |
|---|---|---|---|
| 1 (LOW) | agent_memory (168 LOC, 4 routes) | Deprecate API 90d sunset | LOW |
| 2 (MED) | opinions, trust_center, bulk_actions | Descontinuar features | MEDIUM |
| 3 (HIGH) | triagem, workforce, saas_metrics, job_vacancies_analytics | Refactor para domains canonical (cv_screening, analytics, billing) | HIGH |
| 4 (LGPD) | technical_tests, goals | Migração de dados + erasure protocol | HIGH-LGPD |

### 3. PROMOTION candidates (5)
- `auth` (PII, 13 rotas)
- `chat` (7 rotas)
- `notifications` (18 rotas)
- `consent` (LGPD core)
- `data_subject` (LGPD core)

Estes são high-value e poderiam ganhar `domain.py` formal (agentic) no futuro.
Backlog F4+ por enquanto (U2 overruled imediato).

### 4. CASE-BY-CASE decisões (5)
- `admin_settings` → **MERGE em admin** (1 caller, mesma área, low risk)
- `clients` + `client_users` → **MANTER SEPARADO** (semântica distinta, cross-call HubSpot)
- `email_templates` → **MOVER para `communication` domain** (2 callers, alinhamento natural)
- `company_culture` → **MANTER STUB backlog** (1 caller, sem urgência)

## Sensor canonical (T-12)

`scripts/check_stub_invariants.py`:

| Regra | Descrição | Modo |
|---|---|---|
| R1 | Stub com `domain.py` deve estar em PROMOTION_CANDIDATES | WARN-ONLY |
| R2 | Stub novo apareceu sem registro em STUB_DOMAINS | WARN-ONLY |
| R3 | Deprecated não pode crescer | TODO (precisa baseline) |

## Consequências

**Positivas:**
- V3 plan D2 corrigido — não destrói produção
- 30 stubs documentados como pattern canonical (não anti-pattern)
- Sensor previne drift (novo stub sem registro, promoção sem catalog update)
- Roadmap descontinuação documentado se decisão produto vier

**Negativas:**
- Não há "limpeza" de Sprint 2 — stubs continuam
- Trade-off aceito: produção íntegra > cleanup cosmético

## Verification

```bash
python scripts/check_stub_invariants.py
# Esperado: "OK -- 30 stubs canonical + 5 promotion candidates documentados"
```

## Referências

- DOMAIN_CATALOG.md (canonical list)
- PLANO_ACAO_REPLIT_V3 T-12 (escopo corrigido)
- SPRINT_EXECUTION_PROTOCOL_2026-05-20.md Fase A pegou state real
